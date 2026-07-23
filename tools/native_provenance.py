#!/usr/bin/env python3
"""Generate fixed native-baseline, selection, census, and commit-object proofs."""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Dict, List, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools import assimilation  # noqa: E402


ROOT = assimilation.ROOT
BASELINE_COMMIT = "66f47a72767cc59d310ddc07d745cce4d612fae8"
BASELINE_TREE = "89599a90e24bebdbbb4c54e29a5ba11f6871b452"
EXPECTED_EVOLVED = {
    ".github/workflows/god-build.yml",
    "GRAIL_SCAN.md",
    "README.md",
    "api/v1/ECOSYSTEM_SPEC.md",
    "api/v1/badge.json",
    "api/v1/ecosystem-spec.json",
    "api/v1/status.json",
    "build_god.py",
    "manifest.json",
    "registry.json",
}


def run(args: Sequence[str], check: bool = True) -> bytes:
    return subprocess.run(
        list(args), check=check, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ).stdout


def tree_entries(repository: Path, ref: str) -> List[Dict[str, object]]:
    raw = run(
        (
            "git",
            "-C",
            str(repository),
            "ls-tree",
            "-rz",
            "-l",
            "--full-tree",
            ref,
        )
    )
    rows = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, path = record.split(b"\t", 1)
        mode, object_type, object_id, size = metadata.split(b" ", 3)
        size = size.strip()
        rows.append(
            {
                "path": path.decode("utf-8", "surrogateescape"),
                "mode": mode.decode("ascii"),
                "type": object_type.decode("ascii"),
                "object": object_id.decode("ascii"),
                "size": None if size == b"-" else int(size),
            }
        )
    return rows


def object_bytes(repository: Path, object_id: str, object_type: str) -> bytes:
    return run(("git", "-C", str(repository), "cat-file", object_type, object_id))


def current_mode(path: Path) -> str:
    if path.is_symlink():
        return "120000"
    executable = bool(os.lstat(str(path)).st_mode & 0o100)
    return "100755" if executable else "100644"


def native_rows() -> List[Dict[str, object]]:
    if run(("git", "-C", str(ROOT), "rev-parse", BASELINE_COMMIT)).decode().strip() != BASELINE_COMMIT:
        raise RuntimeError("native baseline commit is unavailable")
    if (
        run(("git", "-C", str(ROOT), "rev-parse", BASELINE_COMMIT + "^{tree}"))
        .decode()
        .strip()
        != BASELINE_TREE
    ):
        raise RuntimeError("native baseline tree differs")
    rows = []
    evolved = set()
    for entry in tree_entries(ROOT, BASELINE_COMMIT):
        before = object_bytes(ROOT, str(entry["object"]), "blob")
        path = ROOT / str(entry["path"])
        if not os.path.lexists(str(path)):
            raise RuntimeError("native baseline path was removed: {}".format(entry["path"]))
        after = assimilation.file_bytes(path, current_mode(path))
        after_mode = current_mode(path)
        disposition = (
            "native-preserved"
            if assimilation.git_blob_id(after) == entry["object"]
            and after_mode == entry["mode"]
            else "native-evolved"
        )
        if disposition == "native-evolved":
            evolved.add(str(entry["path"]))
        rows.append(
            {
                "repository": "kody-w/rapp-god",
                "baseline_commit": BASELINE_COMMIT,
                "baseline_tree": BASELINE_TREE,
                "path": entry["path"],
                "before_mode": entry["mode"],
                "before_blob": entry["object"],
                "before_size": entry["size"],
                "before_sha256": hashlib.sha256(before).hexdigest(),
                "closure_mode": after_mode,
                "closure_blob": assimilation.git_blob_id(after),
                "closure_size": len(after),
                "closure_sha256": hashlib.sha256(after).hexdigest(),
                "disposition": disposition,
                "closure_snapshot": "staged-assimilation-closure",
            }
        )
    if len(rows) != 284 or evolved != EXPECTED_EVOLVED:
        raise RuntimeError(
            "native closure differs: {} entries, evolved {}".format(
                len(rows), sorted(evolved)
            )
        )
    return rows


