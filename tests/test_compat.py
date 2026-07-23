import json
from pathlib import Path
import unittest

from compat.rapp1 import CompatibilityError, normalize_request, normalize_success
from compat.sdk_paths import PathResolutionError, RegistryPathResolver


ROOT = Path(__file__).resolve().parents[1]


class CompatibilityTests(unittest.TestCase):
    def test_rapp1_request_success_and_422_are_strict(self):
        fixture_root = ROOT / "tests/fixtures/compat"
        request_fixture = json.loads((fixture_root / "rapp1-request.json").read_text())
        success_fixture = json.loads((fixture_root / "rapp1-success.json").read_text())
        error_fixture = json.loads((fixture_root / "rapp1-422.json").read_text())
        request = normalize_request(request_fixture)
        self.assertEqual(
            set(request), {"user_input", "session_id", "idempotency_key"}
        )
        self.assertEqual(normalize_request({"user_input": ""}), {"user_input": ""})
        success = normalize_success(
            success_fixture["response"],
            success_fixture["agent_logs"],
            success_fixture["session_id"],
        )
        self.assertEqual(success, success_fixture)
        self.assertEqual(set(success), {"response", "agent_logs", "session_id"})
        with self.assertRaises(CompatibilityError) as caught:
            normalize_request(
                {
                    "user_input": 1,
                    "execute": True,
                }
            )
        self.assertEqual(caught.exception.http_status, 422)
        self.assertEqual(set(caught.exception.as_422()), {"error"})
        self.assertEqual(set(caught.exception.as_422()["error"]), {"code", "step"})
        self.assertEqual(CompatibilityError().as_422(), error_fixture)
        with self.assertRaises(CompatibilityError):
            normalize_success("ok", [1], "s-1")

    def test_registry_path_resolver_is_relative_cached_and_explicit(self):
        resolver = RegistryPathResolver(
            ROOT,
            {
                "rapp1": "authority/protocol/rapp-1",
                "grail": "vendor/grail/rapp-installer-brainstem-v0.6.9",
            },
        )
        first = resolver.resolve("rapp1", "SPEC.md")
        second = resolver.resolve("rapp1", "SPEC.md")
        self.assertIs(first, second)
        self.assertEqual(len(resolver.cache_key("rapp1", "SPEC.md")), 64)
        with self.assertRaises(PathResolutionError):
            resolver.resolve("rapp1", "../manifest.json")
        with self.assertRaises(PathResolutionError):
            resolver.resolve("missing", "SPEC.md")

    def test_current_mcp_profile_is_7073_without_bootstrap(self):
        profiles = json.loads((ROOT / "compat/profiles.json").read_text())["profiles"]
        mcp = next(row for row in profiles if row["id"] == "rapp-mcp-client/1")
        self.assertEqual(mcp["default_port"], 7073)
        self.assertFalse(mcp["bootstrap"])
        current = [row for row in profiles if row["status"].startswith("reviewed-runnable")]
        self.assertNotIn("7071", json.dumps(current))
        static_ids = {
            row["id"] for row in profiles if row["id"].startswith("rapp-static-mcp-")
        }
        self.assertEqual(
            static_ids,
            {
                "rapp-static-mcp-catalog/1",
                "rapp-static-mcp-python-agent-frame/1",
                "rapp-static-mcp-browser-cell/1",
            },
        )

    def test_legacy_profiles_are_visible_but_not_runnable(self):
        profiles = json.loads((ROOT / "compat/profiles.json").read_text())["profiles"]
        legacy = [row for row in profiles if row["status"] == "legacy-non-runnable"]
        self.assertGreaterEqual(len(legacy), 5)
        self.assertTrue(all(row["runnable"] is False for row in legacy))


if __name__ == "__main__":
    unittest.main()
