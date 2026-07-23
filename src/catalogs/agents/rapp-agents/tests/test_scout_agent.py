"""Tests for agents/scout_agent.py — twin discovery / recommendation agent."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
AGENTS_DIR = REPO_ROOT / "agents"
sys.path.insert(0, str(AGENTS_DIR))

import scout_agent as scout_module  # noqa: E402
from scout_agent import (  # noqa: E402
    _DEFAULT_MAX_RESULTS,
    _DEFAULT_MIN_CONFIDENCE,
    _HARD_MAX_RESULTS,
    ScoutAgent,
)
from basic_agent import BasicAgent  # noqa: E402


# Module-level isolation: redirect history file to a tmpfile so tests don't
# pollute .brainstem_data/scout_history.json.
_orig_history_path = None
_tmphist_file = None


def setUpModule():
    global _orig_history_path, _tmphist_file
    _orig_history_path = scout_module._HISTORY_PATH
    _tmphist_file = tempfile.NamedTemporaryFile(
        prefix="scout_history_test_", suffix=".json", delete=False
    )
    _tmphist_file.close()
    # Start clean — _load_history treats nonexistent as empty
    os.unlink(_tmphist_file.name)
    scout_module._HISTORY_PATH = _tmphist_file.name


def tearDownModule():
    scout_module._HISTORY_PATH = _orig_history_path
    if _tmphist_file and os.path.exists(_tmphist_file.name):
        os.unlink(_tmphist_file.name)


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

def _touch(path, content=""):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(content)


def _make_strong_node_project(root, name):
    d = Path(root) / name
    (d / "src").mkdir(parents=True, exist_ok=True)
    (d / ".git").mkdir(parents=True, exist_ok=True)
    _touch(d / "README.md", "# project\n")
    _touch(d / "package.json", '{"name":"x"}')
    _touch(d / "tsconfig.json", "{}")
    _touch(d / "src" / "index.ts", "console.log(1);\n")
    _touch(d / "src" / "util.ts", "export {};\n")
    return d


def _make_python_project(root, name):
    d = Path(root) / name
    (d / ".git").mkdir(parents=True, exist_ok=True)
    _touch(d / "pyproject.toml", "[project]\nname='x'\n")
    _touch(d / "README.md", "# py\n")
    _touch(d / "main.py", "print('hi')\n")
    _touch(d / "util.py", "x = 1\n")
    return d


def _make_weak_dir(root, name):
    d = Path(root) / name
    d.mkdir(parents=True, exist_ok=True)
    _touch(d / "notes.txt", "hello")
    return d


# --------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------

class TestScoutMetadata(unittest.TestCase):

    def setUp(self):
        self.agent = ScoutAgent()

    def test_extends_basic_agent(self):
        self.assertIsInstance(self.agent, BasicAgent)

    def test_name(self):
        self.assertEqual(self.agent.name, "Scout")

    def test_metadata_required_fields(self):
        m = self.agent.metadata
        self.assertEqual(m["name"], "Scout")
        self.assertIn("description", m)
        self.assertIn("parameters", m)

    def test_modes_enum(self):
        modes = self.agent.metadata["parameters"]["properties"]["mode"]["enum"]
        self.assertEqual(set(modes), {"auto", "dir", "parent", "history"})

    def test_known_optional_params(self):
        props = self.agent.metadata["parameters"]["properties"]
        for key in ["mode", "path", "max_results", "min_confidence", "kind_hint"]:
            self.assertIn(key, props)

    def test_to_tool_shape(self):
        tool = self.agent.to_tool()
        self.assertEqual(tool["type"], "function")
        self.assertEqual(tool["function"]["name"], "Scout")


class TestScoutInputValidation(unittest.TestCase):

    def setUp(self):
        self.agent = ScoutAgent()

    def _call(self, **kw):
        return json.loads(self.agent.perform(**kw))

    def test_missing_path_errors(self):
        r = self._call()
        self.assertIn("error", r)

    def test_blank_path_errors(self):
        r = self._call(path="   ")
        self.assertIn("error", r)

    def test_nonexistent_path_errors(self):
        r = self._call(path="/this/definitely/does/not/exist/anywhere/xyz")
        self.assertIn("error", r)

    def test_unknown_mode_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = self._call(mode="bogus", path=tmp)
            self.assertIn("error", r)


class TestScoutDirMode(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp_obj = tempfile.TemporaryDirectory()
        cls.tmp = cls.tmp_obj.name
        cls.strong = _make_strong_node_project(cls.tmp, "alpha")
        cls.python = _make_python_project(cls.tmp, "beta")
        cls.weak = _make_weak_dir(cls.tmp, "gamma")

    @classmethod
    def tearDownClass(cls):
        cls.tmp_obj.cleanup()

    def setUp(self):
        self.agent = ScoutAgent()

    def _call(self, **kw):
        return json.loads(self.agent.perform(**kw))

    def test_dir_mode_returns_single_candidate(self):
        r = self._call(mode="dir", path=str(self.strong))
        self.assertTrue(r["ok"])
        self.assertEqual(len(r["candidates"]), 1)

    def test_strong_candidate_high_confidence(self):
        r = self._call(mode="dir", path=str(self.strong))
        self.assertGreater(r["candidates"][0]["confidence"], 0.5)

    def test_anchor_is_path_type(self):
        r = self._call(mode="dir", path=str(self.strong))
        a = r["candidates"][0]["anchor"]
        self.assertEqual(a["type"], "path")
        self.assertEqual(a["value"], str(self.strong))

    def test_kind_defaults_to_project(self):
        r = self._call(mode="dir", path=str(self.strong))
        self.assertEqual(r["candidates"][0]["kind"], "project")

    def test_node_tech_detected(self):
        r = self._call(mode="dir", path=str(self.strong))
        techs = r["candidates"][0]["tech"]
        self.assertIn("Node.js", techs)
        self.assertIn("TypeScript", techs)

    def test_python_tech_detected(self):
        r = self._call(mode="dir", path=str(self.python))
        self.assertIn("Python", r["candidates"][0]["tech"])

    def test_hatch_args_present_and_structured(self):
        r = self._call(mode="dir", path=str(self.strong))
        h = r["candidates"][0]["hatch_args"]
        self.assertEqual(h["action"], "hatch")
        self.assertEqual(h["kind"], "project")
        self.assertEqual(h["project_path"], str(self.strong))

    def test_next_step_string_paste_ready(self):
        r = self._call(mode="dir", path=str(self.strong))
        ns = r["candidates"][0]["next_step"]
        self.assertIn("Twin(", ns)
        self.assertIn("hatch", ns)
        self.assertIn(str(self.strong), ns)

    def test_planning_instructions_present(self):
        r = self._call(mode="dir", path=str(self.strong))
        self.assertIn("instructions", r["planning_mode"])
        self.assertIn("PLANNING MODE", r["planning_mode"]["instructions"])

    def test_weak_dir_filtered_at_default_threshold(self):
        r = self._call(mode="dir", path=str(self.weak))
        self.assertEqual(r["kept_count"], 0)
        self.assertGreaterEqual(r["dropped_low_confidence"], 1)

    def test_weak_dir_visible_with_low_threshold(self):
        r = self._call(mode="dir", path=str(self.weak), min_confidence=0.0)
        self.assertEqual(r["kept_count"], 1)


class TestScoutParentMode(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp_obj = tempfile.TemporaryDirectory()
        cls.tmp = cls.tmp_obj.name
        _make_strong_node_project(cls.tmp, "alpha")
        _make_python_project(cls.tmp, "beta")
        _make_weak_dir(cls.tmp, "gamma")
        _make_weak_dir(cls.tmp, "node_modules")  # excluded
        _make_weak_dir(cls.tmp, ".hidden")       # excluded
        _make_weak_dir(cls.tmp, "_archive")      # excluded
        _make_weak_dir(cls.tmp, "__pycache__")   # excluded

    @classmethod
    def tearDownClass(cls):
        cls.tmp_obj.cleanup()

    def setUp(self):
        self.agent = ScoutAgent()

    def _call(self, **kw):
        return json.loads(self.agent.perform(**kw))

    def test_parent_finds_strong_candidates(self):
        r = self._call(mode="parent", path=self.tmp, min_confidence=0.0)
        names = {c["name"] for c in r["candidates"]}
        self.assertIn("alpha", names)
        self.assertIn("beta", names)

    def test_parent_skips_excluded_dirs(self):
        r = self._call(mode="parent", path=self.tmp, min_confidence=0.0)
        names = {c["name"] for c in r["candidates"]}
        for excluded in {"node-modules", "node_modules", "pycache", "__pycache__"}:
            self.assertNotIn(excluded, names)

    def test_parent_skips_hidden_dirs(self):
        r = self._call(mode="parent", path=self.tmp, min_confidence=0.0)
        names = {c["name"] for c in r["candidates"]}
        self.assertNotIn(".hidden", names)
        self.assertNotIn("hidden", names)

    def test_parent_skips_underscore_prefix(self):
        r = self._call(mode="parent", path=self.tmp, min_confidence=0.0)
        names = {c["name"] for c in r["candidates"]}
        self.assertNotIn("_archive", names)
        self.assertNotIn("archive", names)

    def test_results_ranked_descending_by_score(self):
        r = self._call(mode="parent", path=self.tmp, min_confidence=0.0)
        scores = [c["score"] for c in r["candidates"]]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_min_confidence_filter(self):
        r = self._call(mode="parent", path=self.tmp, min_confidence=0.9)
        for c in r["candidates"]:
            self.assertGreaterEqual(c["confidence"], 0.9)

    def test_max_results_caps_returned_list(self):
        r = self._call(mode="parent", path=self.tmp, max_results=1, min_confidence=0.0)
        self.assertLessEqual(len(r["candidates"]), 1)

    def test_max_results_hard_capped(self):
        r = self._call(mode="parent", path=self.tmp, max_results=9999, min_confidence=0.0)
        self.assertLessEqual(len(r["candidates"]), _HARD_MAX_RESULTS)

    def test_kind_hint_filters(self):
        r = self._call(mode="parent", path=self.tmp, kind_hint="person", min_confidence=0.0)
        # v1 only emits project — kind=person should filter to empty
        self.assertEqual(r["kept_count"], 0)


class TestScoutAutoMode(unittest.TestCase):

    def setUp(self):
        self.tmp_obj = tempfile.TemporaryDirectory()
        self.tmp = self.tmp_obj.name
        self.agent = ScoutAgent()

    def tearDown(self):
        self.tmp_obj.cleanup()

    def _call(self, **kw):
        return json.loads(self.agent.perform(**kw))

    def test_auto_chooses_parent_when_many_subdirs(self):
        for n in ["a", "b", "c", "d"]:
            _make_strong_node_project(self.tmp, n)
        r = self._call(mode="auto", path=self.tmp, min_confidence=0.0)
        self.assertEqual(r["mode"], "parent")

    def test_auto_chooses_dir_when_few_subdirs(self):
        _make_strong_node_project(self.tmp, "only")
        r = self._call(mode="auto", path=self.tmp, min_confidence=0.0)
        self.assertEqual(r["mode"], "dir")


class TestScoutHistory(unittest.TestCase):

    def setUp(self):
        self.agent = ScoutAgent()

    def test_history_mode_returns_envelope(self):
        r = json.loads(self.agent.perform(mode="history"))
        self.assertIn("total", r)
        self.assertIn("entries", r)
        self.assertIsInstance(r["entries"], list)

    def test_history_grows_after_scout(self):
        before = json.loads(self.agent.perform(mode="history"))["total"]
        with tempfile.TemporaryDirectory() as tmp:
            _make_strong_node_project(tmp, "alpha")
            self.agent.perform(mode="dir", path=str(Path(tmp) / "alpha"))
        after = json.loads(self.agent.perform(mode="history"))["total"]
        self.assertEqual(after, before + 1)


class TestScoutDefaults(unittest.TestCase):

    def test_default_min_confidence(self):
        self.assertEqual(_DEFAULT_MIN_CONFIDENCE, 0.5)

    def test_default_max_results(self):
        self.assertEqual(_DEFAULT_MAX_RESULTS, 15)

    def test_hard_max_results(self):
        self.assertEqual(_HARD_MAX_RESULTS, 50)


if __name__ == "__main__":
    unittest.main()