def raw_commit_record(repository: str, checkout: Path, source: Dict[str, object]):
    commit = str(source["source_commit"])
    raw = object_bytes(checkout, commit, "commit")
    oid = hashlib.sha1(
        "commit {}\0".format(len(raw)).encode("ascii") + raw
    ).hexdigest()
    if oid != commit:
        raise RuntimeError("commit object OID mismatch for " + repository)
    tree_line = next(
        (line for line in raw.splitlines() if line.startswith(b"tree ")), None
    )
    if tree_line is None:
        raise RuntimeError("commit object lacks tree for " + repository)
    tree = tree_line.split(b" ", 1)[1].decode("ascii")
    if tree != source["source_tree"]:
        raise RuntimeError("commit object tree mismatch for " + repository)
    return {
        "repository": repository,
        "commit": commit,
        "tree": tree,
        "object_type": "commit",
        "object_bytes": len(raw),
        "raw_base64": base64.b64encode(raw).decode("ascii"),
        "disposition": "public-commit-object-proof",
    }


def generate(source_cache: Path) -> None:
    privacy_path = ROOT / "provenance/privacy-status.json"
    if privacy_path.exists():
        privacy = json.loads(privacy_path.read_text())
        if privacy.get("pending_import_quarantine", {}).get("status") == "applied":
            raise RuntimeError(
                "refusing to regenerate unsanitized commit objects after quarantine"
            )
    lock_path = ROOT / "provenance/sources.lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    sources = sorted(lock["sources"], key=lambda row: str(row["repository"]))
    selected_bytes = "".join(
        str(row["repository"]) + "\n" for row in sources
    ).encode("utf-8")
    selected_digest = hashlib.sha256(selected_bytes).hexdigest()
    native = native_rows()
    commit_rows = []
    for source in sources:
        repository = str(source["repository"])
        name = repository.split("/", 1)[1]
        checkout = source_cache / name
        if not checkout.is_dir():
            raise RuntimeError("selected source checkout is absent: " + name)
        commit_rows.append(raw_commit_record(repository, checkout, source))
    lock["native_baseline"] = {
        "commit": BASELINE_COMMIT,
        "tree": BASELINE_TREE,
        "file_count": 284,
        "preserved": 274,
        "evolved": 10,
        "ledger": "provenance/native-files.jsonl",
    }
    lock["selected_repositories"] = {
        "path": "provenance/selected-repositories.txt",
        "sha256": selected_digest,
        "records": len(sources),
    }
    lock_bytes = assimilation.json_bytes(lock)
    repositories_bytes = (ROOT / "provenance/repositories.jsonl").read_bytes()
    commit_bytes = assimilation.jsonl_bytes(commit_rows)
    census = {
        "schema": "rapp-god-public-census-proof/1",
        "scope": "public-source-capture-only",
        "public_repositories": 370,
        "selected_repositories": 198,
        "external_imports": 197,
        "public_tree_entries": 42175,
        "public_logical_bytes": 1904914693,
        "private_quarantine": {
            "count": 142,
            "disposition": "aggregate-only-not-imported",
            "note": "No private source payload or per-repository private metadata is part of this proof.",
        },
        "bindings": {
            "selected_repositories_sha256": selected_digest,
            "repositories_jsonl_sha256": hashlib.sha256(repositories_bytes).hexdigest(),
            "sources_lock_sha256": hashlib.sha256(lock_bytes).hexdigest(),
            "commit_objects_sha256": hashlib.sha256(commit_bytes).hexdigest(),
            "native_files_sha256": hashlib.sha256(
                assimilation.jsonl_bytes(native)
            ).hexdigest(),
        },
        "commit_object_records": len(commit_rows),
        "native_baseline_commit": BASELINE_COMMIT,
        "native_baseline_tree": BASELINE_TREE,
    }
    assimilation.write_generated(
        "provenance/selected-repositories.txt", selected_bytes
    )
    assimilation.write_generated("provenance/native-files.jsonl", assimilation.jsonl_bytes(native))
    assimilation.write_generated("provenance/commit-objects.jsonl", commit_bytes)
    assimilation.write_generated("provenance/sources.lock.json", lock_bytes)
    assimilation.write_generated(
        "provenance/census-proof.json", assimilation.json_bytes(census)
    )
    print("Bound 198 selected commits and 284 native baseline entries.")


