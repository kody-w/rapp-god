#!/usr/bin/env python3
"""Bind each selected public source pin to its own non-atomic capture time."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools import assimilation  # noqa: E402


ROOT = assimilation.ROOT
OUTPUT = ROOT / "provenance/source-captures.jsonl"
LOCK = ROOT / "provenance/sources.lock.json"
CENSUS = ROOT / "provenance/census-proof.json"


def utc_timestamp(epoch: float) -> str:
    return (
        datetime.fromtimestamp(epoch, timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def git_text(repository: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repository), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def capture_rows(source_cache: Path, sources):
    rows = []
    for source in sorted(sources, key=lambda row: str(row["repository"])):
        name = str(source["repository"]).split("/", 1)[1]
        checkout = source_cache / name
        if not checkout.is_dir():
            raise RuntimeError("selected source checkout is absent: " + name)
        if git_text(checkout, "rev-parse", "HEAD") != source["source_commit"]:
            raise RuntimeError("selected source HEAD differs: " + name)
        if git_text(checkout, "rev-parse", "HEAD^{tree}") != source["source_tree"]:
            raise RuntimeError("selected source tree differs: " + name)
        evidence = checkout / ".git" / "FETCH_HEAD"
        if not evidence.exists():
            evidence = checkout / ".git" / "index"
        if not evidence.exists():
            raise RuntimeError("source capture timestamp evidence is absent: " + name)
        rows.append(
            {
                "repository": source["repository"],
                "source_commit": source["source_commit"],
                "source_tree": source["source_tree"],
                "captured_at": utc_timestamp(evidence.stat().st_mtime),
                "evidence_kind": "local-checkout-fetch-metadata-mtime",
                "atomic_owner_snapshot": False,
            }
        )
    return rows


def window(rows):
    timestamps = sorted(str(row["captured_at"]) for row in rows)
    return {
        "model": "non-atomic-per-repository",
        "atomic_owner_snapshot": False,
        "started_at": timestamps[0],
        "completed_at": timestamps[-1],
        "semantics": (
            "Each repository is frozen independently at its recorded capture "
            "time; later upstream advances do not change the selected pin."
        ),
    }


def generate(source_cache: Path) -> None:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    rows = capture_rows(source_cache, lock["sources"])
    by_repository = {row["repository"]: row for row in rows}
    for source in lock["sources"]:
        source["captured_at"] = by_repository[source["repository"]]["captured_at"]
    lock["capture_window"] = window(rows)
    rows_bytes = assimilation.jsonl_bytes(rows)
    lock_bytes = assimilation.json_bytes(lock)
    census = json.loads(CENSUS.read_text(encoding="utf-8"))
    census["capture_window"] = lock["capture_window"]
    census["bindings"]["source_captures_sha256"] = hashlib.sha256(
        rows_bytes
    ).hexdigest()
    census["bindings"]["sources_lock_sha256"] = hashlib.sha256(lock_bytes).hexdigest()
    assimilation.write_generated(str(OUTPUT.relative_to(ROOT)), rows_bytes)
    assimilation.write_generated(str(LOCK.relative_to(ROOT)), lock_bytes)
    assimilation.write_generated(
        str(CENSUS.relative_to(ROOT)), assimilation.json_bytes(census)
    )
    print(
        "Bound {} per-repository captures across {} to {}.".format(
            len(rows),
            lock["capture_window"]["started_at"],
            lock["capture_window"]["completed_at"],
        )
    )


def check() -> None:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    census = json.loads(CENSUS.read_text(encoding="utf-8"))
    raw = OUTPUT.read_bytes()
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line]
    assert len(rows) == 198
    assert len({row["repository"] for row in rows}) == 198
    assert all(row["atomic_owner_snapshot"] is False for row in rows)
    assert all(
        row["evidence_kind"] == "local-checkout-fetch-metadata-mtime"
        for row in rows
    )
    for row in rows:
        datetime.strptime(row["captured_at"], "%Y-%m-%dT%H:%M:%SZ")
    by_repository = {row["repository"]: row for row in rows}
    for source in lock["sources"]:
        row = by_repository[source["repository"]]
        assert source["source_commit"] == row["source_commit"]
        assert source["source_tree"] == row["source_tree"]
        assert source["captured_at"] == row["captured_at"]
    expected_window = window(rows)
    assert lock["capture_window"] == expected_window
    assert census["capture_window"] == expected_window
    assert census["bindings"]["source_captures_sha256"] == hashlib.sha256(raw).hexdigest()
    assert census["bindings"]["sources_lock_sha256"] == hashlib.sha256(
        LOCK.read_bytes()
    ).hexdigest()
    print("Per-repository non-atomic source capture proof verified.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--source-cache",
        type=Path,
        default=(
            Path(os.environ["RAPP_GOD_SOURCE_CACHE"])
            if "RAPP_GOD_SOURCE_CACHE" in os.environ
            else None
        ),
    )
    args = parser.parse_args()
    if args.check:
        check()
        return 0
    if args.source_cache is None:
        parser.error("--source-cache or RAPP_GOD_SOURCE_CACHE is required")
    generate(args.source_cache.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
