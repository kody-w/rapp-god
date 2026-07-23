#!/usr/bin/env python3
"""Apply a sensitive session-only deny set without publishing its contents."""

import argparse
import base64
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import unicodedata


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools import assimilation  # noqa: E402


ROOT = assimilation.ROOT
EXPECTED_PUBLIC = {
    "pending_import_paths_scanned": 42228,
    "pending_regular_paths_scanned": 42222,
    "pending_symlink_paths_scanned": 6,
    "top_level_archive_containers_scanned": 100,
    "nested_archive_containers_scanned": 2,
    "archive_members_scanned": 3086,
    "quarantined_target_paths": 703,
    "quarantined_regular_paths": 703,
    "quarantined_symlink_paths": 0,
    "quarantined_archive_paths": 9,
    "quarantined_target_bytes": 244267497,
    "path_match_paths": 508,
    "content_match_paths": 194,
    "archive_member_matches": 14,
    "archive_member_content_matches": 8,
    "archive_member_path_matches": 6,
    "archive_member_identifier_occurrences": 23,
    "maximum_archive_depth": 2,
    "matched_private_repository_identifier_count": 138,
    "private_repository_inventory_count": 142,
    "path_identifier_occurrences": 510,
    "content_identifier_occurrences": 782,
    "affected_public_source_repository_count": 58,
    "scan_errors": 0,
}

EXPECTED_PUBLIC_V2 = {
    "current_staged_source_paths_scanned": 41525,
    "current_staged_regular_paths_scanned": 41519,
    "current_staged_symlink_paths_scanned": 6,
    "current_staged_top_level_archive_containers_scanned": 91,
    "current_staged_nested_archive_containers_scanned": 2,
    "current_staged_archive_members_scanned": 2581,
    "current_staged_maximum_archive_depth": 2,
    "prior_withheld_target_paths": 703,
    "newly_detected_staged_target_paths": 13,
    "quarantined_target_paths": 716,
    "quarantined_regular_paths": 716,
    "quarantined_symlink_paths": 0,
    "quarantined_archive_paths": 9,
    "quarantined_target_bytes": 244661926,
    "path_match_paths": 508,
    "path_identifier_occurrences": 510,
    "content_match_paths": 207,
    "content_identifier_occurrences": 803,
    "archive_member_matches": 14,
    "archive_member_path_matches": 6,
    "archive_member_content_matches": 8,
    "archive_member_identifier_occurrences": 23,
    "archive_member_match_archives": 6,
    "git_suffix_match_paths": 13,
    "git_suffix_identifier_occurrences": 21,
    "matched_private_repository_identifier_count": 138,
    "private_repository_inventory_count": 142,
    "affected_public_source_repository_count": 58,
    "scan_errors": 0,
}


def load_jsonl(relative):
    return [
        json.loads(line)
        for line in (ROOT / relative).read_text(encoding="utf-8").splitlines()
        if line
    ]


def nfc(value):
    return unicodedata.normalize("NFC", value)


def identifier_patterns(sensitive):
    patterns = []
    for row in sensitive["matched_private_repository_identifiers"]:
        for value in (row["name_with_owner"], row["name"]):
            patterns.append(
                re.compile(
                    r"(?<![A-Za-z0-9_.-])"
                    + re.escape(str(value))
                    + r"(?=(?:\.git)?(?:[^A-Za-z0-9_.-]|$))",
                    re.IGNORECASE,
                )
            )
    return patterns


def contains_identifier(value, patterns):
    return any(pattern.search(value) for pattern in patterns)


def safe_withheld_record(prefix, number, disposition):
    return {
        "record_kind": "withheld-source-entry",
        "withheld_ordinal": "{}-{:06d}".format(prefix, number),
        "destination": None,
        "disposition": disposition,
    }


