#!/usr/bin/env python3
"""Scan the staged tree without printing secret values."""

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Dict, Iterable, List, Sequence, Tuple


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools import assimilation  # noqa: E402


ROOT = assimilation.ROOT
DEFAULT_ALLOWLIST = ROOT / "security/secret-allowlist.json"
DEFAULT_REPORT = ROOT / "provenance/staged-secret-scan.json"
BYTE_PATTERNS = {
    name: re.compile(pattern.encode("ascii"))
    for name, pattern in assimilation.SECRET_PATTERNS.items()
}
TEXT_PATTERNS = {
    name: re.compile(pattern) for name, pattern in assimilation.SECRET_PATTERNS.items()
}


def index_blobs() -> Tuple[Dict[str, List[str]], int]:
    raw = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-s", "-z"],
        check=True,
        capture_output=True,
    ).stdout
    paths = defaultdict(list)
    records = 0
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, path = record.split(b"\t", 1)
        _mode, object_id, stage = metadata.decode("ascii").split()
        if stage != "0":
            raise RuntimeError("non-zero index stage")
        decoded = path.decode("utf-8", "surrogateescape")
        if decoded == "provenance/staged-secret-scan.json":
            continue
        paths[object_id].append(decoded)
        records += 1
    return {key: value for key, value in paths.items() if value}, records


def fingerprint(pattern: str, matched: bytes, context: bytes) -> Dict[str, str]:
    return {
        "pattern": pattern,
        "fingerprint": hashlib.sha256(
            pattern.encode("ascii") + b"\0" + matched
        ).hexdigest(),
        "context_sha256": hashlib.sha256(context).hexdigest(),
    }


def scan_bytes(data: bytes) -> List[Dict[str, str]]:
    findings = []
    for name, pattern in BYTE_PATTERNS.items():
        for match in pattern.finditer(data):
            start = max(0, match.start() - 64)
            end = min(len(data), match.end() + 64)
            findings.append(fingerprint(name, match.group(0), data[start:end]))
    null_ratio = data[:8192].count(b"\0") / max(1, len(data[:8192]))
    if data.startswith((b"\xff\xfe", b"\xfe\xff")) or null_ratio > 0.2:
        encodings = ["utf-16"]
        for encoding in encodings:
            try:
                text = data.decode(encoding)
            except UnicodeDecodeError:
                continue
            for name, pattern in TEXT_PATTERNS.items():
                for match in pattern.finditer(text):
                    start = max(0, match.start() - 64)
                    end = min(len(text), match.end() + 64)
                    findings.append(
                        fingerprint(
                            name,
                            match.group(0).encode("utf-8"),
                            text[start:end].encode("utf-8"),
                        )
                    )
    unique = {
        (row["pattern"], row["fingerprint"], row["context_sha256"]): row
        for row in findings
    }
    return [unique[key] for key in sorted(unique)]


def read_git_blobs(object_paths: Dict[str, List[str]]):
    process = subprocess.Popen(
        ["git", "-C", str(ROOT), "cat-file", "--batch"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdin is not None and process.stdout is not None
    try:
        for object_id in sorted(object_paths):
            process.stdin.write(object_id.encode("ascii") + b"\n")
            process.stdin.flush()
            header = process.stdout.readline().decode("ascii").strip().split()
            if len(header) != 3 or header[1] != "blob":
                raise RuntimeError("cannot read staged blob " + object_id)
            size = int(header[2])
            data = process.stdout.read(size)
            if process.stdout.read(1) != b"\n":
                raise RuntimeError("invalid cat-file framing")
            yield object_id, data
    finally:
        process.stdin.close()
        return_code = process.wait()
        if return_code:
            raise RuntimeError("git cat-file failed")


def load_allowlist(path: Path):
    if not path.exists():
        return {}
    document = json.loads(path.read_text(encoding="utf-8"))
    return {
        (row["pattern"], row["fingerprint"], row["context_sha256"]): row
        for row in document.get("entries", [])
    }


def generate(allowlist_path: Path):
    object_paths, path_count = index_blobs()
    allowlist = load_allowlist(allowlist_path)
    findings = []
    for object_id, data in read_git_blobs(object_paths):
        for finding in scan_bytes(data):
            key = (
                finding["pattern"],
                finding["fingerprint"],
                finding["context_sha256"],
            )
            allowed = allowlist.get(key)
            findings.append(
                {
                    **finding,
                    "object": object_id,
                    "paths": sorted(object_paths[object_id]),
                    "allowlisted": allowed is not None,
                    "classification": (
                        allowed["classification"] if allowed else "unreviewed"
                    ),
                }
            )
    archive_proof = json.loads(
        (ROOT / "provenance/archive-audit-proof.json").read_text()
    )
    archive_members = (ROOT / "provenance/archive-members.jsonl").read_bytes()
    report = {
        "schema": "rapp-god-staged-secret-scan/1",
        "paths_scanned": path_count,
        "unique_blobs_scanned": len(object_paths),
        "self_excluded_path": "provenance/staged-secret-scan.json",
        "binary_scan": True,
        "utf16_scan": True,
        "archive_scan": {
            "recursive": True,
            "containers": archive_proof["retained"]["containers"],
            "members": archive_proof["retained"]["members"],
            "member_index_sha256": hashlib.sha256(archive_members).hexdigest(),
            "secret_hits": archive_proof["retained"]["secret_hits"],
            "complete": (
                archive_proof["retained"]["incomplete_scans"] == 0
                and archive_proof["pre_quarantine_scan"]["errors"] == 0
            ),
        },
        "finding_count": len(findings),
        "allowlisted_findings": sum(row["allowlisted"] for row in findings),
        "unallowlisted_findings": sum(not row["allowlisted"] for row in findings),
        "findings": sorted(
            findings,
            key=lambda row: (
                str(row["pattern"]),
                str(row["fingerprint"]),
                str(row["object"]),
            ),
        ),
        "values_recorded": False,
    }
    return assimilation.json_bytes(report), report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allowlist", type=Path, default=DEFAULT_ALLOWLIST)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--candidate", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data, report = generate(args.allowlist.resolve())
    if args.check:
        if not args.report.exists() or args.report.read_bytes() != data:
            raise SystemExit("staged secret report differs")
    else:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_bytes(data)
    if report["archive_scan"]["secret_hits"] or not report["archive_scan"]["complete"]:
        raise SystemExit("recursive archive secret scan is not clean")
    if report["unallowlisted_findings"] and not args.candidate:
        raise SystemExit(
            "{} unallowlisted staged secret fingerprints".format(
                report["unallowlisted_findings"]
            )
        )
    print(
        "Scanned {} staged paths; {} exact allowlisted findings, {} unallowlisted.".format(
            report["paths_scanned"],
            report["allowlisted_findings"],
            report["unallowlisted_findings"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
