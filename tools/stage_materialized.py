#!/usr/bin/env python3
"""NUL-safe force staging and exact index closure verification."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import unicodedata
from typing import Dict, Tuple


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools import assimilation  # noqa: E402


ROOT = assimilation.ROOT
EXCLUDED_TARGET_PARTS = {".git", ".rapp-god-input", "__pycache__", ".pytest_cache"}


def logical_path(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def target_mode(path: Path) -> str:
    info = os.lstat(str(path))
    if stat.S_ISLNK(info.st_mode):
        return "120000"
    return "100755" if info.st_mode & stat.S_IXUSR else "100644"


def imported_expectations():
    rows = [
        json.loads(line)
        for line in (ROOT / "provenance/files.jsonl").read_text().splitlines()
        if line
    ]
    expected = {}
    for row in rows:
        if not row.get("destination"):
            continue
        path = logical_path(str(row["destination"]))
        expected[path] = {
            "mode": str(row["source_mode"]),
            "blob": str(row["source_blob"]),
            "access_path": ROOT / str(row["destination"]),
            "origin": "imported-ledger",
        }
    return expected


def imported_roots():
    lock = json.loads((ROOT / "provenance/sources.lock.json").read_text())
    roots = [
        Path(str(source["destination"]))
        for source in lock["sources"]
        if source["disposition"] != "native-evolved"
    ]
    roots.append(Path(assimilation.GRAIL_DESTINATION))
    return sorted(roots, key=lambda path: len(path.parts), reverse=True)


def below_import_root(relative: Path, roots) -> bool:
    for root in roots:
        try:
            relative.relative_to(root)
            return True
        except ValueError:
            pass
    return False


def expected_index():
    expected = imported_expectations()
    roots = imported_roots()
    for directory, directory_names, file_names in os.walk(str(ROOT), followlinks=False):
        relative_directory = Path(directory).relative_to(ROOT)
        directory_names[:] = [
            name
            for name in directory_names
            if name not in EXCLUDED_TARGET_PARTS
            and not below_import_root(relative_directory / name, roots)
            and not os.path.islink(os.path.join(directory, name))
        ]
        candidates = list(file_names)
        candidates.extend(
            name
            for name in os.listdir(directory)
            if os.path.islink(os.path.join(directory, name))
        )
        for name in candidates:
            path = Path(directory) / name
            relative = path.relative_to(ROOT)
            if any(part in EXCLUDED_TARGET_PARTS for part in relative.parts):
                continue
            if below_import_root(relative, roots):
                continue
            logical = logical_path(str(relative))
            mode = target_mode(path)
            data = assimilation.file_bytes(path, mode)
            expected[logical] = {
                "mode": mode,
                "blob": assimilation.git_blob_id(data),
                "access_path": path,
                "origin": "target-owned",
            }
    return expected


def index_entries() -> Dict[str, Tuple[str, str]]:
    raw = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-s", "-z"],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    entries = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, path = record.split(b"\t", 1)
        mode, object_id, stage = metadata.decode("ascii").split()
        if stage != "0":
            raise RuntimeError("non-zero index stage for " + os.fsdecode(path))
        entries[logical_path(os.fsdecode(path))] = (mode, object_id)
    return entries


def check_index(expected) -> None:
    actual = index_entries()
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    mismatched = sorted(
        path
        for path in set(expected) & set(actual)
        if actual[path] != (expected[path]["mode"], expected[path]["blob"])
    )
    if missing or extra or mismatched:
        raise RuntimeError(
            "index closure differs: missing={} extra={} mismatched={}".format(
                len(missing), len(extra), len(mismatched)
            )
        )
    print("Index closure verified for {} materialized paths.".format(len(expected)))


def stage(expected) -> None:
    extras = sorted(set(index_entries()) - set(expected))
    if extras:
        subprocess.run(
            [
                "git",
                "-C",
                str(ROOT),
                "update-index",
                "--force-remove",
                "-z",
                "--stdin",
            ],
            input=b"".join(os.fsencode(path) + b"\0" for path in extras),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
    payload = b"".join(
        os.fsencode(path) + b"\0" for path in sorted(expected)
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "add",
            "-f",
            "--pathspec-from-file=-",
            "--pathspec-file-nul",
        ],
        input=payload,
        check=True,
    )
    check_index(expected)


def ignored_paths(expected):
    payload = b"".join(os.fsencode(path) + b"\0" for path in sorted(expected))
    result = subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "check-ignore",
            "--no-index",
            "-z",
            "--stdin",
        ],
        input=payload,
        stdout=subprocess.PIPE,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError("git check-ignore failed")
    return {
        logical_path(os.fsdecode(path))
        for path in result.stdout.split(b"\0")
        if path
    }


def plan_bytes(expected):
    ignored = ignored_paths(expected)
    rows = [
        {
            "path": path,
            "mode": expected[path]["mode"],
            "blob": expected[path]["blob"],
            "bytes": len(
                assimilation.file_bytes(
                    expected[path]["access_path"], expected[path]["mode"]
                )
            ),
            "disposition": "force-stage-required",
        }
        for path in sorted(ignored)
    ]
    ignored_data = assimilation.jsonl_bytes(rows)
    plan = {
        "schema": "rapp-god-staging-plan/1",
        "materialized_paths": len(expected),
        "ignored_materialized_paths": len(rows),
        "ignored_logical_bytes": sum(row["bytes"] for row in rows),
        "ignored_index": "provenance/ignored-materialized.jsonl",
        "ignored_index_sha256": hashlib.sha256(ignored_data).hexdigest(),
        "path_encoding": "NUL-delimited-NFC",
        "force_stage": True,
        "commit": False,
        "tool": "tools/stage_materialized.py --stage",
    }
    privacy_path = ROOT / "provenance/privacy-status.json"
    if privacy_path.exists():
        privacy = json.loads(privacy_path.read_text())
        if privacy.get("pending_import_quarantine", {}).get("status") in {
            "applied",
            "applied-v2",
        }:
            plan["pre_quarantine_ignored_materialized_paths"] = 985
            plan["pre_quarantine_ignored_logical_bytes"] = 345500245
            plan["withheld_ignored_materialized_paths"] = 985 - len(rows)
            plan["withheld_ignored_logical_bytes"] = 345500245 - sum(
                row["bytes"] for row in rows
            )
    return ignored_data, assimilation.json_bytes(plan)


def write_plan(check=False):
    expected = expected_index()
    ignored_data, plan = plan_bytes(expected)
    generated = {
        "provenance/ignored-materialized.jsonl": ignored_data,
        "provenance/staging-plan.json": plan,
    }
    if check:
        mismatches = [
            path
            for path, data in generated.items()
            if not (ROOT / path).exists() or (ROOT / path).read_bytes() != data
        ]
        if mismatches:
            raise RuntimeError("staging plan differs: " + ", ".join(mismatches))
    else:
        for path, data in generated.items():
            assimilation.write_generated(path, data)
        # The two generated paths become expected target-owned paths on first creation.
        expected = expected_index()
        ignored_data, plan = plan_bytes(expected)
        assimilation.write_generated("provenance/ignored-materialized.jsonl", ignored_data)
        assimilation.write_generated("provenance/staging-plan.json", plan)
    print("Staging plan accounts for {} ignored materialized paths.".format(
        json.loads(plan)["ignored_materialized_paths"]
    ))


def main() -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--stage", action="store_true")
    action.add_argument("--check", action="store_true")
    action.add_argument("--print0", action="store_true")
    action.add_argument("--plan", action="store_true")
    action.add_argument("--check-plan", action="store_true")
    args = parser.parse_args()
    expected = expected_index()
    if args.plan:
        write_plan()
    elif args.check_plan:
        write_plan(check=True)
    elif args.print0:
        sys.stdout.buffer.write(
            b"".join(os.fsencode(path) + b"\0" for path in sorted(expected))
        )
    elif args.stage:
        stage(expected)
    else:
        check_index(expected)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
