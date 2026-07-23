#!/usr/bin/env python3
"""Offline integrity checks for the assimilated public monorepo."""

import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from typing import Dict, Iterable, List, Sequence, Tuple
import unicodedata


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import assimilation  # noqa: E402


GITHUB_BLOB_LIMIT = 100_000_000


def load_json(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def load_jsonl(relative: str) -> List[Dict[str, object]]:
    rows = []
    with (ROOT / relative).open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as error:
                    raise AssertionError("{}:{}: {}".format(relative, number, error))
    return rows


def git_blob_id(data: bytes) -> str:
    header = "blob {}\0".format(len(data)).encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def checkout_attributes(relative: Path) -> Dict[str, str]:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "check-attr",
            "-z",
            "text",
            "eol",
            "working-tree-encoding",
            "filter",
            "--",
            str(relative),
        ],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout.split(b"\0")
    values = {}
    for index in range(0, len(result) - 2, 3):
        values[os.fsdecode(result[index + 1])] = os.fsdecode(result[index + 2])
    return values


def clean_checkout_blob(relative: Path, data: bytes) -> str:
    return (
        subprocess.run(
            [
                "git",
                "-C",
                str(ROOT),
                "hash-object",
                "--path={}".format(relative),
                "--stdin",
            ],
            input=data,
            check=True,
            stdout=subprocess.PIPE,
        )
        .stdout.decode("ascii")
        .strip()
    )


def git_tree_id(rows: Sequence[Dict[str, object]]) -> str:
    root: Dict[str, object] = {}
    for row in rows:
        parts = str(row["source_path"]).split("/")
        node = root
        for part in parts[:-1]:
            child = node.setdefault(part, {})
            if not isinstance(child, dict):
                raise AssertionError("file/directory collision at {}".format(row["source_path"]))
            node = child
        node[parts[-1]] = (str(row["source_mode"]), str(row["source_blob"]))

    def build(node: Dict[str, object]) -> Tuple[str, bool]:
        entries = []
        for name, value in node.items():
            if isinstance(value, dict):
                object_id, _ = build(value)
                entries.append((os.fsencode(name), "40000", object_id, True))
            else:
                mode, object_id = value
                entries.append((os.fsencode(name), mode, object_id, False))
        entries.sort(key=lambda item: item[0] + (b"/" if item[3] else b""))
        body = b"".join(
            mode.encode("ascii")
            + b" "
            + name
            + b"\0"
            + bytes.fromhex(object_id)
            for name, mode, object_id, _ in entries
        )
        header = "tree {}\0".format(len(body)).encode("ascii")
        return hashlib.sha1(header + body).hexdigest(), True

    return build(root)[0]


