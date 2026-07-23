#!/usr/bin/env python3
"""Offline rapp-map gate using pinned blob IDs instead of unavailable history."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[2]
COMPONENT = ROOT / "docs/components/rapp-map"
PINNED_BLOBS = {
    "neurons.json": "007e99fef9b38d782679e08b9c3842472f9f458a",
    "neurons-manifest.json": "c09f206f8fa93c328e81a8207fe93eb6cc4c948e",
}
REQUIRED_INPUTS = {"estate-map.json", *PINNED_BLOBS}
BLOCKED_EXIT = 3


def git_blob_id(data: bytes) -> str:
    return hashlib.sha1(
        "blob {}\0".format(len(data)).encode("ascii") + data
    ).hexdigest()


def private_boundary_applied() -> bool:
    try:
        privacy = json.loads(
            (ROOT / "provenance/privacy-status.json").read_text()
        )
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
    missing = [relative for relative in REQUIRED_INPUTS if not (COMPONENT / relative).is_file()]
    if missing:
        if private_boundary_applied():
            return "blocked-private-boundary"
        raise RuntimeError("rapp-map wrapper inputs are unexpectedly absent")
    for relative, expected in PINNED_BLOBS.items():
        path = COMPONENT / relative
        if git_blob_id(path.read_bytes()) != expected:
            raise RuntimeError("pinned rapp-map evidence differs: " + relative)
    # The estate map has no publishable post-quarantine hash pin.
    if private_boundary_applied():
        return "blocked-private-boundary"
    return "ready"


def run_gates() -> None:
    current = state()
    if current == "blocked-private-boundary":
        raise SystemExit(BLOCKED_EXIT)
    python = os.environ.get("RAPP_GOD_PYTHON312") or shutil.which("python3.12")
    if not python:
        raise RuntimeError(
            "rapp-map offline gate requires Python 3.12; set RAPP_GOD_PYTHON312"
        )
    guard = COMPONENT / ".github/scripts/offline-guard.mjs"
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": str(ROOT / ".rapp-god-input/offline-home"),
        "LANG": "C",
        "CI": "true",
        "NO_COLOR": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
    }
    node_environment = {
        **environment,
        "NODE_OPTIONS": "--import={}".format(guard),
    }
    commands = [
        (["node", "conformance/run-conformance.mjs"], node_environment),
        (["node", "conformance/waiver-freshness.mjs"], node_environment),
        (["node", "tests/run-regressions.mjs"], node_environment),
        (["node", "tests/offline-guard-probe.mjs"], node_environment),
        ([python, "-I", "build_graph.py", "--check"], environment),
        (["node", ".github/scripts/standing-guard.mjs", "local"], node_environment),
        (["node", ".github/scripts/standing-guard.mjs", "blocker"], node_environment),
    ]
    for command, command_environment in commands:
        subprocess.run(
            command,
            cwd=str(COMPONENT),
            env=command_environment,
            check=True,
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--run", action="store_true")
    action.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.run:
        run_gates()
    else:
        print("rapp-map wrapper state=" + state())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