def remove_materialized(entries, mapping_by_destination):
    withheld_mappings = []
    for entry in entries:
        target = nfc(str(entry["target_path"]))
        if target not in mapping_by_destination:
            raise RuntimeError("session quarantine entry is not in the public file ledger")
        mapping = mapping_by_destination[target]
        path = ROOT / str(mapping["destination"])
        if not os.path.lexists(str(path)):
            raise RuntimeError("quarantine target is not materialized")
        mode = str(mapping["source_mode"])
        data = assimilation.file_bytes(path, mode)
        if len(data) != int(entry["bytes"]):
            raise RuntimeError("quarantine target byte count differs")
        if assimilation.git_blob_id(data) != mapping["source_blob"]:
            raise RuntimeError("quarantine target blob differs")
        if path.is_dir() and not path.is_symlink():
            raise RuntimeError("quarantine target unexpectedly names a directory")
        path.unlink()
        withheld_mappings.append(mapping)
    return withheld_mappings


def sanitize_file_ledger(mappings, withheld_mappings):
    withheld_destinations = {
        nfc(str(row["destination"])) for row in withheld_mappings
    }
    retained = [
        row
        for row in mappings
        if not row.get("destination")
        or nfc(str(row["destination"])) not in withheld_destinations
    ]
    opaque = [
        safe_withheld_record("withheld", number, "withheld-private-boundary")
        for number in range(1, len(withheld_mappings) + 1)
    ]
    return assimilation.jsonl_bytes(retained + opaque)


def sanitize_file_ledger_incremental(mappings, newly_withheld):
    withheld_destinations = {
        nfc(str(row["destination"])) for row in newly_withheld
    }
    existing_opaque = [
        row
        for row in mappings
        if row.get("record_kind") == "withheld-source-entry"
    ]
    retained = [
        row
        for row in mappings
        if row.get("record_kind") != "withheld-source-entry"
        and (
            not row.get("destination")
            or nfc(str(row["destination"])) not in withheld_destinations
        )
    ]
    start = len(existing_opaque) + 1
    opaque = existing_opaque + [
        safe_withheld_record(
            "withheld",
            number,
            "withheld-private-boundary",
        )
        for number in range(start, start + len(newly_withheld))
    ]
    return assimilation.jsonl_bytes(retained + opaque)


def sanitize_archives(withheld_mappings, public):
    archive_keys = {
        (
            str(row["source_repository"]),
            str(row["source_ref"]),
            str(row["source_path"]),
        )
        for row in withheld_mappings
        if row.get("destination")
    }
    containers = load_jsonl("provenance/archive-containers.jsonl")
    withheld_container_ids = {
        row["container_id"]
        for row in containers
        if (
            str(row["repository"]),
            str(row["source_ref"]),
            str(row["source_path"]),
        )
        in archive_keys
    }
    retained_containers = [
        row for row in containers if row["container_id"] not in withheld_container_ids
    ]
    retained_members = [
        row
        for row in load_jsonl("provenance/archive-members.jsonl")
        if row["container_id"] not in withheld_container_ids
    ]
    container_bytes = assimilation.jsonl_bytes(retained_containers)
    member_bytes = assimilation.jsonl_bytes(retained_members)
    proof = {
        "schema": "rapp-god-archive-proof/3",
        "session_evidence": {
            "verified": True,
            "copied": False,
            "sensitive_identifiers_published": False,
        },
        "pre_quarantine_scan": {
            "top_level_containers": public["top_level_archive_containers_scanned"],
            "nested_containers": public["nested_archive_containers_scanned"],
            "members": public["archive_members_scanned"],
            "maximum_depth": public["maximum_archive_depth"],
            "errors": public["scan_errors"],
        },
        "withheld": {
            "archive_paths": public["quarantined_archive_paths"],
            "archive_member_matches": public["archive_member_matches"],
            "member_path_matches": public["archive_member_path_matches"],
            "member_content_matches": public["archive_member_content_matches"],
        },
        "retained": {
            "containers": len(retained_containers),
            "members": len(retained_members),
            "container_index": "provenance/archive-containers.jsonl",
            "container_index_sha256": hashlib.sha256(container_bytes).hexdigest(),
            "member_index": "provenance/archive-members.jsonl",
            "member_index_sha256": hashlib.sha256(member_bytes).hexdigest(),
            "uncompressed_bytes": sum(
                int(row["uncompressed_bytes"]) for row in retained_members
            ),
            "dangerous_paths": sum(
                bool(row["dangerous_path"]) for row in retained_members
            ),
            "dangerous_link_targets": sum(
                bool(row["dangerous_link_target"]) for row in retained_members
            ),
            "encrypted_members": sum(
                bool(row["encrypted"]) for row in retained_members
            ),
            "secret_hits": sum(
                bool(row["secret_patterns"]) for row in retained_members
            ),
            "incomplete_scans": sum(
                not bool(row["scan_complete"]) for row in retained_containers
            ),
        },
        "disposition": "retained-index-plus-opaque-withholding",
    }
    return container_bytes, member_bytes, assimilation.json_bytes(proof)


