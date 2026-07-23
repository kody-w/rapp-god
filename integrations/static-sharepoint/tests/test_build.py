"""Deterministic build contract tests — stdlib unittest only."""

from __future__ import annotations

import copy
import importlib.util
import json
import re
import shutil
import sys
import tempfile
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import build  # noqa: E402

SOURCE = build.load_source()
OUTPUTS = build.build_outputs(SOURCE)
NAMESPACE = uuid.UUID(SOURCE["namespace"])
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

SOURCE_KEYS = {"contracts": "contracts", "policies": "policies", "meetingnotes": "meetingnotes"}


def items_for(list_key: str) -> list[dict]:
    path = build.API_ROOT / "lists" / build.LISTS[list_key]["path"] / "items.json"
    return json.loads(OUTPUTS[path].decode("utf-8"))["d"]["results"]


def lists_index() -> list[dict]:
    return json.loads(OUTPUTS[build.API_ROOT / "lists.json"].decode("utf-8"))["d"]["results"]


class DeterminismTests(unittest.TestCase):
    def test_two_builds_are_byte_identical(self) -> None:
        second = build.build_outputs(build.load_source())
        self.assertEqual(sorted(OUTPUTS), sorted(second))
        for path, payload in OUTPUTS.items():
            self.assertEqual(payload, second[path], path.as_posix())

    def test_check_matches_every_committed_output(self) -> None:
        self.assertEqual(build.check_outputs(OUTPUTS), [])

    def test_rebuild_to_temp_area_matches_committed_bytes(self) -> None:
        for path, payload in OUTPUTS.items():
            self.assertEqual(path.read_bytes(), payload, path.as_posix())


class ShapeTests(unittest.TestCase):
    def test_every_output_parses_as_json_or_html(self) -> None:
        for path, payload in OUTPUTS.items():
            if path.suffix == ".json":
                json.loads(payload.decode("utf-8"))
            else:
                self.assertTrue(payload.decode("utf-8").startswith("<!doctype html>"))

    def test_collections_use_classic_sp_rest_envelope(self) -> None:
        for list_key in build.LISTS:
            path = build.API_ROOT / "lists" / build.LISTS[list_key]["path"] / "items.json"
            document = json.loads(OUTPUTS[path].decode("utf-8"))
            self.assertEqual(set(document), {"d"})
            self.assertEqual(set(document["d"]), {"results"})
            self.assertIsInstance(document["d"]["results"], list)

    def test_counts_derive_from_source_never_hardcoded(self) -> None:
        for list_key, source_key in SOURCE_KEYS.items():
            self.assertEqual(
                len(items_for(list_key)),
                len(SOURCE[source_key]),
                list_key,
            )
        index_counts = {entry["Title"]: entry["ItemCount"] for entry in lists_index()}
        for list_key, spec in build.LISTS.items():
            self.assertEqual(index_counts[spec["title"]], len(items_for(list_key)))

    def test_every_item_has_required_fields(self) -> None:
        required = {
            "__metadata",
            "Id",
            "ID",
            "GUID",
            "Title",
            "FileLeafRef",
            "ServerRelativeUrl",
            "Author",
            "AuthorId",
            "Created",
            "Modified",
            "Preview",
        }
        for list_key in build.LISTS:
            for item in items_for(list_key):
                self.assertTrue(required <= set(item), f"{list_key}: {item['Title']}")
                self.assertEqual(item["Id"], item["ID"])
                self.assertRegex(item["FileLeafRef"], r"\.(docx|pdf)$")
                self.assertTrue(
                    item["ServerRelativeUrl"].endswith(item["FileLeafRef"])
                )
                self.assertEqual(
                    item["__metadata"]["type"], build.LISTS[list_key]["entity_type"]
                )
                self.assertGreaterEqual(len(item["Preview"]), 40)


