"""Scout — point it somewhere and it tells you what twins to create.

Borg-for-twins. A discovery / recommendation agent. Given any target
(filesystem path, parent dir of many candidates, eventually GitHub org or
comms inbox), Scout analyzes the terrain and returns a ranked list of TWIN
CANDIDATES: kind, anchor, rationale, confidence, and a paste-ready next-step
hatch hint.

The user usually doesn't know which twins they should create in their
workspace. Scout figures it out for them and presents an ordered slate; the
user picks; hatching happens after.

Pattern matches @borg/borg_agent (HOLO): same planning-mode contract,
history persistence under .brainstem_data/.

Usage:
  Scout(mode='parent', path='~/code')   # scout every subdir of ~/code
  Scout(path='/abs/path/to/repo')       # auto-mode on one path
  Scout(mode='history')                 # show past scouts
"""

import json
import os
import re
import time
from datetime import datetime, timezone

try:
    from basic_agent import BasicAgent
except ModuleNotFoundError:
    from agents.basic_agent import BasicAgent


__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@rapp/scout_agent",
    "version": "0.1.0",
    "display_name": "Scout",
    "description": (
        "Discovers what twins to create. Point Scout at a filesystem path "
        "(one dir or a parent of many) and it returns a ranked list of twin "
        "candidates with kind, anchor, rationale, confidence, and a "
        "ready-to-run hatch hint. Borg-for-twins."
    ),
    "author": "RAPP",
    "tags": ["scout", "discovery", "twin", "recommendation", "planning", "borg"],
    "category": "core",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic_agent"],
}


_BRAINSTEM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HISTORY_PATH = os.path.join(_BRAINSTEM_DIR, ".brainstem_data", "scout_history.json")


# Project-marker file → (tech label, score points if found)
_PROJECT_MARKERS = {
    "package.json": ("Node.js", 18),
    "pyproject.toml": ("Python", 18),
    "requirements.txt": ("Python", 14),
    "setup.py": ("Python", 14),
    "Pipfile": ("Python", 14),
    "Cargo.toml": ("Rust", 18),
    "go.mod": ("Go", 18),
    "pom.xml": ("Java", 16),
    "build.gradle": ("Java/Kotlin", 16),
    "Gemfile": ("Ruby", 16),
    "composer.json": ("PHP", 16),
    "Dockerfile": ("Docker", 6),
    "docker-compose.yml": ("Docker", 5),
    "docker-compose.yaml": ("Docker", 5),
    "tsconfig.json": ("TypeScript", 8),
    "next.config.js": ("Next.js", 6),
    "vite.config.js": ("Vite", 5),
    "azuredeploy.json": ("Azure ARM", 7),
    "CMakeLists.txt": ("C/C++ (CMake)", 12),
    "Makefile": ("Make", 4),
}

_CODE_EXTS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java", ".kt",
    ".rb", ".php", ".c", ".cc", ".cpp", ".h", ".hpp", ".swift", ".m", ".mm",
}
_DOC_EXTS = {".md", ".rst", ".txt"}

_EXCLUDE_DIRS = {
    "node_modules", "venv", ".venv", "__pycache__", "dist", "build", "target",
    ".git", ".idea", ".vscode", ".brainstem", "vendor", "deps", ".pytest_cache",
}

_DEFAULT_MAX_RESULTS = 15
_HARD_MAX_RESULTS = 50
_DEFAULT_MIN_CONFIDENCE = 0.5
_WALK_DEPTH_CAP = 2
_RECENCY_WINDOW_DAYS = 90

_PLANNING_INSTRUCTIONS = (
    "ENTER PLANNING MODE. Present the candidates to the user as a numbered "
    "list with: rank, display_name, kind, confidence, one-line rationale, "
    "and the ready-to-run next_step. Group by kind if multiple kinds appear. "
    "After the list, ask exactly: 'Which twins should I hatch? Give numbers "
    "or say all.' Do NOT hatch anything until the user picks. If no candidate "
    "has confidence ≥ 0.5, say so plainly and suggest the user point Scout "
    "elsewhere or lower min_confidence."
)


# --------------------------------------------------------------------------
# History persistence
# --------------------------------------------------------------------------

def _history_path():
    return _HISTORY_PATH


def _load_history():
    path = _history_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save_history(history):
    path = _history_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