def sanitize_commits(affected_sources):
    rows = load_jsonl("provenance/commit-objects.jsonl")
    retained = [
        row for row in rows if row.get("repository") not in affected_sources
    ]
    withheld_count = len(rows) - len(retained)
    opaque = [
        {
            "record_kind": "withheld-commit-object",
            "withheld_ordinal": "withheld-commit-{:03d}".format(number),
            "disposition": "withheld-private-boundary",
        }
        for number in range(1, withheld_count + 1)
    ]
    return assimilation.jsonl_bytes(retained + opaque), len(retained), withheld_count


def sanitize_refs(patterns):
    rows = load_jsonl("provenance/refs.jsonl")
    retained = []
    withheld = 0
    for row in rows:
        candidate = "\n".join(
            str(row.get(key) or "")
            for key in ("original_ref", "symbolic_target")
        )
        if contains_identifier(candidate, patterns):
            withheld += 1
        else:
            retained.append(row)
    retained.extend(
        {
            "record_kind": "withheld-ref",
            "withheld_ordinal": "withheld-ref-{:04d}".format(number),
            "disposition": "withheld-private-boundary",
        }
        for number in range(1, withheld + 1)
    )
    ref_bytes = assimilation.jsonl_bytes(retained)
    tag_rows = load_jsonl("provenance/tag-targets.jsonl")
    safe_tags = []
    withheld_tags = 0
    for row in tag_rows:
        if contains_identifier(str(row.get("tag_ref") or ""), patterns):
            withheld_tags += 1
        else:
            safe_tags.append(row)
    safe_tags.extend(
        {
            "record_kind": "withheld-tag-target",
            "withheld_ordinal": "withheld-tag-{:03d}".format(number),
            "disposition": "withheld-private-boundary",
        }
        for number in range(1, withheld_tags + 1)
    )
    tag_bytes = assimilation.jsonl_bytes(safe_tags)
    proof = json.loads((ROOT / "provenance/refs-releases-proof.json").read_text())
    proof["schema"] = "rapp-god-refs-releases-proof/3"
    proof["independent_evidence"]["refs"] = {
        "session_evidence_verified": True,
        "copied": False,
    }
    proof["refs"]["retained_records"] = len(rows) - withheld
    proof["refs"]["withheld_records"] = withheld
    proof["refs"]["index_sha256"] = hashlib.sha256(ref_bytes).hexdigest()
    proof["tag_targets"]["retained_records"] = len(tag_rows) - withheld_tags
    proof["tag_targets"]["withheld_records"] = withheld_tags
    proof["tag_targets"]["index_sha256"] = hashlib.sha256(tag_bytes).hexdigest()
    return ref_bytes, tag_bytes, assimilation.json_bytes(proof), withheld


