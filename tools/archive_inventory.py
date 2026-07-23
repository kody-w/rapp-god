#!/usr/bin/env python3
"""Signature-discover and recursively index ZIP/TAR containers without extraction."""

import argparse
from collections import Counter
from io import BytesIO
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tarfile
from typing import Dict, List, Optional, Sequence, Tuple
import zipfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools import assimilation  # noqa: E402


ROOT = assimilation.ROOT
SOURCE_COPY = "provenance/archive-audit.source.json"
PASS1_COPY = "provenance/archive-audit-pass1.source.json"
MEMBER_INDEX = "provenance/archive-members.jsonl"
CONTAINER_INDEX = "provenance/archive-containers.jsonl"
PROOF = "provenance/archive-audit-proof.json"
MAX_DEPTH = 4

SECRET_BYTES = {
    name: re.compile(pattern.encode("ascii"))
    for name, pattern in assimilation.SECRET_PATTERNS.items()
}


def load_jsonl(path: Path) -> List[Dict[str, object]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def dangerous_path(name: str) -> bool:
    normalized = name.replace("\\", "/")
    return (
        normalized.startswith("/")
        or bool(re.match(r"^[A-Za-z]:/", normalized))
        or ".." in PurePosixPath(normalized).parts
        or any(ord(character) < 32 for character in normalized)
    )


def member_secret_patterns(data: bytes) -> List[str]:
    return sorted(name for name, pattern in SECRET_BYTES.items() if pattern.search(data))


def candidate_format(prefix: bytes) -> Optional[str]:
    if prefix.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")):
        return "zip"
    if len(prefix) >= 265 and prefix[257:262] == b"ustar":
        return "tar"
    if prefix.startswith(
        (
            b"\x1f\x8b",
            b"BZh",
            b"\xfd7zXZ\x00",
        )
    ):
        return "tar"
    return None


def verified_format(data: bytes) -> Optional[str]:
    candidate = candidate_format(data[:512])
    if candidate == "zip":
        try:
            with zipfile.ZipFile(BytesIO(data)):
                return "zip"
        except (OSError, zipfile.BadZipFile):
            return None
    if candidate == "tar":
        try:
            with tarfile.open(fileobj=BytesIO(data), mode="r:*"):
                return "tar"
        except (OSError, tarfile.TarError):
            return None
    return None


def container_id(repository: str, source_ref: str, locator: str) -> str:
    return hashlib.sha256(
        (repository + "\0" + source_ref + "\0" + locator).encode("utf-8")
    ).hexdigest()


def base_container(
    repository: str,
    source_ref: str,
    source_path: str,
    locator: str,
    archive_format: str,
    data: bytes,
    depth: int,
    parent_id: Optional[str],
    parent_member: Optional[str],
) -> Dict[str, object]:
    return {
        "container_id": container_id(repository, source_ref, locator),
        "repository": repository,
        "source_ref": source_ref,
        "source_path": source_path,
        "container_locator": locator,
        "format": archive_format,
        "depth": depth,
        "parent_container_id": parent_id,
        "parent_member": parent_member,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "disposition": "indexed-not-extracted",
    }


def scan_container(
    repository: str,
    source_ref: str,
    source_path: str,
    locator: str,
    data: bytes,
    archive_format: str,
    depth: int,
    parent_id: Optional[str],
    parent_member: Optional[str],
    containers: List[Dict[str, object]],
    members: List[Dict[str, object]],
    errors: List[Dict[str, object]],
) -> None:
    container = base_container(
        repository,
        source_ref,
        source_path,
        locator,
        archive_format,
        data,
        depth,
        parent_id,
        parent_member,
    )
    direct_rows = []
    nested = []
    names = []
    try:
        if archive_format == "zip":
            with zipfile.ZipFile(BytesIO(data)) as archive:
                for index, info in enumerate(archive.infolist()):
                    names.append(info.filename)
                    unix_mode = (info.external_attr >> 16) & 0xFFFF
                    is_link = stat.S_ISLNK(unix_mode)
                    is_directory = info.is_dir()
                    encrypted = bool(info.flag_bits & 0x1)
                    body = None
                    if not is_directory and not encrypted:
                        with archive.open(info, "r") as member:
                            body = member.read()
                        if len(body) != info.file_size:
                            raise RuntimeError("ZIP member size differs")
                    link_target = None
                    if is_link and body is not None:
                        link_target = body.decode("utf-8", "surrogateescape")
                    row = {
                        "container_id": container["container_id"],
                        "repository": repository,
                        "source_ref": source_ref,
                        "container_locator": locator,
                        "member_index": index,
                        "member_path": info.filename,
                        "member_type": (
                            "directory"
                            if is_directory
                            else "symlink"
                            if is_link
                            else "file"
                        ),
                        "uncompressed_bytes": info.file_size,
                        "compressed_bytes": info.compress_size,
                        "mode": format(unix_mode, "06o") if unix_mode else None,
                        "crc32": format(info.CRC, "08x"),
                        "sha256": hashlib.sha256(body).hexdigest() if body is not None else None,
                        "link_target": link_target,
                        "dangerous_path": dangerous_path(info.filename),
                        "dangerous_link_target": (
                            dangerous_path(link_target) if link_target is not None else False
                        ),
                        "encrypted": encrypted,
                        "secret_patterns": member_secret_patterns(body or b""),
                        "disposition": "indexed-not-extracted",
                    }
                    direct_rows.append(row)
                    if body is not None and depth < MAX_DEPTH:
                        nested_format = verified_format(body)
                        if nested_format:
                            nested.append((info.filename, body, nested_format))
        else:
            with tarfile.open(fileobj=BytesIO(data), mode="r:*") as archive:
                for index, info in enumerate(archive.getmembers()):
                    names.append(info.name)
                    body = None
                    if info.isfile():
                        extracted = archive.extractfile(info)
                        if extracted is None:
                            raise RuntimeError("TAR member cannot be read")
                        with extracted:
                            body = extracted.read()
                        if len(body) != info.size:
                            raise RuntimeError("TAR member size differs")
                    link_target = info.linkname if info.issym() or info.islnk() else None
                    row = {
                        "container_id": container["container_id"],
                        "repository": repository,
                        "source_ref": source_ref,
                        "container_locator": locator,
                        "member_index": index,
                        "member_path": info.name,
                        "member_type": (
                            "directory"
                            if info.isdir()
                            else "symlink"
                            if info.issym()
                            else "hardlink"
                            if info.islnk()
                            else "file"
                            if info.isfile()
                            else "special"
                        ),
                        "uncompressed_bytes": info.size,
                        "compressed_bytes": None,
                        "mode": format(info.mode, "06o"),
                        "crc32": None,
                        "sha256": hashlib.sha256(body).hexdigest() if body is not None else None,
                        "link_target": link_target,
                        "dangerous_path": dangerous_path(info.name),
                        "dangerous_link_target": (
                            dangerous_path(link_target) if link_target else False
                        ),
                        "encrypted": False,
                        "secret_patterns": member_secret_patterns(body or b""),
                        "disposition": "indexed-not-extracted",
                    }
                    direct_rows.append(row)
                    if body is not None and depth < MAX_DEPTH:
                        nested_format = verified_format(body)
                        if nested_format:
                            nested.append((info.name, body, nested_format))
    except Exception as error:
        errors.append(
            {
                "repository": repository,
                "container_locator": locator,
                "error_type": type(error).__name__,
            }
        )
        return
    duplicate_names = sum(
        count - 1 for count in Counter(names).values() if count > 1
    )
    container.update(
        {
            "members": len(direct_rows),
            "uncompressed_bytes": sum(
                int(row["uncompressed_bytes"]) for row in direct_rows
            ),
            "max_member_bytes": max(
                (int(row["uncompressed_bytes"]) for row in direct_rows), default=0
            ),
            "dangerous_paths": sum(bool(row["dangerous_path"]) for row in direct_rows),
            "dangerous_link_targets": sum(
                bool(row["dangerous_link_target"]) for row in direct_rows
            ),
            "duplicate_names": duplicate_names,
            "encrypted_members": sum(bool(row["encrypted"]) for row in direct_rows),
            "secret_hits": sum(bool(row["secret_patterns"]) for row in direct_rows),
            "scan_complete": True,
        }
    )
    containers.append(container)
    members.extend(direct_rows)
    for member_name, nested_data, nested_format in nested:
        scan_container(
            repository,
            source_ref,
            source_path,
            locator + "!" + member_name,
            nested_data,
            nested_format,
            depth + 1,
            str(container["container_id"]),
            member_name,
            containers,
            members,
            errors,
        )


def scope_rows(mappings: Sequence[Dict[str, object]]):
    return [
        row
        for row in mappings
        if row.get("destination")
        and row.get("source_path")
        and row.get("source_mode") in {"100644", "100755"}
    ]


def scan_paths(
    mappings: Sequence[Dict[str, object]],
    reader,
) -> Tuple[List[Dict[str, object]], List[Dict[str, object]], List[Dict[str, object]]]:
    containers: List[Dict[str, object]] = []
    members: List[Dict[str, object]] = []
    errors: List[Dict[str, object]] = []
    for mapping in scope_rows(mappings):
        prefix, data = reader(mapping)
        archive_format = candidate_format(prefix)
        if archive_format is None:
            continue
        if data is None:
            errors.append(
                {
                    "repository": mapping["source_repository"],
                    "container_locator": mapping["source_path"],
                    "error_type": "UnreadableCandidate",
                }
            )
            continue
        archive_format = verified_format(data)
        if archive_format is None:
            continue
        scan_container(
            str(mapping["source_repository"]),
            str(mapping["source_ref"]),
            str(mapping["source_path"]),
            str(mapping["source_path"]),
            data,
            archive_format,
            0,
            None,
            None,
            containers,
            members,
            errors,
        )
    containers.sort(
        key=lambda row: (
            str(row["repository"]),
            str(row["source_ref"]),
            str(row["container_locator"]),
        )
    )
    members.sort(
        key=lambda row: (
            str(row["repository"]),
            str(row["source_ref"]),
            str(row["container_locator"]),
            int(row["member_index"]),
        )
    )
    return containers, members, errors


def source_reader(source_cache: Path):
    def read(mapping):
        repository = str(mapping["source_repository"]).split("/", 1)[1]
        checkout = (
            source_cache / assimilation.GRAIL_DIRECTORY
            if mapping.get("authority_alias")
            else source_cache / repository
        )
        path = checkout / str(mapping["source_path"])
        try:
            with path.open("rb") as handle:
                prefix = handle.read(512)
                if candidate_format(prefix) is None:
                    return prefix, None
                return prefix, prefix + handle.read()
        except OSError:
            return b"", None

    return read


def target_reader(mapping):
    path = ROOT / str(mapping["destination"])
    try:
        with path.open("rb") as handle:
            prefix = handle.read(512)
            if candidate_format(prefix) is None:
                return prefix, None
            return prefix, prefix + handle.read()
    except OSError:
        return b"", None


def evidence_document(
    captured_at: str,
    mappings: Sequence[Dict[str, object]],
    containers: Sequence[Dict[str, object]],
    members: Sequence[Dict[str, object]],
    errors: Sequence[Dict[str, object]],
) -> Dict[str, object]:
    top = [row for row in containers if row["depth"] == 0]
    nested = [row for row in containers if row["depth"] > 0]
    return {
        "schema": "rapp-source-archive-audit/2.0",
        "captured_at": captured_at,
        "scope": {
            "selected_external_repositories": 197,
            "source_trees": 198,
            "includes_grail": True,
            "regular_tracked_files": len(scope_rows(mappings)),
        },
        "discovery": "file-signature-recursive",
        "top_level_containers": len(top),
        "nested_containers": len(nested),
        "formats": dict(sorted(Counter(str(row["format"]) for row in containers).items())),
        "archive_members": len(members),
        "archive_uncompressed_bytes": sum(
            int(row["uncompressed_bytes"]) for row in members
        ),
        "dangerous_paths": sum(bool(row["dangerous_path"]) for row in members),
        "dangerous_link_targets": sum(
            bool(row["dangerous_link_target"]) for row in members
        ),
        "encrypted_members": sum(bool(row["encrypted"]) for row in members),
        "duplicate_names": sum(int(row["duplicate_names"]) for row in containers),
        "archive_member_secret_hits": sum(
            bool(row["secret_patterns"]) for row in members
        ),
        "incomplete_scans": sum(not bool(row["scan_complete"]) for row in containers),
        "errors": list(errors),
        "containers": list(containers),
        "members": list(members),
    }


def scan_source(source_cache: Path, output: Path, captured_at: str) -> None:
    mappings = load_jsonl(ROOT / "provenance/files.jsonl")
    containers, members, errors = scan_paths(mappings, source_reader(source_cache))
    evidence = evidence_document(captured_at, mappings, containers, members, errors)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(assimilation.json_bytes(evidence))
    print(
        "Source evidence: {} top-level + {} nested containers, {} members.".format(
            evidence["top_level_containers"],
            evidence["nested_containers"],
            evidence["archive_members"],
        )
    )


def comparable_container(row: Dict[str, object]) -> Dict[str, object]:
    return dict(row)


def generate(evidence_path: Path, check: bool = False) -> None:
    evidence_raw = evidence_path.read_bytes()
    evidence = json.loads(evidence_raw)
    if evidence.get("schema") != "rapp-source-archive-audit/2.0":
        raise RuntimeError("unexpected archive evidence schema")
    mappings = load_jsonl(ROOT / "provenance/files.jsonl")
    containers, members, errors = scan_paths(mappings, target_reader)
    target_evidence = evidence_document(
        str(evidence["captured_at"]), mappings, containers, members, errors
    )
    for key in (
        "scope",
        "discovery",
        "top_level_containers",
        "nested_containers",
        "formats",
        "archive_members",
        "archive_uncompressed_bytes",
        "dangerous_paths",
        "dangerous_link_targets",
        "encrypted_members",
        "duplicate_names",
        "archive_member_secret_hits",
        "incomplete_scans",
        "errors",
        "containers",
        "members",
    ):
        if target_evidence[key] != evidence[key]:
            raise RuntimeError("target archive scan differs from source evidence: " + key)
    member_bytes = assimilation.jsonl_bytes(members)
    container_bytes = assimilation.jsonl_bytes(containers)
    proof = {
        "schema": "rapp-god-archive-proof/2",
        "captured_at": evidence["captured_at"],
        "independent_evidence": {
            "path": SOURCE_COPY,
            "sha256": hashlib.sha256(evidence_raw).hexdigest(),
        },
        "scope": evidence["scope"],
        "discovery": evidence["discovery"],
        "containers": {
            "top_level": evidence["top_level_containers"],
            "nested": evidence["nested_containers"],
            "formats": evidence["formats"],
            "index": CONTAINER_INDEX,
            "sha256": hashlib.sha256(container_bytes).hexdigest(),
        },
        "members": {
            "records": evidence["archive_members"],
            "uncompressed_bytes": evidence["archive_uncompressed_bytes"],
            "index": MEMBER_INDEX,
            "sha256": hashlib.sha256(member_bytes).hexdigest(),
        },
        "safety": {
            "dangerous_paths": evidence["dangerous_paths"],
            "dangerous_link_targets": evidence["dangerous_link_targets"],
            "encrypted_members": evidence["encrypted_members"],
            "duplicate_names": evidence["duplicate_names"],
            "secret_hits": evidence["archive_member_secret_hits"],
            "incomplete_scans": evidence["incomplete_scans"],
            "errors": len(evidence["errors"]),
        },
        "disposition": "indexed-not-extracted",
        "generator": "tools/archive_inventory.py",
    }
    generated = {
        SOURCE_COPY: evidence_raw,
        MEMBER_INDEX: member_bytes,
        CONTAINER_INDEX: container_bytes,
        PROOF: assimilation.json_bytes(proof),
    }
    if check:
        mismatches = [
            path
            for path, data in generated.items()
            if not (ROOT / path).exists() or (ROOT / path).read_bytes() != data
        ]
        if mismatches:
            raise RuntimeError("archive proof differs: " + ", ".join(mismatches))
        print("Recursive archive proof is deterministic.")
    else:
        old_source = ROOT / "provenance/archive-audit.source.json"
        old_pass1 = ROOT / PASS1_COPY
        if old_source.exists() and not old_pass1.exists():
            assimilation.write_generated(PASS1_COPY, old_source.read_bytes())
        for path, data in generated.items():
            assimilation.write_generated(path, data)
        print(
            "Indexed {} top-level + {} nested containers and {} members.".format(
                evidence["top_level_containers"],
                evidence["nested_containers"],
                evidence["archive_members"],
            )
        )


def check_public() -> None:
    proof = json.loads((ROOT / PROOF).read_text())
    if proof.get("schema") not in {
        "rapp-god-archive-proof/3",
        "rapp-god-archive-proof/4",
    }:
        raise RuntimeError("unexpected sanitized archive proof schema")
    if proof.get("schema") == "rapp-god-archive-proof/4":
        assert proof["private_boundary_v2"] == {
            "current_staged_top_level_containers": 91,
            "current_staged_nested_containers": 2,
            "current_staged_members": 2581,
            "prior_withheld_paths": 703,
            "additional_withheld_paths": 13,
            "total_withheld_paths": 716,
            "session_evidence_copied": False,
            "git_suffix_is_identifier_delimiter": True,
        }
    mappings = load_jsonl(ROOT / "provenance/files.jsonl")
    containers, members, errors = scan_paths(mappings, target_reader)
    if errors:
        raise RuntimeError("retained archive scan has errors")
    container_bytes = assimilation.jsonl_bytes(containers)
    member_bytes = assimilation.jsonl_bytes(members)
    retained = proof["retained"]
    assert len(containers) == retained["containers"]
    assert len(members) == retained["members"]
    assert hashlib.sha256(container_bytes).hexdigest() == retained[
        "container_index_sha256"
    ]
    assert hashlib.sha256(member_bytes).hexdigest() == retained[
        "member_index_sha256"
    ]
    assert (ROOT / retained["container_index"]).read_bytes() == container_bytes
    assert (ROOT / retained["member_index"]).read_bytes() == member_bytes
    assert not any(row["dangerous_path"] for row in members)
    assert not any(row["dangerous_link_target"] for row in members)
    assert not any(row["secret_patterns"] for row in members)
    print("Sanitized recursive archive proof is deterministic.")


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    source = subparsers.add_parser("scan-source")
    source.add_argument("--source-cache", type=Path, required=True)
    source.add_argument("--output", type=Path, required=True)
    source.add_argument("--captured-at", required=True)
    target = subparsers.add_parser("generate")
    target.add_argument("--evidence", type=Path, required=True)
    target.add_argument("--check", action="store_true")
    subparsers.add_parser("check-public")
    args = parser.parse_args()
    if args.command == "scan-source":
        scan_source(args.source_cache.resolve(), args.output.resolve(), args.captured_at)
    elif args.command == "generate":
        generate(args.evidence.resolve(), check=args.check)
    else:
        check_public()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
