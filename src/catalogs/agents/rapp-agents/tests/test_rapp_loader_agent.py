"""Tests for agents/rapp_loader_agent.py — the hot-loader."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
AGENTS_DIR = REPO_ROOT / "agents"

# Put the agents dir on sys.path so 'basic_agent' resolves.
sys.path.insert(0, str(AGENTS_DIR))


# Module-level isolation: redirect WORKSPACE + REPOS_CONFIG to tmpdirs.
_tmpdir = None


def setUpModule():
    global _tmpdir
    _tmpdir = tempfile.TemporaryDirectory(prefix="rapp_loader_test_")
    base = Path(_tmpdir.name)
    os.environ["RAPP_WORKSPACE"] = str(base / "workspace")
    os.environ["RAPP_LOADER_REPOS_CONFIG"] = str(base / "loader_repos.json")
    (base / "workspace").mkdir(parents=True, exist_ok=True)
    # Plant a real basic_agent.py copy in the workspace so it's "canonical".
    (base / "workspace" / "basic_agent.py").write_text(
        (AGENTS_DIR / "basic_agent.py").read_text()
    )


def tearDownModule():
    global _tmpdir
    if _tmpdir:
        _tmpdir.cleanup()
    os.environ.pop("RAPP_WORKSPACE", None)
    os.environ.pop("RAPP_LOADER_REPOS_CONFIG", None)


def _import_loader():
    """Import fresh each test so env-var overrides are picked up."""
    if "rapp_loader_agent" in sys.modules:
        del sys.modules["rapp_loader_agent"]
    import rapp_loader_agent  # noqa: WPS433
    return rapp_loader_agent


def _write_agent_file(path, class_name):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        "from basic_agent import BasicAgent\n"
        f"class {class_name}(BasicAgent):\n"
        "    def __init__(self):\n"
        f"        self.name = '{class_name}'\n"
        "        self.metadata = {'name': self.name, "
        "'description': 'x', 'parameters': {'type':'object','properties':{}}}\n"
        "        super().__init__(name=self.name, metadata=self.metadata)\n"
        "    def perform(self, **kwargs):\n"
        "        return 'ok'\n"
    )


def _make_repo(root, name, agents=(), stacks=()):
    """Create a fake stack repo at root/name with given agents and stacks."""
    d = Path(root) / name
    (d / "agents").mkdir(parents=True, exist_ok=True)
    (d / "stacks").mkdir(parents=True, exist_ok=True)
    # Every repo has its own basic_agent.py
    (d / "agents" / "basic_agent.py").write_text(
        (AGENTS_DIR / "basic_agent.py").read_text()
    )
    for filename, class_name in agents:
        _write_agent_file(d / "agents" / filename, class_name)
    for stack in stacks:
        (d / "stacks" / f"{stack['name']}.json").write_text(json.dumps(stack))
    return d


class _LoaderTestBase(unittest.TestCase):
    """Per-test isolation of workspace + repos config."""

    def setUp(self):
        self.fixture = tempfile.TemporaryDirectory()
        self.tmp = Path(self.fixture.name)

        # Override env per-test so each test gets a clean workspace and registry.
        self.workspace = self.tmp / "workspace"
        self.workspace.mkdir(parents=True, exist_ok=True)
        (self.workspace / "basic_agent.py").write_text(
            (AGENTS_DIR / "basic_agent.py").read_text()
        )
        self.repos_config = self.tmp / "loader_repos.json"

        os.environ["RAPP_WORKSPACE"] = str(self.workspace)
        os.environ["RAPP_LOADER_REPOS_CONFIG"] = str(self.repos_config)
        # Seed empty registry so each test starts with no default fallback.
        self.repos_config.write_text("[]")

        self.mod = _import_loader()
        self.agent = self.mod.RappLoaderAgent()

    def tearDown(self):
        self.fixture.cleanup()

    def _call(self, **kwargs):
        return json.loads(self.agent.perform(**kwargs))


# --------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------

class TestMetadata(_LoaderTestBase):

    def test_name(self):
        self.assertEqual(self.agent.name, "RappLoader")

    def test_metadata_required_fields(self):
        m = self.agent.metadata
        self.assertEqual(m["name"], "RappLoader")
        self.assertIn("description", m)
        self.assertIn("parameters", m)

    def test_action_enum_complete(self):
        actions = self.agent.metadata["parameters"]["properties"]["action"]["enum"]
        expected = {
            "catalog", "load", "unload", "loaded",
            "load_stack", "unload_stack", "unload_all",
            "sync", "add_repo", "remove_repo", "list_repos",
        }
        self.assertEqual(set(actions), expected)

    def test_to_tool(self):
        tool = self.agent.to_tool()
        self.assertEqual(tool["function"]["name"], "RappLoader")


class TestEmpty(_LoaderTestBase):

    def test_catalog_with_no_repos_returns_envelope(self):
        # Empty registry → defaults are tried, and they probably don't exist
        # in tempdir. Catalog should still succeed and report missing.
        r = self._call(action="catalog")
        self.assertIn("agents", r)
        self.assertIn("stacks", r)
        self.assertEqual(r["agent_count"], 0)

    def test_loaded_with_no_loads(self):
        r = self._call(action="loaded")
        # basic_agent.py is canonical and excluded from loaded list
        self.assertEqual(r["loaded"], [])

    def test_unknown_action(self):
        r = self._call(action="bogus")
        self.assertIn("error", r)


class TestCatalog(_LoaderTestBase):

    def test_catalog_finds_repo_agents(self):
        _make_repo(self.tmp, "stackA", agents=[
            ("scout_agent.py", "Scout"),
            ("double_down_agent.py", "DoubleDown"),
        ])
        self._call(action="add_repo", path=str(self.tmp / "stackA"))
        r = self._call(action="catalog")
        names = {a["name"] for a in r["agents"]}
        self.assertIn("Scout", names)
        self.assertIn("DoubleDown", names)

    def test_catalog_finds_stacks(self):
        _make_repo(self.tmp, "stackA",
                   agents=[("scout_agent.py", "Scout")],
                   stacks=[{"name": "x", "description": "y", "agents": ["Scout"]}])
        self._call(action="add_repo", path=str(self.tmp / "stackA"))
        r = self._call(action="catalog")
        stacks = {s["name"] for s in r["stacks"]}
        self.assertIn("x", stacks)

    def test_catalog_reports_missing_repos(self):
        self._call(action="add_repo", path=str(self.tmp / "stackA"))  # doesn't exist as a dir
        # add_repo refuses non-dirs; so add a real one, then delete it
        _make_repo(self.tmp, "stackA",
                   agents=[("a_agent.py", "A")])
        self._call(action="add_repo", path=str(self.tmp / "stackA"))
        # Remove the dir contents and the dir itself
        import shutil
        shutil.rmtree(self.tmp / "stackA")
        r = self._call(action="catalog")
        self.assertTrue(any(
            "stackA" in m for m in r.get("missing_repos", [])
        ))

    def test_agent_friendly_name_mapping(self):
        _make_repo(self.tmp, "stackA",
                   agents=[("project_twin_agent.py", "ProjectTwin")])
        self._call(action="add_repo", path=str(self.tmp / "stackA"))
        r = self._call(action="catalog")
        names = {a["name"] for a in r["agents"]}
        self.assertIn("ProjectTwin", names)


class TestLoadUnload(_LoaderTestBase):

    def setUp(self):
        super().setUp()
        _make_repo(self.tmp, "stackA", agents=[
            ("scout_agent.py", "Scout"),
            ("double_down_agent.py", "DoubleDown"),
        ])
        self._call(action="add_repo", path=str(self.tmp / "stackA"))

    def test_load_by_friendly_name(self):
        r = self._call(action="load", name="Scout")
        self.assertTrue(r["ok"])
        self.assertTrue((self.workspace / "scout_agent.py").is_symlink())

    def test_load_by_filename(self):
        r = self._call(action="load", name="scout_agent.py")
        self.assertTrue(r["ok"])

    def test_load_case_insensitive(self):
        r = self._call(action="load", name="scout")
        self.assertTrue(r["ok"])

    def test_load_missing_agent_errors(self):
        r = self._call(action="load", name="DefinitelyNotReal")
        self.assertIn("error", r)

    def test_load_requires_name(self):
        r = self._call(action="load")
        self.assertIn("error", r)

    def test_unload_removes_symlink(self):
        self._call(action="load", name="Scout")
        r = self._call(action="unload", name="Scout")
        self.assertTrue(r["ok"])
        self.assertFalse((self.workspace / "scout_agent.py").exists())

    def test_unload_not_loaded_is_noop(self):
        r = self._call(action="unload", name="Scout")
        self.assertTrue(r["ok"])
        self.assertIn("note", r)

    def test_unload_protects_canonical_basic_agent(self):
        r = self._call(action="unload", name="basic_agent.py")
        self.assertIn("error", r)
        # basic_agent.py still exists
        self.assertTrue((self.workspace / "basic_agent.py").exists())

    def test_unload_protects_canonical_loader(self):
        # Pre-plant the loader as if installed
        (self.workspace / "rapp_loader_agent.py").write_text("# loader\n")
        r = self._call(action="unload", name="rapp_loader_agent.py")
        self.assertIn("error", r)
        self.assertTrue((self.workspace / "rapp_loader_agent.py").exists())

    def test_loaded_lists_active_agents(self):
        self._call(action="load", name="Scout")
        self._call(action="load", name="DoubleDown")
        r = self._call(action="loaded")
        names = {item["name"] for item in r["loaded"]}
        self.assertEqual(names, {"Scout", "DoubleDown"})

    def test_loaded_excludes_basic_agent(self):
        r = self._call(action="loaded")
        for item in r["loaded"]:
            self.assertNotEqual(item["filename"], "basic_agent.py")


class TestStacks(_LoaderTestBase):

    def setUp(self):
        super().setUp()
        _make_repo(self.tmp, "stackA",
                   agents=[("scout_agent.py", "Scout"),
                           ("double_down_agent.py", "DoubleDown"),
                           ("borg_agent.py", "Borg")],
                   stacks=[
                       {"name": "discovery",
                        "description": "Scout + DoubleDown",
                        "agents": ["Scout", "DoubleDown"]},
                       {"name": "all",
                        "description": "all of them",
                        "agents": ["Scout", "DoubleDown", "Borg"]},
                   ])
        self._call(action="add_repo", path=str(self.tmp / "stackA"))

    def test_load_stack_activates_all_agents(self):
        r = self._call(action="load_stack", name="discovery")
        self.assertTrue(r["ok"])
        self.assertEqual(r["loaded_count"], 2)
        for fname in ["scout_agent.py", "double_down_agent.py"]:
            self.assertTrue((self.workspace / fname).is_symlink())

    def test_load_stack_missing_errors(self):
        r = self._call(action="load_stack", name="nope")
        self.assertIn("error", r)

    def test_unload_stack_reverses_loads(self):
        self._call(action="load_stack", name="discovery")
        r = self._call(action="unload_stack", name="discovery")
        self.assertTrue(r["ok"])
        for fname in ["scout_agent.py", "double_down_agent.py"]:
            self.assertFalse((self.workspace / fname).exists())

    def test_load_stack_partial_failure_reports(self):
        # Stack referencing a non-existent agent
        Path(self.tmp / "stackA" / "stacks" / "broken.json").write_text(
            json.dumps({"name": "broken", "agents": ["Scout", "DefinitelyMissing"]})
        )
        r = self._call(action="load_stack", name="broken")
        self.assertEqual(r["loaded_count"], 1)
        self.assertEqual(r["failed_count"], 1)
        self.assertFalse(r["ok"])


class TestUnloadAll(_LoaderTestBase):

    def test_unload_all_preserves_canonical(self):
        _make_repo(self.tmp, "stackA", agents=[("scout_agent.py", "Scout")])
        self._call(action="add_repo", path=str(self.tmp / "stackA"))
        self._call(action="load", name="Scout")
        # Plant the loader as if installed
        (self.workspace / "rapp_loader_agent.py").write_text("# loader\n")
        r = self._call(action="unload_all")
        self.assertIn("scout_agent.py", r["removed"])
        self.assertTrue((self.workspace / "basic_agent.py").exists())
        self.assertTrue((self.workspace / "rapp_loader_agent.py").exists())
        self.assertIn("basic_agent.py", r["protected"])


class TestRepoManagement(_LoaderTestBase):

    def test_add_repo_persists(self):
        _make_repo(self.tmp, "stackA", agents=[("a_agent.py", "A")])
        r = self._call(action="add_repo", path=str(self.tmp / "stackA"))
        self.assertTrue(r["ok"])
        self.assertIn(str((self.tmp / "stackA").resolve()), r["repos"])
        # Reload to verify persistence
        self.mod = _import_loader()
        self.agent = self.mod.RappLoaderAgent()
        listing = json.loads(self.agent.perform(action="list_repos"))
        paths = {r["path"] for r in listing["repos"]}
        self.assertIn(str((self.tmp / "stackA").resolve()), paths)

    def test_add_repo_rejects_non_dir(self):
        r = self._call(action="add_repo", path="/this/does/not/exist/anywhere")
        self.assertIn("error", r)

    def test_add_repo_dedupes(self):
        _make_repo(self.tmp, "stackA", agents=[("a_agent.py", "A")])
        self._call(action="add_repo", path=str(self.tmp / "stackA"))
        r = self._call(action="add_repo", path=str(self.tmp / "stackA"))
        self.assertTrue(r["ok"])
        self.assertEqual(r.get("note"), "already registered")

    def test_remove_repo(self):
        _make_repo(self.tmp, "stackA", agents=[("a_agent.py", "A")])
        self._call(action="add_repo", path=str(self.tmp / "stackA"))
        r = self._call(action="remove_repo", path=str(self.tmp / "stackA"))
        self.assertTrue(r["ok"])
        self.assertNotIn(str((self.tmp / "stackA").resolve()), r["repos"])

    def test_list_repos_reports_counts(self):
        _make_repo(self.tmp, "stackA",
                   agents=[("a_agent.py", "A"), ("b_agent.py", "B")],
                   stacks=[{"name": "s", "agents": ["A"]}])
        self._call(action="add_repo", path=str(self.tmp / "stackA"))
        r = self._call(action="list_repos")
        entry = next(x for x in r["repos"]
                     if str((self.tmp / "stackA").resolve()) == x["path"])
        self.assertEqual(entry["agent_count"], 2)
        self.assertEqual(entry["stack_count"], 1)


class TestSync(_LoaderTestBase):

    def test_sync_relinks_after_repo_move(self):
        _make_repo(self.tmp, "stackA", agents=[("scout_agent.py", "Scout")])
        self._call(action="add_repo", path=str(self.tmp / "stackA"))
        self._call(action="load", name="Scout")
        self.assertTrue((self.workspace / "scout_agent.py").is_symlink())

        # Move the stack to a new location
        import shutil
        new_loc = self.tmp / "stackA_moved"
        shutil.move(str(self.tmp / "stackA"), str(new_loc))
        # Update registry to point to new location
        self._call(action="remove_repo", path=str(self.tmp / "stackA"))
        self._call(action="add_repo", path=str(new_loc))

        r = self._call(action="sync")
        # Symlink should now point at the new location (or be reported broken if not fixable)
        self.assertTrue(r["ok"])
        link_target = os.readlink(self.workspace / "scout_agent.py")
        self.assertIn("stackA_moved", link_target)


if __name__ == "__main__":
    unittest.main()
