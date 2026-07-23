#!/usr/bin/env python3
"""Verify the immutable LTS grail and optionally make this checkout read-only."""

import argparse
import os
from pathlib import Path
import stat
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools import assimilation
from tools.check_assimilation import IntegrityChecker


def lock_checkout() -> int:
    changed = 0
    root = assimilation.ROOT / assimilation.GRAIL_DESTINATION
    for path in root.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        mode = stat.S_IMODE(os.lstat(str(path)).st_mode)
        locked = mode & ~0o222
        if locked != mode:
            path.chmod(locked)
            changed += 1
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--lock",
        action="store_true",
        help="remove write bits from grail files in this checkout after verification",
    )
    args = parser.parse_args()
    IntegrityChecker().check_grail()
    changed = lock_checkout() if args.lock else 0
    print("immutable grail verified; {} files made read-only".format(changed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