class IdentifierTests(unittest.TestCase):
    def test_every_guid_is_rederivable_via_uuid5(self) -> None:
        for list_key in build.LISTS:
            for index, item in enumerate(items_for(list_key)):
                expected = str(
                    uuid.uuid5(NAMESPACE, f"{build.REPO_SLUG}/{list_key}/{index}")
                )
                self.assertEqual(item["GUID"], expected)
                self.assertEqual(item["Id"], index + 1)

    def test_list_ids_are_rederivable_via_uuid5(self) -> None:
        by_title = {entry["Title"]: entry for entry in lists_index()}
        for spec in build.LISTS.values():
            expected = str(
                uuid.uuid5(NAMESPACE, f"{build.REPO_SLUG}/lists/{spec['path']}")
            )
            self.assertEqual(by_title[spec["title"]]["Id"], expected)


class DateTests(unittest.TestCase):
    def test_all_dates_are_canonical_utc_and_epoch_derived(self) -> None:
        epoch = datetime.fromisoformat(SOURCE["epoch"].replace("Z", "+00:00"))
        date_fields = ("Created", "Modified", "ExpiryDate", "EffectiveDate", "MeetingDate")
        for list_key in build.LISTS:
            for item in items_for(list_key):
                for field in date_fields:
                    if field not in item:
                        continue
                    self.assertRegex(item[field], DATE_RE, f"{list_key}.{field}")
                    parsed = datetime.fromisoformat(item[field].replace("Z", "+00:00"))
                    self.assertEqual(parsed.tzinfo, timezone.utc)
                created = datetime.fromisoformat(item["Created"].replace("Z", "+00:00"))
                modified = datetime.fromisoformat(item["Modified"].replace("Z", "+00:00"))
                self.assertLess(created, modified)
                self.assertLess(created, epoch)


class CrossReferenceTests(unittest.TestCase):
    def test_related_accounts_resolve_to_shared_world_accounts(self) -> None:
        accounts = set(SOURCE["accounts"])
        for list_key in ("contracts", "meetingnotes"):
            for item in items_for(list_key):
                if item.get("RelatedAccount") is not None:
                    self.assertIn(item["RelatedAccount"], accounts)

    def test_related_tickets_use_crm_ticket_format(self) -> None:
        ticket_re = re.compile(r"^CAS-\d{6}$")
        seen = 0
        for list_key in ("contracts", "meetingnotes"):
            for item in items_for(list_key):
                if item.get("RelatedTicket") is not None:
                    self.assertRegex(item["RelatedTicket"], ticket_re)
                    seen += 1
        self.assertGreater(seen, 0)

    def test_authors_resolve_to_tenant_identities(self) -> None:
        names = {identity["name"] for identity in SOURCE["identities"]}
        for list_key in build.LISTS:
            for item in items_for(list_key):
                self.assertIn(item["Author"], names)
                self.assertEqual(
                    SOURCE["identities"][item["AuthorId"] - 1]["name"], item["Author"]
                )

    def test_summit_trail_renewal_matches_crm_case(self) -> None:
        contracts = items_for("contracts")
        renewal = next(
            item
            for item in contracts
            if item["RelatedAccount"] == "Summit Trail Software"
            and item["ContractType"] == "Renewal"
        )
        self.assertEqual(renewal["RelatedTicket"], "CAS-260134")
        granite = next(
            item
            for item in contracts
            if item["RelatedAccount"] == "Granite Peak Manufacturing"
        )
        self.assertEqual(granite["ContractType"], "SOW")

    def test_no_real_domains_or_binary_paths_leak(self) -> None:
        for path, payload in OUTPUTS.items():
            text = payload.decode("utf-8")
            self.assertNotIn("sharepoint.com", text, path.as_posix())
            self.assertNotIn("@example.com", text, path.as_posix())