def sanitize_refs_incremental(patterns):
    rows = load_jsonl("provenance/refs.jsonl")
    existing_opaque = [
        row for row in rows if row.get("record_kind") == "withheld-ref"
    ]
    retained = []
    newly_withheld = 0
    for row in rows:
        if row.get("record_kind") == "withheld-ref":
            continue
        candidate = "\n".join(
            str(row.get(key) or "")
            for key in ("original_ref", "symbolic_target")
        )
        if contains_identifier(candidate, patterns):
            newly_withheld += 1
        else:
            retained.append(row)
    total_withheld = len(existing_opaque) + newly_withheld
    retained.extend(existing_opaque)
    retained.extend(
        {
            "record_kind": "withheld-ref",
            "withheld_ordinal": "withheld-ref-{:04d}".format(number),
            "disposition": "withheld-private-boundary",
        }
        for number in range(len(existing_opaque) + 1, total_withheld + 1)
    )
    ref_bytes = assimilation.jsonl_bytes(retained)

    tag_rows = load_jsonl("provenance/tag-targets.jsonl")
    existing_tag_opaque = [
        row for row in tag_rows if row.get("record_kind") == "withheld-tag-target"
    ]
    safe_tags = []
    new_tag_withheld = 0
    for row in tag_rows:
        if row.get("record_kind") == "withheld-tag-target":
            continue
        if contains_identifier(str(row.get("tag_ref") or ""), patterns):
            new_tag_withheld += 1
        else:
            safe_tags.append(row)
    total_tag_withheld = len(existing_tag_opaque) + new_tag_withheld
    safe_tags.extend(existing_tag_opaque)
    safe_tags.extend(
        {
            "record_kind": "withheld-tag-target",
            "withheld_ordinal": "withheld-tag-{:03d}".format(number),
            "disposition": "withheld-private-boundary",
        }
        for number in range(
            len(existing_tag_opaque) + 1, total_tag_withheld + 1
        )
    )
    tag_bytes = assimilation.jsonl_bytes(safe_tags)
    proof = json.loads((ROOT / "provenance/refs-releases-proof.json").read_text())
    proof["schema"] = "rapp-god-refs-releases-proof/4"
    proof["identifier_boundary"] = {
        "git_suffix_is_delimiter": True,
        "deny_set_published": False,
    }
    proof["refs"]["retained_records"] = len(rows) - total_withheld
    proof["refs"]["withheld_records"] = total_withheld
    proof["refs"]["index_sha256"] = hashlib.sha256(ref_bytes).hexdigest()
    proof["tag_targets"]["retained_records"] = len(tag_rows) - total_tag_withheld
    proof["tag_targets"]["withheld_records"] = total_tag_withheld
    proof["tag_targets"]["index_sha256"] = hashlib.sha256(tag_bytes).hexdigest()
    return (
        ref_bytes,
        tag_bytes,
        assimilation.json_bytes(proof),
        total_withheld,
    )


def scrub_lock_license_paths():
    lock = json.loads((ROOT / "provenance/sources.lock.json").read_text())
    for source in lock["sources"]:
        license_record = source["license"]
        source["license"] = {
            "status": license_record["status"],
            "note": license_record["note"],
            "scoped_inventory": "provenance/licenses.jsonl",
        }
    return lock


def public_summary(public, retained_commits, withheld_commits, withheld_refs):
    approved = {
        key: public[key]
        for key in sorted(EXPECTED_PUBLIC)
    }
    approved.update(
        {
            "schema": "rapp-god-private-boundary-quarantine/1",
            "disposition": "opaque-withholding-applied",
            "session_evidence_copied": False,
            "sensitive_identifiers_paths_hashes_published": False,
            "withheld_commit_objects": withheld_commits,
            "retained_commit_objects": retained_commits,
            "withheld_ref_records": withheld_refs,
        }
    )
    return assimilation.json_bytes(approved)


def public_summary_v2(public, withheld_refs):
    approved = {key: public[key] for key in sorted(EXPECTED_PUBLIC_V2)}
    approved.update(
        {
            "schema": "rapp-god-private-boundary-quarantine/2",
            "disposition": "incremental-opaque-withholding-applied",
            "session_evidence_copied": False,
            "sensitive_identifiers_paths_hashes_published": False,
            "retained_commit_objects": 140,
            "withheld_commit_objects": 58,
            "withheld_ref_records": withheld_refs,
            "git_suffix_is_identifier_delimiter": True,
        }
    )
    return assimilation.json_bytes(approved)


