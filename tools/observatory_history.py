#!/usr/bin/env python3
"""Reconcile registry frames, physical files, orphans, and explicit tombstones."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools import assimilation  # noqa: E402


ROOT = assimilation.ROOT
BASELINE_COMMIT = "66f47a72767cc59d310ddc07d745cce4d612fae8"


def registry_paths(value):
    return {
        str(version["path"])
        for part in value.get("parts", [])
        for version in part.get("versions", [])
    }


def outputs():
    baseline_raw = subprocess.run(
        ["git", "-C", str(ROOT), "show", BASELINE_COMMIT + ":registry.json"],
        check=True,
        capture_output=True,
    ).stdout
    prior = registry_paths(json.loads(baseline_raw))
    current_registry = json.loads((ROOT / "registry.json").read_text())
    current_parts = registry_paths(current_registry)
    physical_index = {
        str(row["path"]): row for row in current_registry.get("physical_frames", [])
    }
    current = current_parts | set(physical_index)
    physical = {
        str(path.relative_to(ROOT)): path
        for path in (ROOT / "versions").rglob("*")
        if path.is_file()
    }
    tombstones_document = json.loads(
        (ROOT / "provenance/version-tombstones.json").read_text()
    )
    tombstones = {
        str(row["path"]): row for row in tombstones_document["tombstones"]
    }
    union = sorted(prior | current | set(physical) | set(tombstones))
    rows = []
    missing = []
    for relative in union:
        path = physical.get(relative)
        tombstone = tombstones.get(relative)
        if path:
            data = path.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            size = len(data)
        else:
            digest = tombstone["sha256"] if tombstone else None
            size = tombstone["bytes"] if tombstone else None
        if path and relative in current:
            state = "current-indexed-physical"
        elif tombstone:
            state = "explicit-tombstone-no-payload"
        else:
            state = "unexplained-missing-payload"
            missing.append(relative)
        rows.append(
            {
                "path": relative,
                "sha256": digest,
                "bytes": size,
                "physical": path is not None,
                "prior_registry": relative in prior,
                "current_registry_part": relative in current_parts,
                "current_physical_index": relative in physical_index,
                "tombstone": tombstone is not None,
                "state": state,
            }
        )
    if missing:
        raise RuntimeError("registry payloads are unexplained: " + ", ".join(missing))
    if set(physical) - current:
        raise RuntimeError("physical frame is absent from the current registry indexes")
    if prior - (current | set(tombstones)):
        raise RuntimeError("prior registry frame is neither indexed nor tombstoned")
    kite = physical_index.get("versions/kite-mark.svg/c4c2ffae5467.svg")
    if (
        not kite
        or kite["part"] != "kite-mark.svg"
        or kite["disposition"] != "part-version-frame"
    ):
        raise RuntimeError("kite-mark physical frame is not indexed as a part version")
    summary = {
        "schema": "rapp-god-observatory-history/1",
        "baseline_registry_commit": BASELINE_COMMIT,
        "prior_registry_versions": len(prior),
        "current_part_versions": len(current_parts),
        "current_indexed_frames": len(current),
        "physical_frames": len(physical),
        "physical_orphans": len(set(physical) - current),
        "standalone_physical_frames": sum(
            row.get("part") is None for row in physical_index.values()
        ),
        "explicit_tombstones": len(tombstones),
        "indexed_union": len(rows),
        "states": {
            state: sum(row["state"] == state for row in rows)
            for state in sorted({str(row["state"]) for row in rows})
        },
        "index": "provenance/observatory-versions.jsonl",
        "raw_url_policy": {
            "transport_immutable": False,
            "content_addressed": True,
            "hash_verification_required": True,
            "note": "Raw main URLs are convenience transport; immutability comes from the recorded hash and append-only path policy.",
        },
        "purged_payload_policy": "Explicit tombstones retain metadata and never restore purged bytes.",
    }
    return {
        "provenance/observatory-versions.jsonl": assimilation.jsonl_bytes(rows),
        "provenance/observatory-history.json": assimilation.json_bytes(summary),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generated = outputs()
    if args.check:
        mismatches = [
            path
            for path, data in generated.items()
            if not (ROOT / path).exists() or (ROOT / path).read_bytes() != data
        ]
        if mismatches:
            raise SystemExit("observatory history differs: " + ", ".join(mismatches))
        print("Observatory history reconciliation is deterministic.")
    else:
        for path, data in generated.items():
            assimilation.write_generated(path, data)
        print("Generated observatory frame reconciliation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