class ValidationTests(unittest.TestCase):
    def rejects(self, mutate) -> None:
        source = copy.deepcopy(SOURCE)
        mutate(source)
        with self.assertRaises(build.BuildError):
            build.build_outputs(source)

    def test_invalid_sources_are_rejected(self) -> None:
        self.rejects(lambda s: s.__setitem__("epoch", "2026-01-15T12:00:00Z"))
        self.rejects(lambda s: s.__setitem__("namespace", "not-a-uuid"))
        self.rejects(lambda s: s["tenant"].__setitem__("name", "Someone Else"))
        self.rejects(lambda s: s["contracts"][0].__setitem__(2, "Unknown Account"))
        self.rejects(lambda s: s["contracts"][0].__setitem__(5, "Bogus Status"))
        self.rejects(lambda s: s["contracts"][0].__setitem__(8, "TICKET-1"))
        self.rejects(lambda s: s["policies"][0].__setitem__(2, "Bogus Category"))
        self.rejects(lambda s: s["meetingnotes"][0].__setitem__(1, "Not A File Name"))
        self.rejects(lambda s: s.__setitem__("extra", []))


class WriteBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tempdir, True)
        (self.tempdir / "data").mkdir()
        shutil.copy(ROOT / "data" / "source.json", self.tempdir / "data" / "source.json")
        spec = importlib.util.spec_from_file_location(
            "process_write_issue", ROOT / "scripts" / "process_write_issue.py"
        )
        self.bridge = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.bridge)
        self.bridge.SOURCE_PATH = self.tempdir / "data" / "source.json"

    def command(self, operation: str, entity: str, record: dict) -> dict:
        return {
            "schema": "sharepoint-write/1.0",
            "operation": operation,
            "entity": entity,
            "record": record,
        }

    def test_create_contract_then_build_serves_it(self) -> None:
        receipt = self.bridge.process(
            self.command(
                "create",
                "Contracts",
                {
                    "Title": "Maple Thread Textiles Loom Room SOW",
                    "RelatedAccount": "Maple Thread Textiles",
                    "ContractValue": 31200,
                    "RelatedTicket": "CAS-260121",
                },
            )
        )
        self.assertTrue(receipt["Id"] > len(SOURCE["contracts"]) - 1)
        mutated = json.loads(self.bridge.SOURCE_PATH.read_text(encoding="utf-8"))
        outputs = build.build_outputs(mutated)
        path = build.API_ROOT / "lists" / "Contracts" / "items.json"
        results = json.loads(outputs[path].decode("utf-8"))["d"]["results"]
        self.assertEqual(len(results), len(SOURCE["contracts"]) + 1)
        self.assertEqual(results[-1]["Title"], "Maple Thread Textiles Loom Room SOW")
        self.assertEqual(results[-1]["GUID"], receipt["GUID"])

    def test_create_meeting_note_accepts_spaced_entity_name(self) -> None:
        receipt = self.bridge.process(
            self.command(
                "create",
                "Meeting Notes",
                {
                    "Title": "Juniper Ridge Desk Program Kickoff",
                    "RelatedAccount": "Juniper Ridge Furnishings",
                    "Preview": (
                        "Kickoff notes for the Juniper Ridge desk refresh program, "
                        "covering delivery windows and assembly guide feedback."
                    ),
                },
            )
        )
        self.assertEqual(receipt["entity"], "Meeting Notes")
        mutated = json.loads(self.bridge.SOURCE_PATH.read_text(encoding="utf-8"))
        build.build_outputs(mutated)

    def test_update_contract_status_by_id(self) -> None:
        receipt = self.bridge.process(
            self.command("update", "Contracts", {"Id": 1, "Status": "Active"})
        )
        self.assertEqual(receipt["changed"], ["Status"])
        mutated = json.loads(self.bridge.SOURCE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(mutated["contracts"][0][5], "Active")
        build.build_outputs(mutated)

    def test_unsupported_operations_are_rejected(self) -> None:
        for operation, entity, record in (
            ("delete", "Contracts", {"Id": 1}),
            ("create", "Policies", {"Title": "New Policy Attempt Number One"}),
            ("update", "Meeting Notes", {"Id": 1, "Status": "Active"}),
            ("create", "Contracts", {"Title": "No Account Given Here"}),
        ):
            with self.assertRaises(self.bridge.WriteError):
                self.bridge.process(self.command(operation, entity, record))


if __name__ == "__main__":
    unittest.main()
