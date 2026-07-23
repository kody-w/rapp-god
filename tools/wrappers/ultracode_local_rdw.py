#!/usr/bin/env python3
"""Run UltraCode tests against the assimilated RDW source overlay."""

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
RDW = ROOT / "src/workflows/rapp-dynamic-workflows"
ULTRACODE = ROOT / "src/workflows/rapp-ultracode"


def environment():
    paths = [str(RDW), str(ULTRACODE / "src")]
    existing = os.environ.get("PYTHONPATH")
    if existing:
        paths.append(existing)
    return {
        **os.environ,
        "PYTHONPATH": os.pathsep.join(paths),
        "PYTHONDONTWRITEBYTECODE": "1",
        "RAPP_GOD_LOCAL_RDW": str(RDW),
    }


def check_configuration() -> None:
    if not (RDW / "rdw").is_dir():
        raise RuntimeError("assimilated RDW package is absent")
    if not (ULTRACODE / "src/rapp_ultracode").is_dir():
        raise RuntimeError("assimilated UltraCode package is absent")
    if "git+" in (ULTRACODE / "pyproject.toml").read_text(encoding="utf-8"):
        pass
    else:
        raise RuntimeError("expected upstream remote dependency evidence is absent")


def main() -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--run", action="store_true")
    action.add_argument("--check", action="store_true")
    args = parser.parse_args()
    check_configuration()
    if args.run:
        python = (
            os.environ.get("RAPP_GOD_PYTHON311")
            or (sys.executable if sys.version_info >= (3, 11) else None)
            or shutil.which("python3.12")
            or shutil.which("python3.11")
        )
        if not python:
            raise RuntimeError(
                "UltraCode/RDW overlay tests require Python >=3.11; set RAPP_GOD_PYTHON311"
            )
        return subprocess.run(
            [
                python,
                "-m",
                "pytest",
                "tests",
                "-q",
                "-p",
                "no:cacheprovider",
            ],
            cwd=str(ULTRACODE),
            env=environment(),
        ).returncode
    print("UltraCode overlay resolves RDW from {}".format(RDW.relative_to(ROOT)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