class IntegrityChecker:
    def __init__(self) -> None:
        self.repositories = load_jsonl("provenance/repositories.jsonl")
        self.lock = load_json("provenance/sources.lock.json")
        self.mappings = load_jsonl("provenance/files.jsonl")
        self.selected_mappings = [
            row for row in self.mappings if not bool(row.get("authority_alias"))
        ]
        self.withheld_mappings = [
            row
            for row in self.mappings
            if row.get("disposition") == "withheld-private-boundary"
        ]
        self.materialized_mappings = [
            row for row in self.mappings if row.get("destination")
        ]
        self.grail_mappings = [
            row for row in self.mappings if bool(row.get("authority_alias"))
        ]

    def check_decisions(self) -> Dict[str, int]:
        assert len(self.repositories) == assimilation.PUBLIC_COUNT
        names = [str(row["repository"]) for row in self.repositories]
        assert len(names) == len(set(names))
        assert all(row["visibility"] == "public" for row in self.repositories)
        decisions: Dict[str, int] = {}
        for row in self.repositories:
            decision = str(row["decision"])
            decisions[decision] = decisions.get(decision, 0) + 1
        assert decisions == {
            "empty": 5,
            "excluded": 166,
            "false-positive": 1,
            "included": 197,
            "native-evolved": 1,
        }
        power_apps = next(
            row for row in self.repositories if row["repository"] == "kody-w/PowerApps"
        )
        assert power_apps["decision"] == "false-positive"
        assert "substring/fork" in str(power_apps["reason"])
        assert self.lock["selected_count"] == assimilation.SELECTED_COUNT
        assert self.lock["external_import_count"] == assimilation.EXTERNAL_SELECTED_COUNT
        assert len(self.lock["sources"]) == assimilation.SELECTED_COUNT
        assert sum(
            1 for source in self.lock["sources"] if source["disposition"] == "native-evolved"
        ) == 1
        return decisions

    def check_private_quarantine(self) -> None:
        summary = load_json("provenance/private-summary.json")
        assert set(summary) == {
            "schema",
            "count",
            "disposition",
            "reason",
            "existing_public_history",
        }
        assert summary["count"] == assimilation.PRIVATE_QUARANTINE_COUNT
        assert summary["disposition"] == "quarantined-not-imported"
        encoded = json.dumps(summary, sort_keys=True).lower()
        assert "repositories" not in encoded
        assert "commit" not in encoded
        assert "sha" not in encoded
        assert "no private names" not in encoded
        assert summary["existing_public_history"] == (
            "unresolved-owner-remediation-no-rewrite"
        )
        privacy = load_json("provenance/privacy-status.json")
        assert privacy["existing_public_observatory_history"]["status"] == (
            "unresolved-owner-remediation"
        )
        assert privacy["existing_public_observatory_history"]["rewrite_history"] is False
        assert privacy["pending_import_quarantine"]["status"] == "applied-v2"
        assert privacy["pending_import_quarantine"]["opaque_ordinals"] is True
        assert privacy["pending_import_quarantine"]["session_evidence_copied"] is False
        assert privacy["pending_import_quarantine"][
            "git_suffix_is_identifier_delimiter"
        ] is True
        assert all(source["visibility"] == "public" for source in self.lock["sources"])

    def check_component_licenses(self) -> None:
        notice = (ROOT / "COMPONENT_LICENSES.md").read_text(encoding="utf-8")
        normalized = " ".join(notice.split())
        assert "does **not** relicense imported components" in normalized
        assert "unlicensed/all rights reserved" in normalized
        licenses = load_jsonl("provenance/licenses.jsonl")
        assert len(licenses) == 199
        assert all(
            row["target_root_mit_relicenses_component"] is False for row in licenses
        )
        native = next(row for row in licenses if row["repository"] == "kody-w/rapp-god")
        assert native["root_mit_applies"] is True
        assert native["status"] == "explicit-root-license"
        rapp1 = next(row for row in licenses if row["repository"] == "kody-w/rapp-1")
        assert rapp1["status"] == "no-explicit-license-all-rights-reserved"
        recognized = {
            grant["kind"]
            for row in licenses
            for grant in row["grants"]
        }
        assert {"general", "documentation", "code", "data", "data-odbl"} & recognized
        summary = load_json("provenance/license-summary.json")
        assert summary["components"] == 199

    def check_mapping_totals(self) -> None:
        assert len(self.selected_mappings) == assimilation.EXTERNAL_FILE_COUNT
        assert len(self.mappings) == assimilation.EXTERNAL_FILE_COUNT + assimilation.GRAIL_FILE_COUNT
        assert len(self.withheld_mappings) == 716
        assert all(
            set(row)
            == {
                "record_kind",
                "withheld_ordinal",
                "destination",
                "disposition",
            }
            for row in self.withheld_mappings
        )
        assert len(self.materialized_mappings) == 41512
        assert sum(int(row["size"] or 0) for row in self.materialized_mappings) == (
            assimilation.EXTERNAL_LOGICAL_BYTES
            + assimilation.GRAIL_LOGICAL_BYTES
            - 244661926
        )
        keys = [
            (row["source_repository"], row["source_commit"], row["source_path"])
            for row in self.materialized_mappings
        ]
        assert len(keys) == len(set(keys))
        assert self.lock["external_file_count"] == assimilation.EXTERNAL_FILE_COUNT
        assert self.lock["external_logical_bytes"] == assimilation.EXTERNAL_LOGICAL_BYTES
        quarantine = load_json("provenance/quarantine-summary.json")
        assert quarantine["quarantined_target_paths"] == 716
        assert quarantine["quarantined_target_bytes"] == 244661926
        assert quarantine["git_suffix_is_identifier_delimiter"] is True
        assert quarantine["session_evidence_copied"] is False
        assert quarantine["sensitive_identifiers_paths_hashes_published"] is False

    def check_semantic_layout(self) -> None:
        sources = {source["repository"]: source for source in self.lock["sources"]}
        expected = {
            "kody-w/rapp-1": "authority/protocol/rapp-1",
            "kody-w/rapp-installer": "vendor/upstream/rapp-installer-main",
            "kody-w/RAPP": "src/runtime/RAPP",
            "kody-w/rapp-dynamic-workflows": "src/workflows/rapp-dynamic-workflows",
            "kody-w/rapp-ultracode": "src/workflows/rapp-ultracode",
            "kody-w/rapp-alpha": "src/release/channels/rapp-alpha",
            "kody-w/rapp-rings": "src/release/channels/rapp-rings",
            "kody-w/rapp-body": "observatory/components/rapp-body",
            "kody-w/rapp-spine": "observatory/components/rapp-spine",
            "kody-w/rapp-basket": "src/runtime/rapp-basket",
            "kody-w/rapp-burrow": "src/runtime/rapp-burrow",
            "kody-w/rapp-eternity": "archive/retired/protocols/rapp-eternity",
            "kody-w/RAPP_Hub": "archive/generations/catalogs/RAPP_Hub",
            "kody-w/rapp-flight-deck": "src/release/control/rapp-flight-deck",
            "kody-w/rapp-train": "src/release/control/rapp-train",
            "kody-w/rapp-quests": "src/experiences/rapp-quests",
            "kody-w/CommunityRAPP": "services/CommunityRAPP",
            "kody-w/rapp-resident": "services/rapp-resident",
            "kody-w/rio": "products/rio",
            "kody-w/openrappter": "products/openrappter/core",
            "kody-w/rappterbook": "products/rappterbook/generations/v1/rappterbook",
            "kody-w/rappterbook-v2": "products/rappterbook/generations/v2/rappterbook-v2",
            "kody-w/twin": "instances/examples/twin",
        }
        for repository, destination in expected.items():
            assert sources[repository]["destination"] == destination
        destinations = [
            str(source["destination"])
            for source in self.lock["sources"]
            if source["disposition"] != "native-evolved"
        ]
        assert len(destinations) == len(set(destinations))
        assert all("/repos/" not in "/" + path and "/sources/" not in "/" + path for path in destinations)
        assert sources["kody-w/rapp-1"]["source_commit"] == (
            "6723c7add2aed36bb68992fc71a56b0a4bd5ad81"
        )
        assert sources["kody-w/RAPP"]["source_commit"] == (
            "e5436fb8ca9f1b2c676c501b4dc2f5741fda80fc"
        )
        assert sources["kody-w/rapp-installer"]["source_commit"] == (
            "5fbde1776a72715935c3d597a9ddfce28a04032b"
        )
        rapp1 = load_json("authority/records/rapp-1.json")
        assert rapp1["status"] == "structural-authority-only"
        assert rapp1["authenticated_section_13_acceptance"] is False
        assert rapp1["license"] == "no-explicit-license-no-downstream-grant"
        spec = ROOT / rapp1["spec"]["path"]
        assert spec.stat().st_size == rapp1["spec"]["bytes"]
        assert hashlib.sha256(spec.read_bytes()).hexdigest() == rapp1["spec"]["sha256"]
        implementation = load_json("authority/records/rapp-implementation.json")
        assert implementation["status"] == "NOT YET FULLY RAPP/1 CONFORMANT"
        assert (ROOT / implementation["status_document"]).exists()
        blockers = load_json("authority/records/owner-blockers.json")
        assert blockers["full_rapp_1_conformance"] is False
        assert [row["id"] for row in blockers["blockers"]] == [
            "signed-monotonic-registry-and-out-of-band-anchor",
            "lawful-root-re-anchor",
            "signed-replacement-invite",
            "external-mirror-correction",
        ]
        assert all(item["state"] == "open" for item in blockers["blockers"])
        blocker_source = ROOT / blockers["source"]["path"]
        assert blockers["source"]["sha256"] == hashlib.sha256(
            blocker_source.read_bytes()
        ).hexdigest()
        federal = load_json("authority/records/federal-governance.json")
        assert federal["content_available"] is False
        assert federal["content_disposition"] == "withheld-private-boundary"
        assert federal["technical_protocol_authority"] is False
        components = load_jsonl("catalog/components.jsonl")
        assert len(components) == 199
        assert sum(row["authoritative"] for row in components) == 2
        grail = next(
            row
            for row in components
            if row["repository"] == "kody-w/rapp-installer@brainstem-v0.6.9"
        )
        assert grail["lifecycle"] == "immutable-lts"

    def check_destinations_hashes_modes_and_trees(self) -> int:
        tree_groups: Dict[Tuple[str, str, str], List[Dict[str, object]]] = {}
        expected_by_root: Dict[str, set] = {}
        validated = 0
        for row in self.mappings:
            if row.get("record_kind") == "withheld-source-entry":
                continue
            group = (
                str(row["source_repository"]),
                str(row["source_ref"]),
                str(row["source_tree"]),
            )
            tree_groups.setdefault(group, []).append(row)
            if row["source_mode"] == "160000":
                assert row["destination"] is None
                assert row["sha256"] is None
                assert row["disposition"] == "external-pin-not-fetched"
                continue
            destination = Path(str(row["destination"]))
            assert not destination.is_absolute() and ".." not in destination.parts
            path = ROOT / destination
            assert os.path.lexists(str(path)), destination
            mode = str(row["source_mode"])
            info = os.lstat(str(path))
            if mode == "120000":
                assert stat.S_ISLNK(info.st_mode), destination
            else:
                assert stat.S_ISREG(info.st_mode), destination
                executable = bool(info.st_mode & stat.S_IXUSR)
                assert executable == (mode == "100755"), destination
            data = assimilation.file_bytes(path, mode)
            raw_matches = (
                len(data) == row["size"]
                and hashlib.sha256(data).hexdigest() == row["sha256"]
                and git_blob_id(data) == row["source_blob"]
            )
            if not raw_matches:
                assert mode != "120000", destination
                attributes = checkout_attributes(destination)
                assert attributes.get("filter") in {"unspecified", "unset"}, destination
                assert attributes.get("working-tree-encoding") == "unspecified", destination
                assert (
                    attributes.get("text") in {"set", "auto"}
                    or attributes.get("eol") in {"lf", "crlf"}
                ), destination
                canonical = subprocess.run(
                    ["git", "-C", str(ROOT), "cat-file", "blob", row["source_blob"]],
                    check=True,
                    stdout=subprocess.PIPE,
                ).stdout
                assert len(canonical) == row["size"], destination
                assert hashlib.sha256(canonical).hexdigest() == row["sha256"], destination
                assert clean_checkout_blob(destination, data) == row["source_blob"], destination
            validated += 1
            # The lock supplies the exact component root, including multi-level product layouts.
            source = next(
                item
                for item in self.lock["sources"]
                if item["repository"] == row["source_repository"]
            ) if not row.get("authority_alias") else None
            root = (
                assimilation.GRAIL_DESTINATION
                if row.get("authority_alias")
                else str(source["destination"])
            )
            relative = unicodedata.normalize(
                "NFC", str(Path(str(row["destination"])).relative_to(root))
            )
            expected_by_root.setdefault(root, set()).add(relative)

        source_counts = {
            source["repository"]: source["file_count"]
            for source in self.lock["sources"]
            if source["disposition"] != "native-evolved"
        }
        complete_trees = 0
        incomplete_trees = 0
        for group, rows in tree_groups.items():
            expected_count = (
                assimilation.GRAIL_FILE_COUNT
                if group[1] == "brainstem-v0.6.9"
                else source_counts[group[0]]
            )
            if len(rows) == expected_count:
                actual = git_tree_id(rows)
                assert actual == group[2], "{} {} tree {} != {}".format(
                    group[0], group[1], actual, group[2]
                )
                complete_trees += 1
            else:
                incomplete_trees += 1
        represented_repositories = {
            group[0] for group in tree_groups if group[1] != "brainstem-v0.6.9"
        }
        missing_trees = len(set(source_counts) - represented_repositories)
        assert complete_trees == 140
        assert incomplete_trees + missing_trees == 58

        for root, expected in expected_by_root.items():
            actual = set()
            component = ROOT / root
            for directory, directory_names, file_names in os.walk(
                str(component), followlinks=False
            ):
                directory_names[:] = sorted(
                    name
                    for name in directory_names
                    if not os.path.islink(os.path.join(directory, name))
                )
                for name in file_names:
                    path = Path(directory) / name
                    actual.add(unicodedata.normalize("NFC", str(path.relative_to(component))))
                for name in os.listdir(directory):
                    path = Path(directory) / name
                    if path.is_symlink():
                        actual.add(unicodedata.normalize("NFC", str(path.relative_to(component))))
            assert actual == expected, "{} contains unmapped or missing files".format(root)
        return validated

    def check_grail(self) -> None:
        assert len(self.grail_mappings) == assimilation.GRAIL_FILE_COUNT
        assert sum(int(row["size"] or 0) for row in self.grail_mappings) == (
            assimilation.GRAIL_LOGICAL_BYTES
        )
        assert {row["source_commit"] for row in self.grail_mappings} == {
            assimilation.GRAIL_COMMIT
        }
        assert {row["source_tree"] for row in self.grail_mappings} == {
            assimilation.GRAIL_TREE
        }
        for row in self.grail_mappings:
            path = ROOT / str(row["destination"])
            mode = str(row["source_mode"])
            data = assimilation.file_bytes(path, mode)
            assert len(data) == row["size"]
            assert hashlib.sha256(data).hexdigest() == row["sha256"]
            assert git_blob_id(data) == row["source_blob"]
            info = os.lstat(str(path))
            if mode == "120000":
                assert stat.S_ISLNK(info.st_mode)
            else:
                assert stat.S_ISREG(info.st_mode)
                assert bool(info.st_mode & stat.S_IXUSR) == (mode == "100755")
        assert git_tree_id(self.grail_mappings) == assimilation.GRAIL_TREE
        guard = load_json("authority/records/grail-lts.json")
        assert guard["commit"] == assimilation.GRAIL_COMMIT
        assert guard["tree"] == assimilation.GRAIL_TREE
        for relative, expected in {
            "rapp_brainstem/brainstem.py": "a293dd9f11eef915bf15776f08c736faa60cb749820871b6753ea98233142a71",
            "rapp_brainstem/agents/basic_agent.py": "701488bc00d536a7b23295e7da99c62f24e9b00f233daa325886430c736b78eb",
            "rapp_brainstem/VERSION": "13eb74b44be6e3a85a0efa0dedf56aec05e9e50140e1c8bbc0d0fbd8097b0717",
        }.items():
            path = ROOT / assimilation.GRAIL_DESTINATION / relative
            assert hashlib.sha256(path.read_bytes()).hexdigest() == expected

    def check_orphan_gitlink(self) -> None:
        pins = load_json("provenance/external-pins.json")["pins"]
        assert len(pins) == 1
        pin = pins[0]
        assert pin["source_repository"] == "kody-w/rappterbook-agent"
        assert pin["source_path"] == "openclaw"
        assert pin["object"] == assimilation.ORPHAN_GITLINK["object"]
        matches = [
            row
            for row in self.selected_mappings
            if row.get("source_repository") == pin["source_repository"]
            and row.get("source_path") == pin["source_path"]
        ]
        assert len(matches) == 1
        assert matches[0]["source_mode"] == "160000"
        assert matches[0]["source_blob"] == pin["object"]
        assert matches[0]["destination"] is None

    def check_indexes(self) -> None:
        expected = assimilation.index_outputs(self.mappings)
        for relative, data in expected.items():
            if relative == "catalog/indexes/protocols-schemas.jsonl":
                continue
            assert (ROOT / relative).read_bytes() == data, relative
        assert expected["catalog/indexes/agents.jsonl"]
        assert expected["catalog/indexes/tests-conformance.jsonl"]
        assert expected["catalog/indexes/workflows.jsonl"]
        workflow_rows = load_jsonl("catalog/indexes/workflows.jsonl")
        assert all(row["activation"] == "inactive-imported" for row in workflow_rows)
        assert all(
            not str(row["destination"]).startswith(".github/workflows/")
            for row in workflow_rows
        )
        from tools import license_inventory, portability, semantic_catalog, test_catalog

        for generator in (
            semantic_catalog.outputs(),
            test_catalog.outputs(),
            portability.outputs(),
            license_inventory.outputs(),
        ):
            for relative, data in generator.items():
                assert (ROOT / relative).read_bytes() == data, relative
        protocols = load_jsonl("catalog/indexes/protocols-schemas.jsonl")
        assert all("authority_status" in row and "currentness" in row for row in protocols)
        capabilities = load_jsonl("catalog/capabilities.jsonl")
        assert all(not row["runnable"] or row["reviewed"] for row in capabilities)
        assert sum(row["runnable"] for row in capabilities) == 2
        assert len(load_jsonl("catalog/test-suites.jsonl")) == 198
        assert load_json("catalog/portability.json")["invalid_path_records"] == 28
        assert load_json("catalog/portability.json")["long_path_records"] == 5

    def check_observatory_abi(self) -> None:
        baseline = load_json("provenance/observatory-baseline.json")
        for relative in baseline["public_abi_paths"]:
            assert (ROOT / relative).exists(), relative
        for row in baseline["immutable_existing_paths"]:
            path = ROOT / row["path"]
            assert path.exists(), row["path"]
            assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]
        registry = load_json("registry.json")
        assert registry["schema"] == "rapp-god-registry/1.0"
        assert registry["summary"]["parts"] == 60
        assert registry["summary"]["versions"] == 265
        assert registry["summary"]["physical_frames"] == 265
        assert registry["summary"]["tombstones"] == 1
        assert len(registry["parts"]) == 60
        assert len(registry["physical_frames"]) == 265
        assert len(registry["version_tombstones"]) == 1
        assert registry["authority"]["kernel_lts"]["commit"] == assimilation.GRAIL_COMMIT
        assert registry["authority"]["installer_main"]["status"] == "observe-only"
        assert registry["authority"]["federal_governance"]["technical_protocol_authority"] is False
        assert all(
            source["sha8"] is not None
            for part in registry["parts"]
            for source in part["sources"]
        )
        for name in ("brainstem.py", "basic_agent.py", "VERSION"):
            part = next(item for item in registry["parts"] if item["name"] == name)
            assert part["kind"] == "enforce"
            assert part["update_available"] is False
            assert part["sources"][0]["pinned"] is True
            assert part["sources"][0]["source_valid"] is True
            assert any(
                source["label"] == "rapp-installer main"
                and source["observe_only"] is True
                for source in part["sources"]
            )
        status = load_json("api/v1/status.json")
        assert status["physical_frames"] == {"count": 265, "standalone": 0}
        assert len(status["version_tombstones"]) == 1
        for name in ("brainstem.py", "basic_agent.py", "VERSION"):
            part = next(item for item in status["parts"] if item["name"] == name)
            assert part["update_available"] is False
            assert all(
                {"observe_only", "pinned", "source_valid"} <= set(source)
                for source in part["sources"]
            )
        for part in registry["parts"]:
            for version in part["versions"]:
                assert (ROOT / version["path"]).exists(), version["path"]
                assert str(version["url"]).startswith(
                    "https://raw.githubusercontent.com/kody-w/rapp-god/main/versions/"
                )
        for name in ("ecosystem-spec.json", "ECOSYSTEM_SPEC.md"):
            part = next(item for item in registry["parts"] if item["name"] == name)
            assert part["version_count"] == 2
            assert part["drift"] is False
        for frame in registry["physical_frames"]:
            path = ROOT / frame["path"]
            assert path.is_file()
            data = path.read_bytes()
            assert hashlib.sha256(data).hexdigest() == frame["sha"]
            assert path.name.startswith(frame["sha"][:12])
        ecosystem = load_json("api/v1/ecosystem-spec.json")
        assert ecosystem["registry_path_status"] == "quarantined-candidate"
        assert ecosystem["accepted_as_rapp1_registry"] is False
        assert ecosystem["authority"]["technical"]["commit"] == (
            "6723c7add2aed36bb68992fc71a56b0a4bd5ad81"
        )
        history = load_json("provenance/api-history.json")
        for artifact in history["artifacts"]:
            historical = ROOT / artifact["historical_path"]
            assert historical.stat().st_size == artifact["bytes"]
            assert hashlib.sha256(historical.read_bytes()).hexdigest() == artifact["sha256"]
        observatory = load_json("provenance/observatory-history.json")
        assert observatory["explicit_tombstones"] == 1
        assert observatory["current_part_versions"] == 265
        assert observatory["current_indexed_frames"] == 265
        assert observatory["physical_frames"] == 265
        assert observatory["physical_orphans"] == 0
        assert observatory["standalone_physical_frames"] == 0
        assert observatory["raw_url_policy"]["transport_immutable"] is False
        assert observatory["raw_url_policy"]["hash_verification_required"] is True
        version_rows = load_jsonl("provenance/observatory-versions.jsonl")
        tombstone = next(
            row
            for row in version_rows
            if row["path"] == "versions/copilot_swarm.py/0f4b9279d552.py"
        )
        assert tombstone["state"] == "explicit-tombstone-no-payload"
        assert not (ROOT / tombstone["path"]).exists()
        kite = next(
            row
            for row in version_rows
            if row["path"] == "versions/kite-mark.svg/c4c2ffae5467.svg"
        )
        assert kite["state"] == "current-indexed-physical"
        assert kite["current_physical_index"] is True
        assert kite["current_registry_part"] is True

    def check_target_file_sizes(self) -> Tuple[str, int]:
        largest_path = ""
        largest_size = -1
        for directory, directory_names, file_names in os.walk(str(ROOT), followlinks=False):
            directory_names[:] = [
                name
                for name in directory_names
                if name != ".git" and not os.path.islink(os.path.join(directory, name))
            ]
            for name in file_names:
                path = Path(directory) / name
                if path.is_symlink():
                    continue
                size = path.stat().st_size
                assert size < GITHUB_BLOB_LIMIT, "{} is {} bytes".format(
                    path.relative_to(ROOT), size
                )
                if size > largest_size:
                    largest_path = str(path.relative_to(ROOT))
                    largest_size = size
        return largest_path, largest_size

    def check_no_nested_git_metadata(self) -> None:
        for source in self.lock["sources"]:
            if source["disposition"] == "native-evolved":
                continue
            root = ROOT / source["destination"]
            assert not any(path.name == ".git" for path in root.rglob(".git"))
        assert not any(
            path.name == ".git"
            for path in (ROOT / assimilation.GRAIL_DESTINATION).rglob(".git")
        )

    def check_secret_scan(self) -> None:
        assert not (ROOT / "provenance/secret-scan.json").exists()
        quarantine = load_json("provenance/quarantine-summary.json")
        assert quarantine["scan_errors"] == 0
        assert quarantine["quarantined_target_paths"] == 716
        assert quarantine["sensitive_identifiers_paths_hashes_published"] is False

    def check_archive_proof(self) -> None:
        from tools import archive_inventory

        proof = load_json("provenance/archive-audit-proof.json")
        assert proof["schema"] == "rapp-god-archive-proof/4"
        assert proof["session_evidence"]["copied"] is False
        assert proof["pre_quarantine_scan"] == {
            "top_level_containers": 100,
            "nested_containers": 2,
            "members": 3086,
            "maximum_depth": 2,
            "errors": 0,
        }
        assert proof["withheld"] == {
            "archive_paths": 9,
            "archive_member_matches": 14,
            "member_path_matches": 6,
            "member_content_matches": 8,
        }
        assert proof["private_boundary_v2"]["additional_withheld_paths"] == 13
        assert proof["private_boundary_v2"]["total_withheld_paths"] == 716
        member_path = ROOT / proof["retained"]["member_index"]
        member_raw = member_path.read_bytes()
        container_raw = (ROOT / proof["retained"]["container_index"]).read_bytes()
        members = [
            json.loads(line) for line in member_raw.decode("utf-8").splitlines() if line
        ]
        containers = [
            json.loads(line)
            for line in container_raw.decode("utf-8").splitlines()
            if line
        ]
        assert len(members) == proof["retained"]["members"] == 2581
        assert len(containers) == proof["retained"]["containers"] == 93
        assert hashlib.sha256(member_raw).hexdigest() == proof["retained"][
            "member_index_sha256"
        ]
        assert hashlib.sha256(container_raw).hexdigest() == proof["retained"][
            "container_index_sha256"
        ]
        assert all(row["disposition"] == "indexed-not-extracted" for row in members)
        assert all(not row["dangerous_path"] for row in members)
        assert all(not row["dangerous_link_target"] for row in members)
        assert all(not row["encrypted"] for row in members)
        assert all(not row["secret_patterns"] for row in members)
        assert all(row["scan_complete"] for row in containers)
        archive_inventory.check_public()

    def check_upstream_test_baselines(self) -> None:
        baseline = load_json("provenance/upstream-test-baselines.json")
        assert baseline["all_green"] is False
        records = baseline["records"]
        passing = {
            (row["component"], row["suite"]): row
            for row in records
            if row["status"] == "pass"
        }
        assert (passing["RAPP", "kernel pin"]["passed"], passing["RAPP", "kernel pin"]["failed"]) == (3, 0)
        assert (passing["RAPP", "Node contracts"]["passed"], passing["RAPP", "Node contracts"]["failed"]) == (23, 0)
        assert passing["rapp-dynamic-workflows", "source baseline"]["passed"] == 138
        assert passing["rapp-ultracode", "source baseline"]["passed"] == 40
        assert passing[
            "rapp-map", "source-cache full-history offline gates"
        ]["runtime"] == (
            "Python 3.12 and Node.js"
        )
        failures = {
            row["component"]: row
            for row in records
            if row["status"] == "known-upstream-failure"
        }
        assert set(failures) == {"rapp-1", "RAPP-Bible", "rapp-spine", "rapp-body"}
        assert (failures["rapp-1"]["passed"], failures["rapp-1"]["failed"]) == (16, 2)
        assert (failures["RAPP-Bible"]["passed"], failures["RAPP-Bible"]["failed"]) == (5, 12)
        assert (failures["rapp-spine"]["passed"], failures["rapp-spine"]["failed"]) == (52, 1)
        assert "legacy rapp-frame/2.0" in failures["rapp-body"]["reason"]
        assert all(row["exit_code"] != 0 for row in failures.values())
        blocked = {
            row["component"]: row
            for row in records
            if row["status"] == "blocked-private-boundary"
        }
        assert set(blocked) == {"rapp-map", "rapp-spine"}
        assert all(row["exit_code"] == 3 for row in blocked.values())
        for row in records:
            evidence = ROOT / row["evidence"]["path"]
            assert hashlib.sha256(evidence.read_bytes()).hexdigest() == (
                row["evidence"]["sha256"]
            )
            assert row["source_commit"] and row["source_tree"]

    def check_ref_release_proof(self) -> None:
        from tools import ref_inventory

        proof = load_json("provenance/refs-releases-proof.json")
        assert proof["schema"] == "rapp-god-refs-releases-proof/5"
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
        assert proof["identifier_boundary"] == {
            "git_suffix_is_delimiter": True,
            "deny_set_published": False,
        }
        captured_at = proof["captured_at"]
        assert not (ROOT / "provenance/refs.source.tsv").exists()
        releases_source = (ROOT / "provenance/releases.source.jsonl").read_bytes()
        refs_raw = (ROOT / proof["refs"]["index"]).read_bytes()
        releases_raw = (ROOT / proof["releases"]["index"]).read_bytes()
        assets_raw = (ROOT / proof["assets"]["index"]).read_bytes()
        refs = [json.loads(line) for line in refs_raw.decode("utf-8").splitlines() if line]
        releases = [
            json.loads(line) for line in releases_raw.decode("utf-8").splitlines() if line
        ]
        assets = [
            json.loads(line) for line in assets_raw.decode("utf-8").splitlines() if line
        ]
        assert hashlib.sha256(releases_source).hexdigest() == (
            "36c7aa90aa109c5b731c35187d2a7270f3fbbe52b4ea499eb6d047180d1c3880"
        )
        assert proof["independent_evidence"]["refs"] == {
            "session_evidence_verified": True,
            "copied": False,
        }
        assert proof["independent_evidence"]["releases"]["sha256"] == hashlib.sha256(
            releases_source
        ).hexdigest()
        assert proof["scope"] == {"selected_repositories": 198}
        assert proof["refs"]["records"] == len(refs) == 12634
        assert proof["refs"]["remote_heads"] == 5083
        assert proof["refs"]["canonical_tags"] == 169
        assert proof["refs"]["peeled_tags"] == 81
        assert proof["refs"]["pull_refs"] == 6905
        assert proof["refs"]["head_outliers"] == [
            {"repository": "kody-w/rappterverse", "remote_heads": 4289},
            {
                "repository": "kody-w/rappterbook-agent-exchange",
                "remote_heads": 133,
            },
            {"repository": "kody-w/rappterbook", "remote_heads": 112},
        ]
        assert hashlib.sha256(refs_raw).hexdigest() == proof["refs"]["index_sha256"]
        withheld_refs = [row for row in refs if row.get("record_kind") == "withheld-ref"]
        retained_refs = [row for row in refs if row.get("record_kind") != "withheld-ref"]
        assert len(withheld_refs) == proof["refs"]["withheld_records"] == 22
        assert len(retained_refs) == proof["refs"]["retained_records"]
        assert all(
            set(row) == {"record_kind", "withheld_ordinal", "disposition"}
            for row in withheld_refs
        )
        assert all(row["disposition"] == "indexed-ref-not-created" for row in retained_refs)
        assert all(
            str(row["namespaced_metadata_key"]).startswith("refs/provenance/kody-w/")
            for row in retained_refs
        )
        assert len({row["namespaced_metadata_key"] for row in retained_refs}) == len(retained_refs)
        actual_refs = subprocess.run(
            [
                "git",
                "-C",
                str(ROOT),
                "for-each-ref",
                "--format=%(refname)",
                "refs/provenance/",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        assert not actual_refs.strip()

        assert proof["releases"]["records"] == len(releases) == 75
        assert proof["releases"]["repositories"] == len(
            {row["repository"] for row in releases}
        ) == 41
        assert hashlib.sha256(releases_raw).hexdigest() == (
            proof["releases"]["index_sha256"]
        )
        assert proof["assets"]["records"] == len(assets) == 50
        assert sum(int(row["size"]) for row in assets) == 1204660676
        assert proof["assets"]["logical_bytes"] == 1204660676
        assert proof["assets"]["stored_as_git_blobs"] == 0
        assert proof["assets"]["fetched_as_release_assets"] == 0
        assert hashlib.sha256(assets_raw).hexdigest() == proof["assets"]["index_sha256"]
        assert all(
            row["disposition"] == "external-release-asset"
            and row["stored_as_git_blob"] is False
            and row["fetched_as_release_asset"] is False
            and row["digest_source"] == "github-api-reported"
            and row["digest_independently_download_verified"] is False
            and str(row["browser_download_url"]).startswith("https://github.com/")
            and str(row["digest"]).startswith("sha256:")
            and len(str(row["digest"])) == 71
            and "destination" not in row
            for row in assets
        )
        oversized = [row for row in assets if int(row["size"]) >= 100_000_000]
        assert len(oversized) == proof["assets"]["oversized_records"] == 4
        assert {row["repository"] for row in oversized} == {"kody-w/ez-rapp"}
        public_outputs = ref_inventory.public_release_outputs()
        assert public_outputs["provenance/releases.jsonl"] == releases_raw
        assert public_outputs["provenance/release-assets.jsonl"] == assets_raw
        assert len(load_jsonl("catalog/indexes/ref-summary.jsonl")) == 198
        assert len(load_jsonl("catalog/indexes/releases.jsonl")) == 75
        tags = load_jsonl("provenance/tag-targets.jsonl")
        assert len(tags) == proof["tag_targets"]["records"] == 169
        assert len(
            [row for row in tags if row.get("record_kind") == "withheld-tag-target"]
        ) == proof["tag_targets"]["withheld_records"]
        assert hashlib.sha256(
            (ROOT / proof["tag_targets"]["index"]).read_bytes()
        ).hexdigest() == proof["tag_targets"]["index_sha256"]
        snapshot = load_json("provenance/ref-snapshot-manifest.json")
        assert snapshot["schema"] == "rapp-god-ref-snapshot-manifest/2"
        assert snapshot["captured_at"] == captured_at
        assert snapshot["capture_model"] == "non-atomic-multi-repository-window"
        assert snapshot["atomic"] is False
        assert snapshot["collection_started_at"] == "2026-07-23T05:11:01Z"
        assert snapshot["collection_completed_at"] == "2026-07-23T05:11:11Z"
        assert snapshot["histories_imported"] is False
        assert snapshot["scope"] == (
            "default-tree-snapshot-plus-external-oid-inventory"
        )
        assert len(snapshot["repositories"]) == 198
        assert snapshot["selected_default_tree_pins"][
            "may_predate_ref_observations"
        ] is True
        assert all(
            row["ref_query"]["status"] == "provided-snapshot"
            and row["release_query"]["status"] == "provided-snapshot"
            for row in snapshot["repositories"]
        )
        assert proof["refs"]["scope"] == "external-oid-inventory-not-imported-history"
        assert proof["policy"]["create_target_refs"] is False
        assert proof["policy"]["fetch_release_assets"] is False
        ref_inventory.check_public()

    def check_native_commit_and_census_proof(self) -> None:
        from tools import native_provenance

        native_provenance.check()
        lock = self.lock
        assert lock["native_baseline"] == {
            "commit": "66f47a72767cc59d310ddc07d745cce4d612fae8",
            "tree": "89599a90e24bebdbbb4c54e29a5ba11f6871b452",
            "file_count": 284,
            "preserved": 274,
            "evolved": 10,
            "ledger": "provenance/native-files.jsonl",
        }
        selected = (ROOT / "provenance/selected-repositories.txt").read_bytes()
        assert selected.count(b"\n") == 198
        assert hashlib.sha256(selected).hexdigest() == (
            lock["selected_repositories"]["sha256"]
        )
        census = load_json("provenance/census-proof.json")
        assert census["public_repositories"] == 370
        assert census["private_quarantine"]["count"] == 142
        assert census["commit_object_records"] == {
            "retained": 140,
            "withheld": 58,
        }

    def check_source_capture_window(self) -> None:
        from tools import source_capture

        source_capture.check()
        window = self.lock["capture_window"]
        assert window["model"] == "non-atomic-per-repository"
        assert window["atomic_owner_snapshot"] is False
        assert window["started_at"] == "2026-07-23T04:48:04Z"
        assert window["completed_at"] == "2026-07-23T05:49:36Z"

    def check_workspace_graph(self) -> None:
        workspace = load_json("WORKSPACE.json")
        assert workspace["schema"] == "rapp-god-workspace/2"
        tasks = {row["id"]: row for row in workspace["tasks"]}
        assert len(tasks) == len(workspace["tasks"])
        assert all(
            isinstance(row["argv"], list)
            and row["argv"]
            and row["argv"][0] == "python3"
            and row["network"] is False
            for row in tasks.values()
        )
        assert all(
            dependency in tasks
            for row in tasks.values()
            for dependency in row["depends_on"]
        )

        visiting = set()
        visited = set()

        def visit(task):
            assert task not in visiting
            if task in visited:
                return
            visiting.add(task)
            for dependency in tasks[task]["depends_on"]:
                visit(dependency)
            visiting.remove(task)
            visited.add(task)

        for task in tasks:
            visit(task)
        assert len(visited) == len(tasks)
        overlay = load_json("workspace/overlays/ultracode-rdw.json")
        assert overlay["modifies_imported_pyproject"] is False
        release = load_json("catalog/release-view.json")
        assert release["installer"]["moving_upstream"]["label"] == "production-head"
        assert release["installer"]["authority"]["label"] == "lts-grail"

    def check_build_no_net(self) -> None:
        result = subprocess.run(
            ["python3", "build_god.py", "--check"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    def check_generated_artifact_manifest(self) -> None:
        from tools import generated_manifest

        expected = generated_manifest.data()
        actual = (ROOT / "provenance/generated-files.jsonl").read_bytes()
        assert actual == expected
        rows = [
            json.loads(line) for line in actual.decode("utf-8").splitlines() if line
        ]
        paths = {row["path"] for row in rows}
        for base in ("catalog", "provenance"):
            for path in (ROOT / base).rglob("*"):
                if path.is_file() and path.name != "generated-files.jsonl":
                    assert str(path.relative_to(ROOT)) in paths

    def check_staged_closure_and_secret_report(self) -> None:
        from tools import stage_materialized

        expected = stage_materialized.expected_index()
        stage_materialized.check_index(expected)
        report = load_json("provenance/staged-secret-scan.json")
        assert report["unallowlisted_findings"] == 0
        assert report["values_recorded"] is False
        assert report["archive_scan"]["recursive"] is True
        assert report["archive_scan"]["complete"] is True
        assert report["archive_scan"]["secret_hits"] == 0

    def run_all(self) -> Dict[str, object]:
        decisions = self.check_decisions()
        self.check_private_quarantine()
        self.check_component_licenses()
        self.check_mapping_totals()
        self.check_semantic_layout()
        validated = self.check_destinations_hashes_modes_and_trees()
        self.check_grail()
        self.check_orphan_gitlink()
        self.check_indexes()
        self.check_observatory_abi()
        largest_path, largest_size = self.check_target_file_sizes()
        self.check_no_nested_git_metadata()
        self.check_secret_scan()
        self.check_archive_proof()
        self.check_upstream_test_baselines()
        self.check_ref_release_proof()
        self.check_native_commit_and_census_proof()
        self.check_source_capture_window()
        self.check_workspace_graph()
        self.check_build_no_net()
        self.check_generated_artifact_manifest()
        self.check_staged_closure_and_secret_report()
        return {
            "public_repositories": len(self.repositories),
            "selected_repositories": len(self.lock["sources"]),
            "selected_external_entries": len(self.selected_mappings),
            "validated_imported_files": validated,
            "retained_materialized_bytes": sum(
                int(row["size"] or 0) for row in self.materialized_mappings
            ),
            "decisions": decisions,
            "largest_file": largest_path,
            "largest_file_bytes": largest_size,
            "archive_containers": 102,
            "archive_members": 3086,
            "remote_heads_indexed": 5083,
            "releases_indexed": 75,
            "external_release_assets": 50,
            "withheld_paths": 716,
            "withheld_bytes": 244661926,
        }


def main() -> int:
    result = IntegrityChecker().run_all()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