def _record_scout(target, results):
    history = _load_history()
    history.append({
        "id": len(history) + 1,
        "target": target,
        "mode": results.get("mode"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "candidate_count": len(results.get("candidates", [])),
        "ranked_top": [c.get("name") for c in results.get("candidates", [])[:5]],
    })
    _save_history(history)


# --------------------------------------------------------------------------
# Scanning + scoring
# --------------------------------------------------------------------------

def _slug(s):
    return re.sub(r"[^A-Za-z0-9]+", "-", s.strip().lower()).strip("-") or "twin"


def _has_git(path):
    return os.path.isdir(os.path.join(path, ".git"))


def _scan_dir_signals(path):
    """Single walk: gather all signals + freshest mtime in one pass."""
    signals = {
        "tech": [],
        "marker_files": [],
        "code_file_count": 0,
        "doc_file_count": 0,
        "total_files": 0,
        "has_readme": False,
        "has_src_dir": False,
        "has_git": _has_git(path),
        "latest_mtime": 0,
    }
    try:
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs
                       if d not in _EXCLUDE_DIRS and not d.startswith(".")]
            depth = root.replace(path, "").count(os.sep)
            if root == path:
                for d in dirs:
                    if d.lower() in ("src", "lib"):
                        signals["has_src_dir"] = True
            for fname in files:
                signals["total_files"] += 1
                lower = fname.lower()
                if lower.startswith("readme"):
                    signals["has_readme"] = True
                if fname in _PROJECT_MARKERS:
                    tech, _w = _PROJECT_MARKERS[fname]
                    if tech not in signals["tech"]:
                        signals["tech"].append(tech)
                    signals["marker_files"].append(fname)
                _, ext = os.path.splitext(fname)
                if ext in _CODE_EXTS:
                    signals["code_file_count"] += 1
                elif ext in _DOC_EXTS:
                    signals["doc_file_count"] += 1
                try:
                    m = os.path.getmtime(os.path.join(root, fname))
                    if m > signals["latest_mtime"]:
                        signals["latest_mtime"] = m
                except OSError:
                    pass
            if depth >= _WALK_DEPTH_CAP:
                dirs[:] = []
    except OSError:
        pass
    return signals


def _recency_score(latest_mtime, days=_RECENCY_WINDOW_DAYS):
    if not latest_mtime:
        return 0
    age_days = (time.time() - latest_mtime) / 86400
    if age_days >= days:
        return 0
    return max(0, int(15 * (1 - age_days / days)))


def _score_candidate(signals):
    score = 0
    reasons = []
    if signals["has_git"]:
        score += 30
        reasons.append("git repo")
    if signals["has_readme"]:
        score += 12
        reasons.append("README present")
    if signals["has_src_dir"]:
        score += 6
        reasons.append("src/lib directory")
    if signals["code_file_count"] >= 1:
        bump = min(15, signals["code_file_count"])
        score += bump
        reasons.append(f"{signals['code_file_count']} code files")
    if signals["doc_file_count"] >= 2:
        score += 4
        reasons.append(f"{signals['doc_file_count']} docs")
    marker_pts = 0
    for fname in signals["marker_files"]:
        if fname in _PROJECT_MARKERS:
            marker_pts += _PROJECT_MARKERS[fname][1]
    if marker_pts:
        score += min(30, marker_pts)
        reasons.append("tech: " + ", ".join(signals["tech"]))
    if signals["total_files"] >= 10:
        score += 5
        reasons.append(f"{signals['total_files']} files")
    return min(100, score), reasons


def _build_candidate(path, kind="project", name=None):
    abspath = os.path.abspath(os.path.expanduser(path))
    if not os.path.isdir(abspath):
        return None
    signals = _scan_dir_signals(abspath)
    base_score, reasons = _score_candidate(signals)
    recency = _recency_score(signals["latest_mtime"])
    if recency:
        reasons.append(f"recent activity (+{recency} pts)")
    score = min(100, base_score + recency)
    display_name = name or os.path.basename(abspath.rstrip(os.sep)) or "twin"
    slug = _slug(display_name)
    return {
        "name": slug,
        "display_name": display_name,
        "kind": kind,
        "anchor": {"type": "path", "value": abspath},
        "confidence": round(score / 100, 2),
        "score": score,
        "tech": signals["tech"],
        "signals": {
            "has_git": signals["has_git"],
            "has_readme": signals["has_readme"],
            "has_src_dir": signals["has_src_dir"],
            "code_file_count": signals["code_file_count"],
            "doc_file_count": signals["doc_file_count"],
            "total_files": signals["total_files"],
            "marker_files": signals["marker_files"][:8],
        },
        "rationale": "; ".join(reasons) if reasons else "no strong signals",
        "hatch_args": {
            "action": "hatch",
            "kind": kind,
            "project_path": abspath,
            "name": slug,
        },
        "next_step": (
            f"Twin(action='hatch', kind='{kind}', "
            f"project_path='{abspath}', name='{slug}')"
        ),
    }


def _scout_dir(path):
    c = _build_candidate(path, kind="project")
    return [c] if c else []


def _scout_parent(parent_path):
    abspath = os.path.abspath(os.path.expanduser(parent_path))
    if not os.path.isdir(abspath):
        return []
    candidates = []
    try:
        for entry in sorted(os.listdir(abspath)):
            full = os.path.join(abspath, entry)
            if not os.path.isdir(full):
                continue
            if (entry in _EXCLUDE_DIRS
                    or entry.startswith(".")
                    or entry.startswith("_")):
                continue
            c = _build_candidate(full, kind="project", name=entry)
            if c:
                candidates.append(c)
    except OSError:
        return []
    return candidates


