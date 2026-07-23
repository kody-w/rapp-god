#!/usr/bin/env python3
"""Deterministic publication and evidence checks for rapp-estate."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
BASELINE = "24c8fdc1e770c790b98724002d719d515d5e5465"
AUTHORITY_COMMIT = "6723c7add2aed36bb68992fc71a56b0a4bd5ad81"
AUTHORITY_SHA256 = "6d06daba65d7c045716f3d6e95db8401ab58e727820e4114466d847f62cae49b"
DEPLOYMENT_STATE = "pending-review-publish-and-live-verification"
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")
PUBLIC_REPOSITORY_RE = re.compile(r"^kody-w/[A-Za-z0-9._-]+$")
EXPECTED_FILES = {
    ".nojekyll",
    ".well-known/rapp-network.json",
    "METROPOLIS.md",
    "RAPP1_AUTHORITY.json",
    "RAPP1_EVIDENCE.json",
    "RAPP1_OWNER_ACTIONS.json",
    "RAPP1_STATUS.md",
    "estate.json",
    "index.html",
    "tests/test_publication.py",
}


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise AssertionError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    assert raw.endswith(b"\n"), f"{path} must end with LF"
    assert not raw.startswith(b"\xef\xbb\xbf"), f"{path} has a BOM"
    assert b"\r\n" not in raw, f"{path} has CRLF"
    return json.loads(raw, object_pairs_hook=reject_duplicate_keys)


def baseline_json(path: str) -> dict[str, object]:
    raw = subprocess.check_output(
        ["git", "-C", str(ROOT), "show", f"{BASELINE}:{path}"]
    )
    return json.loads(raw, object_pairs_hook=reject_duplicate_keys)


def test_static_tree() -> None:
    files = {
        str(path.relative_to(ROOT))
        for path in ROOT.rglob("*")
        if path.is_file() and ".git" not in path.parts
    }
    assert files == EXPECTED_FILES
    assert not any(
        re.search(r"\.(zip|tar|tgz|gz|bz2|xz|7z|rar|egg)$", path, re.IGNORECASE)
        for path in files
    )
    for relative_path in files:
        raw = (ROOT / relative_path).read_bytes()
        if raw:
            assert raw.endswith(b"\n"), relative_path
            assert not raw.startswith(b"\xef\xbb\xbf"), relative_path
            assert b"\r\n" not in raw, relative_path

    html = (ROOT / "index.html").read_text(encoding="utf-8")
    allowed_external = {
        (
            "https://raw.githubusercontent.com/kody-w/rapp-1/"
            f"{AUTHORITY_COMMIT}/SPEC.md"
        ),
        (
            "https://github.com/kody-w/rapp-estate/tree/"
            "24c8fdc1e770c790b98724002d719d515d5e5465"
        ),
    }
    for href in re.findall(r'href="([^"]+)"', html):
        if href.startswith("https://"):
            assert href in allowed_external
        else:
            assert (ROOT / href.split("#", 1)[0]).is_file(), href

    status = (ROOT / "RAPP1_STATUS.md").read_text(encoding="utf-8")
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", status):
        if target.startswith("https://"):
            assert target in allowed_external
        else:
            assert (ROOT / target.split("#", 1)[0]).is_file(), target

    current_text = "\n".join(
        (ROOT / relative_path).read_text(encoding="utf-8")
        for relative_path in sorted(files)
    )
    home_marker = "/" + "Users" + "/"
    assert home_marker not in current_text
    assert not re.search(
        r"https://raw\.githubusercontent\.com/[^/\s]+/[^/\s]+/main/",
        current_text,
    )


def test_baseline_accounting(evidence: dict[str, object]) -> None:
    estate = baseline_json("estate.json")
    beacon = baseline_json(".well-known/rapp-network.json")
    estate_values = [estate["owner"]["rappid"]]
    estate_values.extend(entry["rappid"] for entry in estate["created"])
    emitted_values = estate_values + [beacon["operator_rappid"]]

    assert len(estate_values) == 17
    assert len(estate["created"]) == 16
    assert len(emitted_values) == 18
    assert len(set(emitted_values)) == 17
    assert beacon["operator_rappid"] == estate["owner"]["rappid"]

    accounting = evidence["occurrence_accounting"]
    assert accounting["estate_json"] == {
        "owner_rappid_occurrences": 1,
        "created_rappid_occurrences": 16,
        "subtotal": 17,
    }
    assert accounting["network_beacon"] == {
        "operator_rappid_occurrences": 1,
        "subtotal": 1,
    }
    assert accounting["total_provisional_emitted_occurrences"] == 18
    assert accounting["distinct_baseline_identifier_values"] == 17
    assert accounting["lookup_records"] == 17
    assert accounting["distinct_source_repository_paths"] == 16
    assert accounting["resolved_lookup_records"] == 16
    assert accounting["resolved_distinct_public_source_paths"] == 15
    assert accounting["unresolved_lookup_records"] == 1


def test_evidence(evidence: dict[str, object]) -> list[str]:
    assert evidence["disposition"] == "non-authoritative-observation"
    assert evidence["authoritative"] is False
    assert evidence["can_establish_identity_mint_authorization_registry_or_trust"] is False
    assert evidence["authority"]["commit"] == AUTHORITY_COMMIT
    assert evidence["authority"]["sha256"] == AUTHORITY_SHA256
    assert evidence["collection"]["moving_ref_policy"].startswith(
        "refs/heads/main was discovery-only"
    )
    observed_utc = evidence["collection"]["observed_utc"]
    assert UTC_RE.fullmatch(observed_utc)

    lookups = evidence["lookups"]
    assert len(lookups) == 17
    assert len({item["lookup_id"] for item in lookups}) == 17
    expected_occurrences = {
        "estate.json#/owner/rappid",
        ".well-known/rapp-network.json#/operator_rappid",
        *(f"estate.json#/created/{index}/rappid" for index in range(16)),
    }
    actual_occurrences = [
        occurrence
        for item in lookups
        for occurrence in item["baseline_occurrences"]
    ]
    assert len(actual_occurrences) == 18
    assert set(actual_occurrences) == expected_occurrences
    assert len(actual_occurrences) == len(set(actual_occurrences))

    resolved_urls: list[str] = []
    unresolved = 0
    resolved_repositories: set[tuple[str, str]] = set()
    for item in lookups:
        assert set(item).isdisjoint(
            {"rappid", "identity_value", "record", "record_contents"}
        )
        source = item["source"]
        observation = item["observation"]
        assessment = item["candidate_assessment"]
        assert source["path"] == "rappid.json"
        assert source["discovery_ref"] == "refs/heads/main"
        assert source["discovery_ref_role"] == "discovery-only"
        assert observation["observed_utc"] == observed_utc
        assert assessment["trust_promotion"] is False
        assert assessment["owner_authorization"] in {
            "not-established",
        }
        assert assessment["registry_acceptance"] == "not-established"

        if observation["status"] == "resolved-public":
            repository = source["repository"]
            commit = observation["resolved_commit"]
            assert PUBLIC_REPOSITORY_RE.fullmatch(repository)
            assert COMMIT_RE.fullmatch(commit)
            assert observation["http_status"] == 200
            assert isinstance(observation["bytes"], int) and observation["bytes"] > 0
            assert SHA256_RE.fullmatch(observation["sha256"])
            assert observation["freshness"] == "point-in-time-only"
            assert assessment["section_6_1_grammar"] is True
            assert assessment["mint_provenance"] == "not-established"
            expected_url = (
                f"https://raw.githubusercontent.com/{repository}/{commit}/"
                f"{source['path']}"
            )
            assert observation["pinned_url"] == expected_url
            resolved_urls.append(expected_url)
            resolved_repositories.add((repository, source["path"]))
        else:
            unresolved += 1
            assert observation["status"] == "unresolved-publicly"
            assert source["repository"] is None
            assert source["repository_disposition"] == (
                "withheld-non-public-baseline-locator"
            )
            assert observation["resolved_commit"] is None
            assert observation["pinned_url"] is None
            assert observation["http_status"] == 404
            assert observation["bytes"] is None
            assert observation["sha256"] is None
            assert observation["freshness"] == "unresolved-at-observation"
            assert assessment["section_6_1_grammar"] is None
            assert assessment["mint_provenance"] == "not-observed"

    assert len(resolved_urls) == 16
    assert len(set(resolved_urls)) == 15
    assert len(resolved_repositories) == 15
    assert unresolved == 1
    return sorted(set(resolved_urls))


def test_candidate_status(documents: dict[str, dict[str, object]]) -> None:
    estate = documents["estate.json"]
    beacon = documents[".well-known/rapp-network.json"]
    for document, acceptance_key in (
        (estate, "accepted_as_estate_manifest"),
        (beacon, "accepted_as_network_beacon"),
    ):
        assert document[acceptance_key] is False
        deployment = document["deployment"]
        assert deployment["state"] == DEPLOYMENT_STATE
        assert deployment["live_deployment_verified"] is False
        assert deployment["verified_commit"] is None
        assert deployment["verified_at"] is None
        assert "main" in deployment["quarantine_effective_only_when"]
        assert "Pages" in deployment["quarantine_effective_only_when"]
        assert all(
            value is None or value == []
            for value in document["candidate_claims"].values()
        )

    historical = estate["historical_claims"]
    assert historical["baseline_estate_identity_occurrences"] == 17
    assert historical["baseline_beacon_identity_occurrences"] == 1
    assert historical["baseline_total_provisional_emitted_occurrences"] == 18
    assert historical["distinct_baseline_identity_lookups"] == 17

    status = (ROOT / "RAPP1_STATUS.md").read_text(encoding="utf-8")
    assert "Candidate deployment status" in status
    assert "quarantine takes effect only when" in status
    assert "Live deployment verification checklist" in status
    assert status.count("- [ ]") >= 8
    assert "Parent/release coordinator" in status

    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert "Candidate quarantine — not deployed" in html
    assert "quarantine takes effect only when" in html
    for forbidden in (
        "<script",
        "onerror=",
        "onclick=",
        "innerHTML",
        "fetch(",
        "navigator.",
        'target="_blank"',
        "javascript:",
    ):
        assert forbidden not in html


def test_owner_actions(actions: dict[str, object]) -> None:
    inputs = actions["blockers"][0]["owner_inputs"]
    assert inputs
    assert all(value is None for value in inputs.values())
    assert actions["authoritative"] is False
    assert actions["can_mint_reanchor_sign_or_accept"] is False


def test_authority(pin: dict[str, object]) -> None:
    assert pin["commit"] == AUTHORITY_COMMIT
    assert pin["bytes"] == 41880
    assert pin["sha256"] == AUTHORITY_SHA256
    assert pin["authenticated_registry_acceptance"] is False


def verify_pinned_sources_online(
    evidence: dict[str, object], resolved_urls: list[str]
) -> None:
    by_url = {
        item["observation"]["pinned_url"]: item["observation"]
        for item in evidence["lookups"]
        if item["observation"]["status"] == "resolved-public"
    }
    for url in resolved_urls:
        request = urllib.request.Request(
            url, headers={"User-Agent": "rapp-estate-publication-test"}
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
            assert response.status == 200
        observation = by_url[url]
        assert len(raw) == observation["bytes"], url
        assert hashlib.sha256(raw).hexdigest() == observation["sha256"], url


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--online",
        action="store_true",
        help="Refetch immutable public evidence URLs and verify bytes.",
    )
    args = parser.parse_args()

    json_paths = sorted(
        path for path in ROOT.rglob("*.json") if ".git" not in path.parts
    )
    documents = {
        str(path.relative_to(ROOT)): load_json(path) for path in json_paths
    }
    expected_json = {
        ".well-known/rapp-network.json",
        "RAPP1_AUTHORITY.json",
        "RAPP1_EVIDENCE.json",
        "RAPP1_OWNER_ACTIONS.json",
        "estate.json",
    }
    assert set(documents) == expected_json

    evidence = documents["RAPP1_EVIDENCE.json"]
    test_static_tree()
    test_baseline_accounting(evidence)
    resolved_urls = test_evidence(evidence)
    test_candidate_status(documents)
    test_owner_actions(documents["RAPP1_OWNER_ACTIONS.json"])
    test_authority(documents["RAPP1_AUTHORITY.json"])
    if args.online:
        verify_pinned_sources_online(evidence, resolved_urls)

    mode = "offline+online" if args.online else "offline"
    print(f"PASS publication tests ({mode}): 18 occurrences, 17 lookups")
    return 0


if __name__ == "__main__":
    sys.exit(main())
