#!/usr/bin/env python3
"""Run the relocated rapp-spine verifier with network fallback disabled."""

import argparse
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SPINE = ROOT / "observatory/components/rapp-spine"
ESTATE = ROOT / "docs/components/rapp-map/estate-map.json"
BLOCKED_EXIT = 3
REQUIRED = (
    SPINE / "verify_spine.py",
    SPINE / "registry.json",
    SPINE / "foundation.json",
    SPINE / "crawl.json",
    SPINE / "coverage.json",
    ESTATE,
)


def private_boundary_applied() -> bool:
    try:
        privacy = json.loads((ROOT / "provenance/privacy-status.json").read_text())
        quarantine = json.loads(
            (ROOT / "provenance/quarantine-summary.json").read_text()
        )
    except (OSError, ValueError):
        return False
    return (
        privacy.get("pending_import_quarantine", {}).get("status") == "applied-v2"
        and quarantine.get("quarantined_target_paths") == 716
        and quarantine.get("quarantined_target_bytes") == 244661926
        and quarantine.get("git_suffix_is_identifier_delimiter") is True
        and quarantine.get("scan_errors") == 0
    )


def state() -> str:
    missing = [path for path in REQUIRED if not path.is_file()]
    if missing:
        if private_boundary_applied():
            return "blocked-private-boundary"
        raise RuntimeError("offline spine inputs are unexpectedly absent")
    mappings = {
        row["destination"]: row
        for row in (
            json.loads(line)
            for line in (ROOT / "provenance/files.jsonl").read_text().splitlines()
            if line
        )
        if row.get("destination")
    }
    from tools import assimilation

    for path in REQUIRED:
        relative = str(path.relative_to(ROOT))
        mapping = mappings.get(relative)
        if mapping is None:
            if private_boundary_applied():
                return "blocked-private-boundary"
            raise RuntimeError("offline spine input lacks an exact ledger pin")
        data = assimilation.file_bytes(path, mapping["source_mode"])
        if assimilation.git_blob_id(data) != mapping["source_blob"]:
            raise RuntimeError("offline spine input differs from its ledger pin")
    json.loads(ESTATE.read_text(encoding="utf-8"))
    return "ready"


def run_verifier() -> int:
    if state() == "blocked-private-boundary":
        return BLOCKED_EXIT
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(SPINE))
    specification = importlib.util.spec_from_file_location(
        "rapp_god_spine_verifier", SPINE / "verify_spine.py"
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("cannot load spine verifier")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    module.LOCAL_ESTATE = ESTATE
    module.get = lambda *_args, **_kwargs: None
    return int(module.main(["--local", "--json"]) or 0)


def main() -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--run", action="store_true")
    action.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.run:
        return run_verifier()
    print("rapp-spine wrapper state=" + state())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