# --------------------------------------------------------------------------
# Agent
# --------------------------------------------------------------------------

class ScoutAgent(BasicAgent):
    def __init__(self):
        self.name = "Scout"
        self.metadata = {
            "name": self.name,
            "description": (
                "Discovers what twins to create. Borg-for-twins. Point at a "
                "filesystem path (one dir or a parent-of-many) and Scout returns "
                "a ranked list of twin candidates with kind, anchor, rationale, "
                "confidence (0..1), hatch_args, and a paste-ready next_step. Use "
                "this BEFORE proposing hatches — the user usually doesn't know "
                "what twins they should create. After receiving Scout's report, "
                "you MUST enter planning mode and present the candidates as a "
                "numbered list; never hatch automatically. Modes: mode='dir' "
                "scouts one path. mode='parent' scouts every subdir. mode='auto' "
                "(default) picks based on subdir count. mode='history' lists "
                "past scouts. v1 emits kind=project only; the abstraction "
                "supports more kinds for future modes."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "mode": {
                        "type": "string",
                        "enum": ["auto", "dir", "parent", "history"],
                        "description": (
                            "auto (default): parent if ≥3 subdirs, else dir. "
                            "dir: scout this path. "
                            "parent: scout every subdir of this path. "
                            "history: list past scouts."
                        ),
                    },
                    "path": {
                        "type": "string",
                        "description": "Path to scout (absolute or ~-expanded).",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": (
                            f"Cap on returned candidates. Default "
                            f"{_DEFAULT_MAX_RESULTS}, hard cap {_HARD_MAX_RESULTS}."
                        ),
                    },
                    "min_confidence": {
                        "type": "number",
                        "description": (
                            f"Drop candidates below this (0..1). Default "
                            f"{_DEFAULT_MIN_CONFIDENCE}."
                        ),
                    },
                    "kind_hint": {
                        "type": "string",
                        "description": (
                            "Filter candidates to a single kind. v1 only emits "
                            "'project'; future modes will support more."
                        ),
                    },
                },
                "required": [],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs):
        mode = (kwargs.get("mode") or "auto").lower()

        if mode == "history":
            hist = _load_history()
            return json.dumps({
                "total": len(hist),
                "entries": hist[-20:],
            })

        path = (kwargs.get("path") or "").strip()
        if not path:
            return json.dumps({
                "error": "Scout requires a 'path' to investigate.",
                "usage": (
                    "Scout(mode='parent', path='~/code')  OR  "
                    "Scout(path='/abs/path/to/repo')"
                ),
            })
        abspath = os.path.abspath(os.path.expanduser(path))
        if not os.path.isdir(abspath):
            return json.dumps({
                "error": f"Not a directory: {abspath}",
                "hint": "Path must be an existing directory.",
            })

        if mode not in ("auto", "dir", "parent"):
            return json.dumps({
                "error": f"unknown mode: {mode}",
                "valid": ["auto", "dir", "parent", "history"],
            })

        try:
            max_results = int(kwargs.get("max_results", _DEFAULT_MAX_RESULTS))
        except (TypeError, ValueError):
            max_results = _DEFAULT_MAX_RESULTS
        max_results = max(1, min(_HARD_MAX_RESULTS, max_results))

        try:
            min_conf = float(kwargs.get("min_confidence", _DEFAULT_MIN_CONFIDENCE))
        except (TypeError, ValueError):
            min_conf = _DEFAULT_MIN_CONFIDENCE
        min_conf = max(0.0, min(1.0, min_conf))

        kind_hint = (kwargs.get("kind_hint") or "").strip().lower() or None

        if mode == "auto":
            try:
                subdirs = [e for e in os.listdir(abspath)
                           if os.path.isdir(os.path.join(abspath, e))
                           and not e.startswith(".")
                           and e not in _EXCLUDE_DIRS]
            except OSError:
                subdirs = []
            mode = "parent" if len(subdirs) >= 3 else "dir"

        candidates = _scout_dir(abspath) if mode == "dir" else _scout_parent(abspath)

        if kind_hint:
            candidates = [c for c in candidates if c["kind"] == kind_hint]

        kept = [c for c in candidates if c["confidence"] >= min_conf]
        dropped_low_confidence = len(candidates) - len(kept)

        kept.sort(key=lambda c: (-c["score"], c["name"]))
        ranked = kept[:max_results]

        results = {
            "ok": True,
            "mode": mode,
            "target": abspath,
            "candidates": ranked,
            "scanned_count": len(candidates),
            "kept_count": len(ranked),
            "dropped_low_confidence": dropped_low_confidence,
            "min_confidence": min_conf,
            "planning_mode": {
                "instructions": _PLANNING_INSTRUCTIONS,
            },
        }
        _record_scout(abspath, results)
        return json.dumps(results, indent=2)