def apply(artifact_path: Path, expected_sha256: str):
    raw = artifact_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise RuntimeError("session quarantine evidence digest differs")
    document = json.loads(raw)
    public = document["public_safe_aggregate"]
    for key, expected in EXPECTED_PUBLIC.items():
        if public.get(key) != expected:
            raise RuntimeError("session quarantine public aggregate differs")
    sensitive = document["session_only_sensitive"]
    entries = sensitive["quarantine_entries"]
    if len(entries) != public["quarantined_target_paths"]:
        raise RuntimeError("session quarantine entry count differs")
    mappings = load_jsonl("provenance/files.jsonl")
    mapping_by_destination = {
        nfc(str(row["destination"])): row
        for row in mappings
        if row.get("destination")
    }
    withheld_mappings = remove_materialized(entries, mapping_by_destination)
    affected_sources = {
        (
            str(row["public_source_repository"])
            if "/" in str(row["public_source_repository"])
            else "kody-w/" + str(row["public_source_repository"])
        )
        for row in sensitive["aggregate_by_public_source_repository"]
    }
    if len(affected_sources) != public["affected_public_source_repository_count"]:
        raise RuntimeError("affected public source aggregate differs")
    commit_bytes, retained_commits, withheld_commits = sanitize_commits(
        affected_sources
    )
    patterns = identifier_patterns(sensitive)
    ref_bytes, tag_bytes, ref_proof, withheld_refs = sanitize_refs(patterns)
    container_bytes, member_bytes, archive_proof = sanitize_archives(
        withheld_mappings, public
    )
    lock = scrub_lock_license_paths()
    file_bytes = sanitize_file_ledger(mappings, withheld_mappings)
    lock_bytes = assimilation.json_bytes(lock)
    census = json.loads((ROOT / "provenance/census-proof.json").read_text())
    census["commit_object_records"] = {
        "retained": retained_commits,
        "withheld": withheld_commits,
    }
    census["bindings"]["sources_lock_sha256"] = hashlib.sha256(lock_bytes).hexdigest()
    census["bindings"]["commit_objects_sha256"] = hashlib.sha256(commit_bytes).hexdigest()
    census["private_boundary"] = {
        "status": "opaque-withholding-applied",
        "paths": public["quarantined_target_paths"],
        "bytes": public["quarantined_target_bytes"],
        "session_evidence_copied": False,
    }
    privacy = json.loads((ROOT / "provenance/privacy-status.json").read_text())
    privacy["pending_import_quarantine"] = {
        "status": "applied",
        "withheld_paths": public["quarantined_target_paths"],
        "withheld_bytes": public["quarantined_target_bytes"],
        "opaque_ordinals": True,
        "session_evidence_copied": False,
        "public_deny_set": False,
    }
    generated = {
        "provenance/files.jsonl": file_bytes,
        "provenance/commit-objects.jsonl": commit_bytes,
        "provenance/sources.lock.json": lock_bytes,
        "provenance/census-proof.json": assimilation.json_bytes(census),
        "provenance/archive-containers.jsonl": container_bytes,
        "provenance/archive-members.jsonl": member_bytes,
        "provenance/archive-audit-proof.json": archive_proof,
        "provenance/refs.jsonl": ref_bytes,
        "provenance/tag-targets.jsonl": tag_bytes,
        "provenance/refs-releases-proof.json": ref_proof,
        "provenance/quarantine-summary.json": public_summary(
            public, retained_commits, withheld_commits, withheld_refs
        ),
        "provenance/privacy-status.json": assimilation.json_bytes(privacy),
    }
    for path, data in generated.items():
        assimilation.write_generated(path, data)
    for relative in (
        "provenance/archive-audit.source.json",
        "provenance/archive-audit-pass1.source.json",
        "provenance/refs.source.tsv",
        "provenance/secret-scan.json",
    ):
        path = ROOT / relative
        if path.exists():
            path.unlink()
    print(
        "Applied opaque withholding to {} paths ({} bytes); sensitive evidence was not copied.".format(
            public["quarantined_target_paths"],
            public["quarantined_target_bytes"],
        )
    )