def refresh_native_only() -> None:
    native = native_rows()
    native_bytes = assimilation.jsonl_bytes(native)
    lock_path = ROOT / "provenance/sources.lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    lock["native_baseline"] = {
        "commit": BASELINE_COMMIT,
        "tree": BASELINE_TREE,
        "file_count": 284,
        "preserved": 274,
        "evolved": 10,
        "ledger": "provenance/native-files.jsonl",
    }
    lock_bytes = assimilation.json_bytes(lock)
    census_path = ROOT / "provenance/census-proof.json"
    census = json.loads(census_path.read_text(encoding="utf-8"))
    census["bindings"]["native_files_sha256"] = hashlib.sha256(native_bytes).hexdigest()
    census["bindings"]["sources_lock_sha256"] = hashlib.sha256(lock_bytes).hexdigest()
    assimilation.write_generated("provenance/native-files.jsonl", native_bytes)
    assimilation.write_generated("provenance/sources.lock.json", lock_bytes)
    assimilation.write_generated(
        "provenance/census-proof.json", assimilation.json_bytes(census)
    )
    print("Refreshed 284 native closure records without private source inputs.")


def check() -> None:
    selected_path = ROOT / "provenance/selected-repositories.txt"
    native_path = ROOT / "provenance/native-files.jsonl"
    commits_path = ROOT / "provenance/commit-objects.jsonl"
    lock = json.loads((ROOT / "provenance/sources.lock.json").read_text())
    census = json.loads((ROOT / "provenance/census-proof.json").read_text())
    selected = selected_path.read_bytes()
    assert hashlib.sha256(selected).hexdigest() == lock["selected_repositories"]["sha256"]
    assert selected.count(b"\n") == 198
    native = [
        json.loads(line) for line in native_path.read_text().splitlines() if line
    ]
    assert len(native) == 284
    assert sum(row["disposition"] == "native-preserved" for row in native) == 274
    assert sum(row["disposition"] == "native-evolved" for row in native) == 10
    baseline_entries = {
        row["path"]: row for row in tree_entries(ROOT, BASELINE_COMMIT)
    }
    for row in native:
        source = baseline_entries[row["path"]]
        raw = object_bytes(ROOT, str(source["object"]), "blob")
        assert row["before_blob"] == source["object"]
        assert row["before_mode"] == source["mode"]
        assert row["before_sha256"] == hashlib.sha256(raw).hexdigest()
        path = ROOT / row["path"]
        assert os.path.lexists(str(path))
        mode = current_mode(path)
        current = assimilation.file_bytes(path, mode)
        assert row["closure_mode"] == mode
        assert row["closure_blob"] == assimilation.git_blob_id(current)
        assert row["closure_size"] == len(current)
        assert row["closure_sha256"] == hashlib.sha256(current).hexdigest()
        assert row["closure_snapshot"] == "staged-assimilation-closure"
    assert census["bindings"]["native_files_sha256"] == hashlib.sha256(
        native_path.read_bytes()
    ).hexdigest()
    commits_raw = commits_path.read_bytes()
    commits = [json.loads(line) for line in commits_raw.decode().splitlines() if line]
    assert len(commits) == 198
    source_by_repo = {row["repository"]: row for row in lock["sources"]}
    retained = [row for row in commits if row.get("raw_base64")]
    withheld = [
        row for row in commits if row.get("record_kind") == "withheld-commit-object"
    ]
    assert len(retained) == 140
    assert len(withheld) == 58
    assert all(
        set(row) == {"record_kind", "withheld_ordinal", "disposition"}
        for row in withheld
    )
    for row in retained:
        raw = base64.b64decode(row["raw_base64"], validate=True)
        oid = hashlib.sha1(
            "commit {}\0".format(len(raw)).encode("ascii") + raw
        ).hexdigest()
        assert oid == row["commit"]
        tree = next(
            line.split(b" ", 1)[1].decode("ascii")
            for line in raw.splitlines()
            if line.startswith(b"tree ")
        )
        assert tree == row["tree"] == source_by_repo[row["repository"]]["source_tree"]
    assert hashlib.sha256(commits_raw).hexdigest() == census["bindings"][
        "commit_objects_sha256"
    ]
    assert census["commit_object_records"] == {"retained": 140, "withheld": 58}
    assert census["private_quarantine"]["count"] == 142
    print("Native, selection, census, and commit-object proofs verified.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--refresh-native-only", action="store_true")
    parser.add_argument(
        "--source-cache",
        type=Path,
        default=Path(
            os.environ.get("RAPP_GOD_SOURCE_CACHE", str(assimilation.DEFAULT_CACHE))
        ),
    )
    args = parser.parse_args()
    if args.check and args.refresh_native_only:
        parser.error("--check and --refresh-native-only are mutually exclusive")
    if args.check:
        check()
    elif args.refresh_native_only:
        refresh_native_only()
    else:
        generate(args.source_cache.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
