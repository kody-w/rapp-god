#!/usr/bin/env python3
"""Bind every catalog/provenance artifact to a deterministic digest manifest."""

import argparse
import hashlib
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools import assimilation  # noqa: E402


ROOT = assimilation.ROOT
OUTPUT = ROOT / "provenance/generated-files.jsonl"


def data():
    rows = []
    for base in (ROOT / "catalog", ROOT / "provenance"):
        for path in base.rglob("*"):
            if not path.is_file() or path == OUTPUT:
                continue
            raw = path.read_bytes()
            relative = str(path.relative_to(ROOT))
            rows.append(
                {
                    "path": relative,
                    "bytes": len(raw),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "kind": (
                        "preserved-independent-evidence"
                        if ".source." in path.name
                        else "catalog-or-provenance-artifact"
                    ),
                }
            )
    rows.sort(key=lambda row: row["path"])
    return assimilation.jsonl_bytes(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = data()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_bytes() != expected:
            raise SystemExit("generated catalog/provenance manifest differs")
        print("All catalog/provenance artifact digests are current.")
    else:
        assimilation.write_generated(
            str(OUTPUT.relative_to(ROOT)), expected
        )
        print("Bound every catalog/provenance artifact digest.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