def apply_v2(artifact_path: Path, expected_sha256: str):
    raw = artifact_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise RuntimeError("session quarantine evidence digest differs")
    document = json.loads(raw)
    public = document["public_safe_aggregate"]
    for key, expected in EXPECTED_PUBLIC_V2.items():
        if public.get(key) != expected:
            raise RuntimeError("session quarantine v2 public aggregate differs")
    sensitive = document["session_only_sensitive"]
    entries = sensitive["quarantine_entries"]
    carried = [
        row
        for row in entries
        if row["withholding_scope"] == "carried-forward-prior-withholding"
    ]
    newly_detected = [
        row
        for row in entries
        if row["withholding_scope"] == "newly-detected-current-staged-scope"
    ]
    if len(carried) != 703 or len(newly_detected) != 13:
        raise RuntimeError("session quarantine v2 scope counts differ")
    if any(os.path.lexists(str(ROOT / str(row["target_path"]))) for row in carried):
        raise RuntimeError("prior opaque withholding regressed")
    mappings = load_jsonl("provenance/files.jsonl")
    if sum(
        row.get("record_kind") == "withheld-source-entry" for row in mappings
    ) != 703:
        raise RuntimeError("prior opaque file ledger count differs")
    mapping_by_destination = {
        nfc(str(row["destination"])): row
        for row in mappings
        if row.get("destination")
    }
    newly_withheld_mappings = remove_materialized(
        newly_detected, mapping_by_destination
    )
    file_bytes = sanitize_file_ledger_incremental(
        mappings, newly_withheld_mappings
    )
    patterns = identifier_patterns(sensitive)
    ref_bytes, tag_bytes, ref_proof, withheld_refs = sanitize_refs_incremental(
        patterns
    )
    archive_proof = json.loads(
        (ROOT / "provenance/archive-audit-proof.json").read_text()
    )
    archive_proof["schema"] = "rapp-god-archive-proof/4"
    archive_proof["private_boundary_v2"] = {
        "current_staged_top_level_containers": public[
            "current_staged_top_level_archive_containers_scanned"
        ],
        "current_staged_nested_containers": public[
            "current_staged_nested_archive_containers_scanned"
        ],
        "current_staged_members": public["current_staged_archive_members_scanned"],
        "prior_withheld_paths": public["prior_withheld_target_paths"],
        "additional_withheld_paths": public["newly_detected_staged_target_paths"],
        "total_withheld_paths": public["quarantined_target_paths"],
        "session_evidence_copied": False,
        "git_suffix_is_identifier_delimiter": True,
    }
    commit_rows = load_jsonl("provenance/commit-objects.jsonl")
    if sum(row.get("record_kind") == "withheld-commit-object" for row in commit_rows) != 58:
        raise RuntimeError("withheld commit proof count differs")
    census = json.loads((ROOT / "provenance/census-proof.json").read_text())
    census["private_boundary"] = {
        "status": "incremental-opaque-withholding-applied",
        "paths": public["quarantined_target_paths"],
        "bytes": public["quarantined_target_bytes"],
        "prior_paths": public["prior_withheld_target_paths"],
        "additional_paths": public["newly_detected_staged_target_paths"],
        "git_suffix_is_identifier_delimiter": True,
        "session_evidence_copied": False,
    }
    privacy = json.loads((ROOT / "provenance/privacy-status.json").read_text())
    privacy["pending_import_quarantine"] = {
        "status": "applied-v2",
        "withheld_paths": public["quarantined_target_paths"],
        "withheld_bytes": public["quarantined_target_bytes"],
        "prior_withheld_paths": public["prior_withheld_target_paths"],
        "additional_withheld_paths": public["newly_detected_staged_target_paths"],
        "git_suffix_is_identifier_delimiter": True,
        "opaque_ordinals": True,
        "session_evidence_copied": False,
        "public_deny_set": False,
    }
    generated = {
        "provenance/files.jsonl": file_bytes,
        "provenance/refs.jsonl": ref_bytes,
        "provenance/tag-targets.jsonl": tag_bytes,
        "provenance/refs-releases-proof.json": ref_proof,
        "provenance/archive-audit-proof.json": assimilation.json_bytes(
            archive_proof
        ),
        "provenance/census-proof.json": assimilation.json_bytes(census),
        "provenance/quarantine-summary.json": public_summary_v2(
            public, withheld_refs
        ),
        "provenance/privacy-status.json": assimilation.json_bytes(privacy),
    }
    for path, data in generated.items():
        assimilation.write_generated(path, data)
    print(
        "Applied incremental opaque withholding to {} additional paths; sensitive evidence was not copied.".format(
            public["newly_detected_staged_target_paths"]
        )
    )


