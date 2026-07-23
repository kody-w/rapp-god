#!/usr/bin/env python3
"""Normalize remote refs and release metadata without creating refs or fetching assets."""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Dict, List, Sequence, Tuple


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools import assimilation  # noqa: E402


ROOT = assimilation.ROOT
DEFAULT_EVIDENCE_DIR = ROOT / ".rapp-god-input/provenance-results"
REF_SOURCE_COPY = "provenance/refs.source.tsv"
RELEASE_SOURCE_COPY = "provenance/releases.source.jsonl"
REF_INDEX = "provenance/refs.jsonl"
RELEASE_INDEX = "provenance/releases.jsonl"
ASSET_INDEX = "provenance/release-assets.jsonl"
TAG_TARGET_INDEX = "provenance/tag-targets.jsonl"
SNAPSHOT_MANIFEST = "provenance/ref-snapshot-manifest.json"
PROOF = "provenance/refs-releases-proof.json"
REF_SUMMARY_INDEX = "catalog/indexes/ref-summary.jsonl"
RELEASE_CATALOG_INDEX = "catalog/indexes/releases.jsonl"
EXTERNAL_ASSET_LIMIT = 100_000_000


def read_jsonl(path: Path) -> List[Dict[str, object]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def selected_repositories() -> set:
    lock = json.loads((ROOT / "provenance/sources.lock.json").read_text(encoding="utf-8"))
    return {str(row["repository"]).split("/", 1)[1] for row in lock["sources"]}


def ref_kind(ref: str, value: str) -> Tuple[str, bool]:
    if ref.startswith("refs/heads/"):
        return "remote-head", False
    if ref.startswith("refs/tags/"):
        return ("peeled-tag", True) if ref.endswith("^{}") else ("tag", False)
    if ref.startswith("refs/pull/"):
        return "pull-ref", False
    if ref == "HEAD" and value.startswith("ref: "):
        return "symbolic-head", False
    if ref == "HEAD":
        return "head-target", False
    return "other", False


def metadata_key(repository: str, ref: str, kind: str) -> str:
    prefix = "refs/provenance/kody-w/{}/".format(repository)
    if kind == "remote-head":
        return prefix + "heads/" + ref[len("refs/heads/") :]
    if kind in {"tag", "peeled-tag"}:
        tag = ref[len("refs/tags/") :]
        if tag.endswith("^{}"):
            tag = tag[:-3]
        return prefix + "tags/" + tag + ("/peeled" if kind == "peeled-tag" else "")
    if kind == "pull-ref":
        return prefix + ref[len("refs/") :]
    if kind == "symbolic-head":
        return prefix + "HEAD/symbolic"
    if kind == "head-target":
        return prefix + "HEAD/object"
    return prefix + "other/" + ref.replace("/", "_")


def normalize_refs(
    raw: bytes, selected: set, captured_at: str
) -> List[Dict[str, object]]:
    rows = []
    for number, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        fields = line.split("\t")
        if len(fields) != 3:
            raise RuntimeError("refs.tsv:{} does not have three columns".format(number))
        repository, value, ref = fields
        if repository not in selected:
            raise RuntimeError("ref evidence contains unselected repository: " + repository)
        kind, peeled = ref_kind(ref, value)
        symbolic_target = value[5:] if value.startswith("ref: ") else None
        object_id = None if symbolic_target else value
        if object_id is not None and not re.fullmatch(r"[0-9a-f]{40}", object_id):
            raise RuntimeError("invalid ref object at line {}".format(number))
        rows.append(
            {
                "repository": "kody-w/" + repository,
                "object": object_id,
                "symbolic_target": symbolic_target,
                "original_ref": ref,
                "kind": kind,
                "peeled": peeled,
                "namespaced_metadata_key": metadata_key(repository, ref, kind),
                "disposition": "indexed-ref-not-created",
                "captured_at": captured_at,
            }
        )
    return sorted(
        rows,
        key=lambda row: (
            str(row["repository"]),
            str(row["original_ref"]),
            str(row["kind"]),
            str(row["object"] or row["symbolic_target"]),
        ),
    )


def normalize_releases(
    source: Sequence[Dict[str, object]],
    selected: set,
    mappings: Sequence[Dict[str, object]],
    captured_at: str,
) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    releases = []
    assets = []
    destinations_by_digest = defaultdict(list)
    for mapping in mappings:
        if (
            not mapping.get("authority_alias")
            and mapping.get("destination")
            and mapping.get("sha256")
        ):
            destinations_by_digest[str(mapping["sha256"])].append(
                str(mapping["destination"])
            )
    required_release = {
        "repo",
        "id",
        "tag_name",
        "target_commitish",
        "name",
        "draft",
        "prerelease",
        "created_at",
        "published_at",
        "assets",
    }
    required_asset = {
        "id",
        "name",
        "content_type",
        "state",
        "size",
        "digest",
        "browser_download_url",
    }
    for source_release in source:
        if set(source_release) != required_release:
            raise RuntimeError(
                "release metadata shape differs for {}".format(source_release.get("repo"))
            )
        repository = str(source_release["repo"])
        if repository not in selected:
            raise RuntimeError("release evidence contains unselected repository: " + repository)
        normalized_assets = []
        for source_asset in source_release["assets"]:
            if set(source_asset) != required_asset:
                raise RuntimeError(
                    "release asset metadata shape differs for {}:{}".format(
                        repository, source_asset.get("name")
                    )
                )
            digest = str(source_asset["digest"])
            url = str(source_asset["browser_download_url"])
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
                raise RuntimeError("release asset lacks a SHA-256 digest")
            if not url.startswith("https://github.com/"):
                raise RuntimeError("release asset URL is not an HTTPS GitHub URL")
            asset = {
                **source_asset,
                "repository": "kody-w/" + repository,
                "release_id": source_release["id"],
                "release_tag": source_release["tag_name"],
                "disposition": "external-release-asset",
                "stored_as_git_blob": False,
                "fetched_as_release_asset": False,
                "digest_source": "github-api-reported",
                "digest_independently_download_verified": False,
                "imported_digest_matches": sorted(
                    destinations_by_digest.get(digest.split(":", 1)[1], [])
                ),
                "captured_at": captured_at,
            }
            normalized_assets.append(asset)
            assets.append(asset)
        release = {
            key: value for key, value in source_release.items() if key not in {"repo", "assets"}
        }
        release.update(
            {
                "repository": "kody-w/" + repository,
                "assets": sorted(normalized_assets, key=lambda row: int(row["id"])),
                "asset_count": len(normalized_assets),
                "asset_bytes": sum(int(row["size"]) for row in normalized_assets),
                "disposition": "release-metadata-only",
                "captured_at": captured_at,
                "metadata_scope": "fields-supplied-by-independent-api-evidence",
            }
        )
        releases.append(release)
    releases.sort(
        key=lambda row: (
            str(row["repository"]),
            str(row["published_at"] or ""),
            int(row["id"]),
        )
    )
    assets.sort(
        key=lambda row: (
            str(row["repository"]),
            int(row["release_id"]),
            int(row["id"]),
        )
    )
    return releases, assets


def ref_counts(rows: Sequence[Dict[str, object]]) -> Counter:
    return Counter(str(row["kind"]) for row in rows)


def generate(
    evidence_dir: Path,
    captured_at: str,
    check: bool = False,
    refs_path: Path = None,
    releases_path: Path = None,
) -> None:
    refs_path = refs_path or evidence_dir / "refs.tsv"
    releases_path = releases_path or evidence_dir / "releases.jsonl"
    refs_raw = refs_path.read_bytes()
    releases_raw = releases_path.read_bytes()
    selected = selected_repositories()
    refs = normalize_refs(refs_raw, selected, captured_at)
    mappings = [
        json.loads(line)
        for line in (ROOT / "provenance/files.jsonl").read_text().splitlines()
        if line
    ]
    release_source = [
        json.loads(line) for line in releases_raw.decode("utf-8").splitlines() if line
    ]
    releases, assets = normalize_releases(
        release_source, selected, mappings, captured_at
    )
    counts = ref_counts(refs)
    head_counts = Counter(
        str(row["repository"]).split("/", 1)[1]
        for row in refs
        if row["kind"] == "remote-head"
    )
    ref_bytes = assimilation.jsonl_bytes(refs)
    release_bytes = assimilation.jsonl_bytes(releases)
    asset_bytes = assimilation.jsonl_bytes(assets)
    canonical_tags = [row for row in refs if row["kind"] == "tag"]
    peeled_by_ref = {
        str(row["original_ref"])[:-3]: row
        for row in refs
        if row["kind"] == "peeled-tag"
    }
    tag_targets = [
        {
            "repository": row["repository"],
            "tag_ref": row["original_ref"],
            "tag_object": row["object"],
            "peeled_target": (
                peeled_by_ref[str(row["original_ref"])]["object"]
                if str(row["original_ref"]) in peeled_by_ref
                else row["object"]
            ),
            "annotated": str(row["original_ref"]) in peeled_by_ref,
            "captured_at": captured_at,
            "disposition": "external-oid-metadata",
        }
        for row in canonical_tags
    ]
    tag_target_bytes = assimilation.jsonl_bytes(tag_targets)
    releases_by_repo = Counter(str(row["repository"]).split("/", 1)[1] for row in releases)
    assets_by_repo = Counter(str(row["repository"]).split("/", 1)[1] for row in assets)
    asset_sizes_by_repo = defaultdict(int)
    for row in assets:
        asset_sizes_by_repo[str(row["repository"]).split("/", 1)[1]] += int(row["size"])
    summaries = []
    lock = json.loads((ROOT / "provenance/sources.lock.json").read_text())
    source_by_name = {
        str(row["repository"]).split("/", 1)[1]: row for row in lock["sources"]
    }
    for repository in sorted(selected):
        repository_rows = [
            row for row in refs if row["repository"] == "kody-w/" + repository
        ]
        repository_counts = ref_counts(repository_rows)
        summaries.append(
            {
                "repository": "kody-w/" + repository,
                "remote_heads": repository_counts["remote-head"],
                "tags": repository_counts["tag"],
                "peeled_tags": repository_counts["peeled-tag"],
                "pull_refs": repository_counts["pull-ref"],
                "releases": releases_by_repo[repository],
                "release_assets": assets_by_repo[repository],
                "release_asset_bytes": asset_sizes_by_repo[repository],
                "disposition": "metadata-index-only",
            }
        )
    snapshot_manifest = {
        "schema": "rapp-god-ref-snapshot-manifest/1",
        "captured_at": captured_at,
        "scope": "default-tree-snapshot-plus-external-oid-inventory",
        "histories_imported": False,
        "repositories": [
            {
                "repository": "kody-w/" + repository,
                "default_tree_snapshot": {
                    "commit": source_by_name[repository]["source_commit"],
                    "tree": source_by_name[repository]["source_tree"],
                },
                "ref_query": {
                    "status": "provided-snapshot",
                    "tool": "git-ls-remote-evidence",
                    "records": sum(
                        1
                        for row in refs
                        if row["repository"] == "kody-w/" + repository
                    ),
                },
                "release_query": {
                    "status": "provided-snapshot",
                    "tool": "github-api-evidence",
                    "records": releases_by_repo[repository],
                },
            }
            for repository in sorted(selected)
        ],
    }
    release_catalog = [
        {
            "repository": row["repository"],
            "release_id": row["id"],
            "tag_name": row["tag_name"],
            "published_at": row["published_at"],
            "draft": row["draft"],
            "prerelease": row["prerelease"],
            "asset_count": row["asset_count"],
            "asset_bytes": row["asset_bytes"],
            "provenance": RELEASE_INDEX,
        }
        for row in releases
    ]
    proof = {
        "schema": "rapp-god-refs-releases-proof/2",
        "captured_at": captured_at,
        "independent_evidence": {
            "refs": {
                "path": REF_SOURCE_COPY,
                "sha256": hashlib.sha256(refs_raw).hexdigest(),
            },
            "releases": {
                "path": RELEASE_SOURCE_COPY,
                "sha256": hashlib.sha256(releases_raw).hexdigest(),
            },
        },
        "scope": {"selected_repositories": len(selected)},
        "refs": {
            "records": len(refs),
            "remote_heads": counts["remote-head"],
            "canonical_tags": counts["tag"],
            "peeled_tags": counts["peeled-tag"],
            "pull_refs": counts["pull-ref"],
            "head_targets": counts["head-target"],
            "symbolic_heads": counts["symbolic-head"],
            "index": REF_INDEX,
            "index_sha256": hashlib.sha256(ref_bytes).hexdigest(),
            "disposition": "indexed-ref-not-created",
            "scope": "external-oid-inventory-not-imported-history",
            "head_outliers": [
                {"repository": "kody-w/" + repo, "remote_heads": count}
                for repo, count in sorted(
                    head_counts.items(), key=lambda item: (-item[1], item[0])
                )[:3]
            ],
        },
        "releases": {
            "records": len(releases),
            "repositories": len({row["repository"] for row in releases}),
            "index": RELEASE_INDEX,
            "index_sha256": hashlib.sha256(release_bytes).hexdigest(),
        },
        "tag_targets": {
            "records": len(tag_targets),
            "index": TAG_TARGET_INDEX,
            "index_sha256": hashlib.sha256(tag_target_bytes).hexdigest(),
        },
        "assets": {
            "records": len(assets),
            "logical_bytes": sum(int(row["size"]) for row in assets),
            "index": ASSET_INDEX,
            "index_sha256": hashlib.sha256(asset_bytes).hexdigest(),
            "disposition": "external-release-asset",
            "stored_as_git_blobs": 0,
            "fetched_as_release_assets": 0,
            "oversized_threshold_bytes": EXTERNAL_ASSET_LIMIT,
            "oversized_records": sum(
                int(row["size"]) >= EXTERNAL_ASSET_LIMIT for row in assets
            ),
        },
        "policy": {
            "create_target_refs": False,
            "fetch_release_assets": False,
            "note": "Default trees are imported snapshots; refs are an external OID inventory, not histories. GitHub-reported asset digests are not independently download-verified.",
        },
        "generator": "tools/ref_inventory.py",
    }
    generated = {
        REF_SOURCE_COPY: refs_raw,
        RELEASE_SOURCE_COPY: releases_raw,
        REF_INDEX: ref_bytes,
        RELEASE_INDEX: release_bytes,
        ASSET_INDEX: asset_bytes,
        TAG_TARGET_INDEX: tag_target_bytes,
        SNAPSHOT_MANIFEST: assimilation.json_bytes(snapshot_manifest),
        PROOF: assimilation.json_bytes(proof),
        REF_SUMMARY_INDEX: assimilation.jsonl_bytes(summaries),
        RELEASE_CATALOG_INDEX: assimilation.jsonl_bytes(release_catalog),
    }
    if check:
        mismatches = [
            path
            for path, data in generated.items()
            if not (ROOT / path).exists() or (ROOT / path).read_bytes() != data
        ]
        if mismatches:
            raise RuntimeError("ref/release metadata differs: " + ", ".join(mismatches))
    else:
        for path, data in generated.items():
            assimilation.write_generated(path, data)
    print(
        "{} {} heads, {} tags, {} releases, and {} external assets; no refs or assets created.".format(
            "Verified" if check else "Indexed",
            counts["remote-head"], counts["tag"], len(releases), len(assets)
        )
    )


def generate_sanitized(
    refs_path: Path,
    releases_path: Path,
    collection_started_at: str,
    collection_completed_at: str,
    sensitive_artifact: Path,
    expected_artifact_sha256: str,
) -> None:
    from tools import apply_private_quarantine

    sensitive_raw = sensitive_artifact.read_bytes()
    if hashlib.sha256(sensitive_raw).hexdigest() != expected_artifact_sha256:
        raise RuntimeError("session quarantine evidence digest differs")
    sensitive_document = json.loads(sensitive_raw)
    public = sensitive_document["public_safe_aggregate"]
    for key, expected in apply_private_quarantine.EXPECTED_PUBLIC_V2.items():
        if public.get(key) != expected:
            raise RuntimeError("session quarantine v2 public aggregate differs")
    patterns = apply_private_quarantine.identifier_patterns(
        sensitive_document["session_only_sensitive"]
    )
    refs_raw = refs_path.read_bytes()
    releases_raw = releases_path.read_bytes()
    selected = selected_repositories()
    original_refs = normalize_refs(
        refs_raw, selected, collection_completed_at
    )
    mappings = [
        json.loads(line)
        for line in (ROOT / "provenance/files.jsonl").read_text().splitlines()
        if line
    ]
    release_source = [
        json.loads(line)
        for line in releases_raw.decode("utf-8").splitlines()
        if line
    ]
    releases, assets = normalize_releases(
        release_source, selected, mappings, collection_completed_at
    )
    counts = ref_counts(original_refs)
    head_counts = Counter(
        str(row["repository"]).split("/", 1)[1]
        for row in original_refs
        if row["kind"] == "remote-head"
    )
    retained_refs = []
    withheld_refs = 0
    for row in original_refs:
        candidate = "\n".join(
            str(row.get(key) or "")
            for key in ("original_ref", "symbolic_target")
        )
        if apply_private_quarantine.contains_identifier(candidate, patterns):
            withheld_refs += 1
        else:
            retained_refs.append(row)
    refs = retained_refs + [
        {
            "record_kind": "withheld-ref",
            "withheld_ordinal": "withheld-ref-{:04d}".format(number),
            "disposition": "withheld-private-boundary",
        }
        for number in range(1, withheld_refs + 1)
    ]
    canonical_tags = [row for row in original_refs if row["kind"] == "tag"]
    peeled_by_ref = {
        str(row["original_ref"])[:-3]: row
        for row in original_refs
        if row["kind"] == "peeled-tag"
    }
    safe_tags = []
    withheld_tags = 0
    for row in canonical_tags:
        if apply_private_quarantine.contains_identifier(
            str(row["original_ref"]), patterns
        ):
            withheld_tags += 1
            continue
        safe_tags.append(
            {
                "repository": row["repository"],
                "tag_ref": row["original_ref"],
                "tag_object": row["object"],
                "peeled_target": (
                    peeled_by_ref[str(row["original_ref"])]["object"]
                    if str(row["original_ref"]) in peeled_by_ref
                    else row["object"]
                ),
                "annotated": str(row["original_ref"]) in peeled_by_ref,
                "captured_at": collection_completed_at,
                "disposition": "external-oid-metadata",
            }
        )
    tag_targets = safe_tags + [
        {
            "record_kind": "withheld-tag-target",
            "withheld_ordinal": "withheld-tag-{:03d}".format(number),
            "disposition": "withheld-private-boundary",
        }
        for number in range(1, withheld_tags + 1)
    ]
    ref_bytes = assimilation.jsonl_bytes(refs)
    release_bytes = assimilation.jsonl_bytes(releases)
    asset_bytes = assimilation.jsonl_bytes(assets)
    tag_target_bytes = assimilation.jsonl_bytes(tag_targets)
    releases_by_repo = Counter(
        str(row["repository"]).split("/", 1)[1] for row in releases
    )
    assets_by_repo = Counter(
        str(row["repository"]).split("/", 1)[1] for row in assets
    )
    asset_sizes_by_repo = defaultdict(int)
    for row in assets:
        asset_sizes_by_repo[str(row["repository"]).split("/", 1)[1]] += int(
            row["size"]
        )
    lock = json.loads((ROOT / "provenance/sources.lock.json").read_text())
    source_by_name = {
        str(row["repository"]).split("/", 1)[1]: row for row in lock["sources"]
    }
    summaries = []
    for repository in sorted(selected):
        repository_rows = [
            row
            for row in original_refs
            if row["repository"] == "kody-w/" + repository
        ]
        repository_counts = ref_counts(repository_rows)
        summaries.append(
            {
                "repository": "kody-w/" + repository,
                "remote_heads": repository_counts["remote-head"],
                "tags": repository_counts["tag"],
                "peeled_tags": repository_counts["peeled-tag"],
                "pull_refs": repository_counts["pull-ref"],
                "releases": releases_by_repo[repository],
                "release_assets": assets_by_repo[repository],
                "release_asset_bytes": asset_sizes_by_repo[repository],
                "disposition": "metadata-index-only",
            }
        )
    capture_model = {
        "capture_model": "non-atomic-multi-repository-window",
        "atomic": False,
        "collection_started_at": collection_started_at,
        "collection_completed_at": collection_completed_at,
        "semantics": (
            "Ref/release observations were collected in waves, not as an "
            "atomic owner snapshot."
        ),
    }
    snapshot_manifest = {
        "schema": "rapp-god-ref-snapshot-manifest/2",
        "captured_at": collection_completed_at,
        **capture_model,
        "scope": "default-tree-snapshot-plus-external-oid-inventory",
        "histories_imported": False,
        "selected_default_tree_pins": {
            "capture_model": "non-atomic-per-repository",
            "window": lock["capture_window"],
            "may_predate_ref_observations": True,
        },
        "repositories": [
            {
                "repository": "kody-w/" + repository,
                "default_tree_snapshot": {
                    "commit": source_by_name[repository]["source_commit"],
                    "tree": source_by_name[repository]["source_tree"],
                    "captured_at": source_by_name[repository]["captured_at"],
                },
                "ref_query": {
                    "status": "provided-snapshot",
                    "tool": "git-ls-remote-evidence",
                    "records": sum(
                        1
                        for row in original_refs
                        if row["repository"] == "kody-w/" + repository
                    ),
                },
                "release_query": {
                    "status": "provided-snapshot",
                    "tool": "github-api-evidence",
                    "records": releases_by_repo[repository],
                },
            }
            for repository in sorted(selected)
        ],
    }
    release_catalog = [
        {
            "repository": row["repository"],
            "release_id": row["id"],
            "tag_name": row["tag_name"],
            "published_at": row["published_at"],
            "draft": row["draft"],
            "prerelease": row["prerelease"],
            "asset_count": row["asset_count"],
            "asset_bytes": row["asset_bytes"],
            "provenance": RELEASE_INDEX,
        }
        for row in releases
    ]
    proof = {
        "schema": "rapp-god-refs-releases-proof/5",
        "captured_at": collection_completed_at,
        **capture_model,
        "independent_evidence": {
            "refs": {
                "session_evidence_verified": True,
                "copied": False,
            },
            "releases": {
                "path": RELEASE_SOURCE_COPY,
                "sha256": hashlib.sha256(releases_raw).hexdigest(),
            },
        },
        "scope": {"selected_repositories": len(selected)},
        "default_tree_pin_semantics": {
            "capture_model": "non-atomic-per-repository",
            "may_predate_ref_observations": True,
            "atomic_owner_snapshot": False,
        },
        "identifier_boundary": {
            "git_suffix_is_delimiter": True,
            "deny_set_published": False,
        },
        "refs": {
            "records": len(original_refs),
            "retained_records": len(retained_refs),
            "withheld_records": withheld_refs,
            "remote_heads": counts["remote-head"],
            "canonical_tags": counts["tag"],
            "peeled_tags": counts["peeled-tag"],
            "pull_refs": counts["pull-ref"],
            "head_targets": counts["head-target"],
            "symbolic_heads": counts["symbolic-head"],
            "index": REF_INDEX,
            "index_sha256": hashlib.sha256(ref_bytes).hexdigest(),
            "disposition": "indexed-ref-not-created",
            "scope": "external-oid-inventory-not-imported-history",
            "head_outliers": [
                {"repository": "kody-w/" + repo, "remote_heads": count}
                for repo, count in sorted(
                    head_counts.items(), key=lambda item: (-item[1], item[0])
                )[:3]
            ],
        },
        "releases": {
            "records": len(releases),
            "repositories": len({row["repository"] for row in releases}),
            "index": RELEASE_INDEX,
            "index_sha256": hashlib.sha256(release_bytes).hexdigest(),
        },
        "tag_targets": {
            "records": len(canonical_tags),
            "retained_records": len(safe_tags),
            "withheld_records": withheld_tags,
            "index": TAG_TARGET_INDEX,
            "index_sha256": hashlib.sha256(tag_target_bytes).hexdigest(),
        },
        "assets": {
            "records": len(assets),
            "logical_bytes": sum(int(row["size"]) for row in assets),
            "index": ASSET_INDEX,
            "index_sha256": hashlib.sha256(asset_bytes).hexdigest(),
            "disposition": "external-release-asset",
            "stored_as_git_blobs": 0,
            "fetched_as_release_assets": 0,
            "oversized_threshold_bytes": EXTERNAL_ASSET_LIMIT,
            "oversized_records": sum(
                int(row["size"]) >= EXTERNAL_ASSET_LIMIT for row in assets
            ),
        },
        "policy": {
            "create_target_refs": False,
            "fetch_release_assets": False,
            "atomic_owner_snapshot": False,
            "note": (
                "Default-tree pins and later ref observations have distinct "
                "per-repository/non-atomic capture times."
            ),
        },
        "generator": "tools/ref_inventory.py",
    }
    generated = {
        RELEASE_SOURCE_COPY: releases_raw,
        REF_INDEX: ref_bytes,
        RELEASE_INDEX: release_bytes,
        ASSET_INDEX: asset_bytes,
        TAG_TARGET_INDEX: tag_target_bytes,
        SNAPSHOT_MANIFEST: assimilation.json_bytes(snapshot_manifest),
        PROOF: assimilation.json_bytes(proof),
        REF_SUMMARY_INDEX: assimilation.jsonl_bytes(summaries),
        RELEASE_CATALOG_INDEX: assimilation.jsonl_bytes(release_catalog),
    }
    for path, data in generated.items():
        assimilation.write_generated(path, data)
    raw_ref_copy = ROOT / REF_SOURCE_COPY
    if raw_ref_copy.exists():
        raw_ref_copy.unlink()
    print(
        "Indexed non-atomic ref/release window ending {} with {} opaque ref records.".format(
            collection_completed_at, withheld_refs
        )
    )


def public_release_outputs():
    proof = json.loads((ROOT / PROOF).read_text())
    captured_at = proof["captured_at"]
    selected = selected_repositories()
    mappings = [
        json.loads(line)
        for line in (ROOT / "provenance/files.jsonl").read_text().splitlines()
        if line
    ]
    source_raw = (ROOT / RELEASE_SOURCE_COPY).read_bytes()
    source = [
        json.loads(line) for line in source_raw.decode("utf-8").splitlines() if line
    ]
    releases, assets = normalize_releases(
        source, selected, mappings, captured_at
    )
    release_bytes = assimilation.jsonl_bytes(releases)
    asset_bytes = assimilation.jsonl_bytes(assets)
    proof["releases"]["index_sha256"] = hashlib.sha256(release_bytes).hexdigest()
    proof["assets"]["index_sha256"] = hashlib.sha256(asset_bytes).hexdigest()
    release_catalog = [
        {
            "repository": row["repository"],
            "release_id": row["id"],
            "tag_name": row["tag_name"],
            "published_at": row["published_at"],
            "draft": row["draft"],
            "prerelease": row["prerelease"],
            "asset_count": row["asset_count"],
            "asset_bytes": row["asset_bytes"],
            "provenance": RELEASE_INDEX,
        }
        for row in releases
    ]
    return {
        RELEASE_INDEX: release_bytes,
        ASSET_INDEX: asset_bytes,
        RELEASE_CATALOG_INDEX: assimilation.jsonl_bytes(release_catalog),
        PROOF: assimilation.json_bytes(proof),
    }


def sanitize_public_releases(check=False):
    generated = public_release_outputs()
    if check:
        mismatches = [
            path
            for path, data in generated.items()
            if not (ROOT / path).exists() or (ROOT / path).read_bytes() != data
        ]
        if mismatches:
            raise RuntimeError("public release metadata differs: " + ", ".join(mismatches))
    else:
        for path, data in generated.items():
            assimilation.write_generated(path, data)


def check_public():
    proof = json.loads((ROOT / PROOF).read_text())
    if proof.get("schema") not in {
        "rapp-god-refs-releases-proof/3",
        "rapp-god-refs-releases-proof/4",
        "rapp-god-refs-releases-proof/5",
    }:
        raise RuntimeError("unexpected sanitized ref proof schema")
    if proof.get("schema") in {
        "rapp-god-refs-releases-proof/4",
        "rapp-god-refs-releases-proof/5",
    }:
        assert proof["identifier_boundary"] == {
            "git_suffix_is_delimiter": True,
            "deny_set_published": False,
        }
    if proof.get("schema") == "rapp-god-refs-releases-proof/5":
        assert proof["capture_model"] == "non-atomic-multi-repository-window"
        assert proof["atomic"] is False
        assert proof["collection_started_at"] == "2026-07-23T05:11:01Z"
        assert proof["collection_completed_at"] == "2026-07-23T05:11:11Z"
        assert proof["captured_at"] == proof["collection_completed_at"]
        assert proof["default_tree_pin_semantics"] == {
            "capture_model": "non-atomic-per-repository",
            "may_predate_ref_observations": True,
            "atomic_owner_snapshot": False,
        }
    refs_raw = (ROOT / proof["refs"]["index"]).read_bytes()
    refs = [json.loads(line) for line in refs_raw.decode().splitlines() if line]
    assert len(refs) == proof["refs"]["records"]
    assert hashlib.sha256(refs_raw).hexdigest() == proof["refs"]["index_sha256"]
    withheld = [row for row in refs if row.get("record_kind") == "withheld-ref"]
    assert len(withheld) == proof["refs"]["withheld_records"]
    assert all(
        set(row) == {"record_kind", "withheld_ordinal", "disposition"}
        for row in withheld
    )
    tags_raw = (ROOT / proof["tag_targets"]["index"]).read_bytes()
    tags = [json.loads(line) for line in tags_raw.decode().splitlines() if line]
    assert len(tags) == proof["tag_targets"]["records"]
    assert hashlib.sha256(tags_raw).hexdigest() == proof["tag_targets"]["index_sha256"]
    sanitize_public_releases(check=True)
    actual_refs = subprocess.run(
        ["git", "-C", str(ROOT), "for-each-ref", "--format=%(refname)", "refs/provenance/"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert not actual_refs.strip()
    print("Sanitized ref/release metadata is deterministic.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--evidence-dir",
        type=Path,
        default=Path(
            os.environ.get("RAPP_GOD_REF_PROVENANCE_RESULTS", str(DEFAULT_EVIDENCE_DIR))
        ),
    )
    parser.add_argument(
        "--captured-at",
        default=os.environ.get("RAPP_GOD_CAPTURED_AT"),
        help="UTC snapshot timestamp (required; or RAPP_GOD_CAPTURED_AT)",
    )
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--sanitize-public", action="store_true")
    parser.add_argument("--check-public", action="store_true")
    parser.add_argument("--regenerate-sanitized", action="store_true")
    parser.add_argument("--sensitive-artifact", type=Path)
    parser.add_argument("--expected-artifact-sha256")
    parser.add_argument("--collection-started-at")
    parser.add_argument("--collection-completed-at")
    parser.add_argument("--refs-file", type=Path)
    parser.add_argument("--releases-file", type=Path)
    args = parser.parse_args()
    if args.regenerate_sanitized:
        required = (
            args.refs_file,
            args.releases_file,
            args.sensitive_artifact,
            args.expected_artifact_sha256,
            args.collection_started_at,
            args.collection_completed_at,
        )
        if not all(required):
            parser.error(
                "sanitized regeneration requires evidence files, sensitive artifact, digest, and collection window"
            )
        timestamp = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z"
        if not re.fullmatch(timestamp, args.collection_started_at) or not re.fullmatch(
            timestamp, args.collection_completed_at
        ):
            parser.error("collection timestamps must be UTC")
        if args.collection_started_at > args.collection_completed_at:
            parser.error("collection window is reversed")
        generate_sanitized(
            args.refs_file.resolve(),
            args.releases_file.resolve(),
            args.collection_started_at,
            args.collection_completed_at,
            args.sensitive_artifact.resolve(),
            args.expected_artifact_sha256,
        )
        return 0
    if args.sanitize_public or args.check_public:
        if args.sanitize_public:
            sanitize_public_releases()
        if args.check_public:
            check_public()
        return 0
    if not args.captured_at or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", args.captured_at
    ):
        parser.error("--captured-at must be an explicit UTC timestamp")
    if bool(args.refs_file) != bool(args.releases_file):
        parser.error("--refs-file and --releases-file must be supplied together")
    generate(
        args.evidence_dir.resolve(),
        args.captured_at,
        check=args.check,
        refs_path=args.refs_file.resolve() if args.refs_file else None,
        releases_path=args.releases_file.resolve() if args.releases_file else None,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
