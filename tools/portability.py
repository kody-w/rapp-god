#!/usr/bin/env python3
"""Generate public Windows path portability findings without renaming imports."""

import argparse
import json
from pathlib import Path
import re
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools import assimilation  # noqa: E402


ROOT = assimilation.ROOT
RESERVED = re.compile(r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?$", re.I)


def outputs():
    mappings = [
        json.loads(line)
        for line in (ROOT / "provenance/files.jsonl").read_text().splitlines()
        if line
    ]
    findings = []
    long_paths = []
    for row in mappings:
        if (
            row.get("authority_alias")
            or not row.get("destination")
            or not row.get("source_repository")
            or not row.get("source_path")
        ):
            continue
        destination = str(row["destination"])
        reasons = set()
        for segment in destination.split("/"):
            if re.search(r'[<>:"\\|?*]', segment):
                reasons.add("windows-forbidden-character")
            if RESERVED.match(segment):
                reasons.add("windows-reserved-name")
            if segment.endswith((" ", ".")):
                reasons.add("windows-trailing-space-or-dot")
            if any(ord(character) < 32 for character in segment):
                reasons.add("control-character")
        if reasons:
            findings.append(
                {
                    "repository": row["source_repository"],
                    "source_path": row["source_path"],
                    "destination": destination,
                    "issues": sorted(reasons),
                    "disposition": "exact-import-portability-limitation",
                }
            )
        path_bytes = len(destination.encode("utf-8"))
        if path_bytes >= 260:
            long_paths.append(
                {
                    "repository": row["source_repository"],
                    "source_path": row["source_path"],
                    "destination": destination,
                    "utf8_path_bytes": path_bytes,
                    "threshold": 260,
                    "disposition": "exact-import-long-path",
                }
            )
    findings.sort(key=lambda row: (str(row["repository"]), str(row["source_path"])))
    long_paths.sort(key=lambda row: (str(row["repository"]), str(row["source_path"])))
    quarantine_applied = False
    privacy_path = ROOT / "provenance/privacy-status.json"
    if privacy_path.exists():
        privacy = json.loads(privacy_path.read_text())
        quarantine_applied = (
            privacy.get("pending_import_quarantine", {}).get("status")
            in {"applied", "applied-v2"}
        )
    baseline_invalid = 28 if quarantine_applied else len(findings)
    baseline_long = 5 if quarantine_applied else len(long_paths)
    report = {
        "schema": "rapp-god-portability/1",
        "platform": "Windows checkout",
        "policy": "Exact imported paths are not renamed.",
        "invalid_path_records": baseline_invalid,
        "long_path_records": baseline_long,
        "retained_invalid_path_records": len(findings),
        "retained_long_path_records": len(long_paths),
        "withheld_invalid_path_records": baseline_invalid - len(findings),
        "withheld_long_path_records": baseline_long - len(long_paths),
        "invalid_paths": findings,
        "long_paths": long_paths,
        "instructions": "docs/WINDOWS_SPARSE_CHECKOUT.md",
    }
    return {"catalog/portability.json": assimilation.json_bytes(report)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generated = outputs()
    if args.check:
        for path, data in generated.items():
            if not (ROOT / path).exists() or (ROOT / path).read_bytes() != data:
                raise SystemExit(path + " differs")
        print("Portability report is deterministic.")
    else:
        for path, data in generated.items():
            assimilation.write_generated(path, data)
        print("Generated portability report.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
