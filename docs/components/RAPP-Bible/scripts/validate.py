#!/usr/bin/env python3
"""
RAPP Bible — validate.

Runs the Bible's own test suite (`tests/`), which includes the spec-freshness
and link checks.

Note: upstream cross-validators (e.g. RAPP-Network's `scripts/cross_validate.py`)
are NOT invoked here — `mirror_sync.py` only fetches spec files, not validator
scripts, so there is nothing to shell out to. If validator scripts are ever
mirrored in the future, wire them in here and update this docstring.

Usage:
    python3 scripts/validate.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def run_pytest() -> int:
    print("=== Running pytest tests/ ===")
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v"],
        cwd=REPO_ROOT,
    )
    return proc.returncode


def main() -> int:
    rc = run_pytest()
    if rc != 0:
        print(f"\nFAIL: pytest exit code {rc}")
        return rc
    print("\nOK: all validators passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