def check_applied(artifact_path: Path, expected_sha256: str):
    raw = artifact_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise RuntimeError("session quarantine evidence digest differs")
    document = json.loads(raw)
    public = document["public_safe_aggregate"]
    for key, expected in EXPECTED_PUBLIC.items():
        if public.get(key) != expected:
            raise RuntimeError("session quarantine public aggregate differs")
    entries = document["session_only_sensitive"]["quarantine_entries"]
    assert all(not os.path.lexists(str(ROOT / str(row["target_path"]))) for row in entries)
    ledger = load_jsonl("provenance/files.jsonl")
    withheld = [
        row for row in ledger if row.get("disposition") == "withheld-private-boundary"
    ]
    assert len(withheld) == public["quarantined_target_paths"]
    assert all(
        set(row) == {
            "record_kind",
            "withheld_ordinal",
            "destination",
            "disposition",
        }
        for row in withheld
    )
    summary = json.loads((ROOT / "provenance/quarantine-summary.json").read_text())
    assert summary["session_evidence_copied"] is False
    assert summary["sensitive_identifiers_paths_hashes_published"] is False
    print("Opaque private-boundary withholding is complete.")


def check_applied_v2(artifact_path: Path, expected_sha256: str):
    raw = artifact_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise RuntimeError("session quarantine evidence digest differs")
    document = json.loads(raw)
    public = document["public_safe_aggregate"]
    for key, expected in EXPECTED_PUBLIC_V2.items():
        if public.get(key) != expected:
            raise RuntimeError("session quarantine v2 public aggregate differs")
    entries = document["session_only_sensitive"]["quarantine_entries"]
    assert all(
        not os.path.lexists(str(ROOT / str(row["target_path"]))) for row in entries
    )
    ledger = load_jsonl("provenance/files.jsonl")
    withheld = [
        row for row in ledger if row.get("record_kind") == "withheld-source-entry"
    ]
    assert len(withheld) == 716
    assert all(
        set(row)
        == {
            "record_kind",
            "withheld_ordinal",
            "destination",
            "disposition",
        }
        for row in withheld
    )
    summary = json.loads((ROOT / "provenance/quarantine-summary.json").read_text())
    assert summary["schema"] == "rapp-god-private-boundary-quarantine/2"
    assert summary["session_evidence_copied"] is False
    assert summary["sensitive_identifiers_paths_hashes_published"] is False
    assert summary["git_suffix_is_identifier_delimiter"] is True
    print("Incremental opaque private-boundary withholding is complete.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{64}", args.expected_sha256):
        parser.error("--expected-sha256 must be a lowercase SHA-256")
    is_v2 = "newly_detected_staged_target_paths" in json.loads(
        args.artifact.read_bytes()
    ).get("public_safe_aggregate", {})
    if args.check and is_v2:
        check_applied_v2(args.artifact.resolve(), args.expected_sha256)
    elif args.check:
        check_applied(args.artifact.resolve(), args.expected_sha256)
    elif is_v2:
        apply_v2(args.artifact.resolve(), args.expected_sha256)
    else:
        apply(args.artifact.resolve(), args.expected_sha256)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
