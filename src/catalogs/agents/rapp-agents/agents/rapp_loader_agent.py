"""RappLoader — hot-load agents from your personal RAPP agent stack repos.

The sacred kernel repo at ~/.brainstem/src/ never gets touched. The
brainstem's AGENTS_PATH is redirected to ~/.rapp/workspace/. RappLoader
manages the contents of that workspace: it symlinks agents from your
registered repos on demand, supports named "stacks" (rapplications =
bundles of agents that work together), and reflects changes immediately
because brainstem reloads agents on every request — no restart needed.

This file is the front door for a RAPP Agent Stack. Drop just this one
file into any brainstem's agents/ directory and the LLM gains the ability
to discover, load, and unload every other agent in the stack.

Default sources (configurable via add_repo / list_repos):
  - ~/rapp-agents/            (public stack)
  - ~/rapp-agents-private/    (private companion)

Each source exposes:
  agents/*_agent.py           single-file drop-in agents
  stacks/*.json               named bundles {name, description, agents:[]}

Verbs (call via natural language — the LLM picks the right action):
  catalog                     show available agents and stacks across repos
  load name=<agent>           symlink one agent into the workspace
  unload name=<agent>         remove that symlink
  loaded                      show what's currently active
  load_stack name=<stack>     load every agent in a named bundle
  unload_stack name=<stack>   reverse a stack
  unload_all                  clean workspace (canonical files preserved)
  sync                        re-resolve all symlinks (e.g. after a repo move)
  add_repo path=<dir>         register an additional source
  remove_repo path=<dir>      unregister a source
  list_repos                  show registered sources
"""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

try:
    from basic_agent import BasicAgent
except ModuleNotFoundError:
    from agents.basic_agent import BasicAgent


__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@rapp/rapp_loader_agent",
    "version": "0.1.0",
    "display_name": "RappLoader",
    "description": (
        "Hot-loads agents into the brainstem workspace from your personal "
        "RAPP agent stack repos. One file, drop it in, gain access to "
        "every other agent across registered sources via natural language."
    ),
    "author": "RAPP",
    "tags": ["loader", "stack", "rapplication", "hot-load", "drop-in", "core"],
    "category": "core",
    "quality_tier": "verified",
    "requires_env": [],
    "dependencies": ["@rapp/basic_agent"],
}


# Workspace: AGENTS_PATH target. Override via env for tests.
WORKSPACE = Path(os.environ.get(
    "RAPP_WORKSPACE", str(Path.home() / ".rapp" / "workspace"))).expanduser()

# Registered-repos config file. Override via env for tests.
REPOS_CONFIG = Path(os.environ.get(
    "RAPP_LOADER_REPOS_CONFIG",
    str(Path.home() / ".rapp" / "loader_repos.json"))).expanduser()

DEFAULT_REPOS = [
    str(Path.home() / "rapp-agents"),
    str(Path.home() / "rapp-agents-private"),
]

# Never unload these from the workspace.
CANONICAL_FILES = {"basic_agent.py", "rapp_loader_agent.py"}

_AGENT_FILE_RE = re.compile(r"^[a-z][a-z0-9_]*_agent\.py$")


# --------------------------------------------------------------------------
# Repo registry
# --------------------------------------------------------------------------

def _load_repos():
    if REPOS_CONFIG.exists():
        try:
            data = json.loads(REPOS_CONFIG.read_text())
            if isinstance(data, list):
                return [str(p) for p in data]
        except (json.JSONDecodeError, OSError):
            pass
    return [str(Path(p).expanduser()) for p in DEFAULT_REPOS]


def _save_repos(repos):
    REPOS_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    REPOS_CONFIG.write_text(json.dumps(repos, indent=2))


# --------------------------------------------------------------------------
# Catalog
# --------------------------------------------------------------------------

def _agent_friendly_name(filename):
    """scout_agent.py -> Scout. project_twin_agent.py -> ProjectTwin."""
    stem = filename[:-3] if filename.endswith(".py") else filename
    if stem.endswith("_agent"):
        stem = stem[:-len("_agent")]
    parts = [p for p in stem.split("_") if p]
    return "".join(p.capitalize() for p in parts) or stem


def _walk_repo_agents(repo_path):
    agents_dir = Path(repo_path).expanduser() / "agents"
    if not agents_dir.is_dir():
        return []
    out = []
    for f in sorted(agents_dir.iterdir()):
        if not f.is_file():
            continue
        if f.name == "basic_agent.py":
            continue
        if not _AGENT_FILE_RE.match(f.name):
            continue
        out.append({
            "name": _agent_friendly_name(f.name),
            "filename": f.name,
            "path": str(f.resolve()),
            "repo": str(Path(repo_path).expanduser().resolve()),
            "size_bytes": f.stat().st_size,
        })
    return out


def _walk_repo_stacks(repo_path):
    stacks_dir = Path(repo_path).expanduser() / "stacks"
    if not stacks_dir.is_dir():
        return []
    out = []
    for f in sorted(stacks_dir.glob("*.json")):
        try:
            data = json.loads(f.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(data, dict):
            continue
        out.append({
            "name": data.get("name", f.stem),
            "description": data.get("description", ""),
            "agents": list(data.get("agents", [])),
            "path": str(f.resolve()),
            "repo": str(Path(repo_path).expanduser().resolve()),
        })
    return out


def _catalog():
    repos = _load_repos()
    agents, stacks, missing = [], [], []
    for r in repos:
        rp = Path(r).expanduser()
        if not rp.is_dir():
            missing.append(r)
            continue
        agents.extend(_walk_repo_agents(r))
        stacks.extend(_walk_repo_stacks(r))
    return {
        "repos": repos,
        "missing_repos": missing,
        "agents": agents,
        "stacks": stacks,
        "agent_count": len(agents),
        "stack_count": len(stacks),
    }


def _resolve_agent(name_or_filename):
    """Find an agent across all repos by friendly name (case-insensitive) or filename."""
    if not name_or_filename:
        return None
    q = name_or_filename.strip()
    q_lower = q.lower()
    for cand in _catalog()["agents"]:
        if cand["filename"] == q or cand["filename"].lower() == q_lower:
            return cand
        if cand["name"].lower() == q_lower:
            return cand
    return None


def _resolve_stack(name):
    if not name:
        return None
    q = name.strip().lower()
    for s in _catalog()["stacks"]:
        if s["name"].lower() == q:
            return s
    return None


# --------------------------------------------------------------------------
# Workspace ops
# --------------------------------------------------------------------------

def _ensure_workspace():
    WORKSPACE.mkdir(parents=True, exist_ok=True)


def _load_one(name):
    cand = _resolve_agent(name)
    if not cand:
        return {"error": f"agent '{name}' not found in any registered repo",
                "hint": "Use action=catalog to see what's available."}
    _ensure_workspace()
    src = Path(cand["path"])
    if not src.exists():
        return {"error": f"source file missing: {src}"}
    dst = WORKSPACE / src.name
    was_loaded = dst.exists() or dst.is_symlink()
    if was_loaded:
        dst.unlink()
    dst.symlink_to(src)
    return {
        "ok": True,
        "loaded": cand["name"],
        "filename": src.name,
        "from_repo": cand["repo"],
        "workspace_path": str(dst),
        "replaced_existing": was_loaded,
    }


def _unload_one(name):
    # Try to resolve by friendly name; fall back to literal filename.
    cand = _resolve_agent(name)
    if cand:
        filename = cand["filename"]
    else:
        filename = name if name.endswith(".py") else (
            f"{name.lower()}_agent.py" if not name.endswith("_agent") else f"{name}.py"
        )
    if filename in CANONICAL_FILES:
        return {"error": f"refusing to unload canonical file: {filename}",
                "hint": "Canonical files (basic_agent.py, rapp_loader_agent.py) are protected."}
    dst = WORKSPACE / filename
    if not dst.exists() and not dst.is_symlink():
        return {"ok": True, "note": f"not currently loaded: {filename}", "filename": filename}
    dst.unlink()
    return {"ok": True, "unloaded": name, "filename": filename}


def _loaded():
    _ensure_workspace()
    items = []
    for f in sorted(WORKSPACE.iterdir()):
        if not f.is_file() and not f.is_symlink():
            continue
        if not f.name.endswith(".py"):
            continue
        if f.name == "basic_agent.py":
            continue
        target = None
        broken = False
        if f.is_symlink():
            target = os.readlink(f)
            broken = not Path(target).exists()
        items.append({
            "filename": f.name,
            "name": _agent_friendly_name(f.name),
            "is_symlink": f.is_symlink(),
            "target": target,
            "broken": broken,
            "is_canonical": f.name in CANONICAL_FILES,
        })
    return items


def _load_stack(name):
    s = _resolve_stack(name)
    if not s:
        return {"error": f"stack '{name}' not found in any registered repo",
                "hint": "Use action=catalog to see available stacks."}
    results = []
    for agent_name in s["agents"]:
        results.append(_load_one(agent_name))
    succeeded = [r for r in results if r.get("ok")]
    failed = [r for r in results if not r.get("ok")]
    return {
        "ok": len(failed) == 0,
        "stack": s["name"],
        "description": s["description"],
        "loaded_count": len(succeeded),
        "failed_count": len(failed),
        "results": results,
    }


def _unload_stack(name):
    s = _resolve_stack(name)
    if not s:
        return {"error": f"stack '{name}' not found"}
    results = [_unload_one(a) for a in s["agents"]]
    return {"ok": True, "stack": s["name"], "results": results}


def _unload_all():
    _ensure_workspace()
    removed, protected = [], []
    for f in WORKSPACE.iterdir():
        if not f.is_file() and not f.is_symlink():
            continue
        if not f.name.endswith(".py"):
            continue
        if f.name in CANONICAL_FILES or f.name == "basic_agent.py":
            protected.append(f.name)
            continue
        try:
            f.unlink()
            removed.append(f.name)
        except OSError:
            pass
    return {"ok": True, "removed": removed, "protected": protected}


def _sync():
    """Re-resolve every symlink by friendly name. Useful if a repo moved."""
    _ensure_workspace()
    refreshed, ok, broken = [], [], []
    for f in WORKSPACE.iterdir():
        if not f.is_symlink():
            continue
        if not f.name.endswith(".py"):
            continue
        if f.name in CANONICAL_FILES or f.name == "basic_agent.py":
            continue
        target = Path(os.readlink(f))
        if target.exists():
            ok.append(f.name)
            continue
        # Try to find replacement in current catalog
        cand = _resolve_agent(_agent_friendly_name(f.name))
        if cand:
            f.unlink()
            f.symlink_to(cand["path"])
            refreshed.append({"filename": f.name, "new_target": cand["path"]})
        else:
            broken.append(f.name)
    return {"ok": True, "still_ok": ok, "refreshed": refreshed, "broken_unfixable": broken}


# --------------------------------------------------------------------------
# Repo management
# --------------------------------------------------------------------------

def _add_repo(path):
    if not path:
        return {"error": "add_repo requires 'path'"}
    resolved = str(Path(path).expanduser().resolve())
    if not Path(resolved).is_dir():
        return {"error": f"not a directory: {resolved}"}
    repos = _load_repos()
    if resolved in repos:
        return {"ok": True, "note": "already registered", "repo": resolved, "repos": repos}
    repos.append(resolved)
    _save_repos(repos)
    return {"ok": True, "added": resolved, "repos": repos}


def _remove_repo(path):
    if not path:
        return {"error": "remove_repo requires 'path'"}
    resolved = str(Path(path).expanduser().resolve())
    repos = _load_repos()
    if resolved not in repos:
        return {"ok": True, "note": "not registered", "repo": resolved, "repos": repos}
    repos = [r for r in repos if r != resolved]
    _save_repos(repos)
    return {"ok": True, "removed": resolved, "repos": repos}


def _list_repos():
    repos = _load_repos()
    out = []
    for r in repos:
        p = Path(r).expanduser()
        out.append({
            "path": r,
            "exists": p.is_dir(),
            "agent_count": len(_walk_repo_agents(r)) if p.is_dir() else 0,
            "stack_count": len(_walk_repo_stacks(r)) if p.is_dir() else 0,
        })
    return {"repos": out, "config_path": str(REPOS_CONFIG),
            "workspace": str(WORKSPACE)}


# --------------------------------------------------------------------------
# Agent surface
# --------------------------------------------------------------------------

class RappLoaderAgent(BasicAgent):
    def __init__(self):
        self.name = "RappLoader"
        self.metadata = {
            "name": self.name,
            "description": (
                "Hot-loads agents into the brainstem workspace from your "
                "personal RAPP agent stack repos. Call this when the user "
                "wants to: discover what agents are available, load/unload "
                "an agent by name, load a named 'stack' (rapplication = "
                "bundle of agents), see what's currently loaded, or "
                "register a new repo. The brainstem reloads agents on every "
                "request, so changes take effect immediately — no restart. "
                "Default sources: ~/rapp-agents (public) and "
                "~/rapp-agents-private. Stacks live as <repo>/stacks/<name>.json. "
                "Use action=catalog when the user asks 'what agents do I "
                "have?'; action=load for 'load Scout' / 'activate "
                "DoubleDown'; action=load_stack for 'load the X stack'; "
                "action=loaded for 'what's active right now?'; "
                "action=unload_all to clean the workspace."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "catalog", "load", "unload", "loaded",
                            "load_stack", "unload_stack", "unload_all",
                            "sync", "add_repo", "remove_repo", "list_repos",
                        ],
                        "description": "Which verb to run.",
                    },
                    "name": {
                        "type": "string",
                        "description": (
                            "Agent name (for load/unload) or stack name "
                            "(for load_stack/unload_stack). Friendly name "
                            "('Scout') or filename ('scout_agent.py') both work."
                        ),
                    },
                    "path": {
                        "type": "string",
                        "description": "For add_repo/remove_repo: directory path.",
                    },
                },
                "required": ["action"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs):
        action = (kwargs.get("action") or "").strip()
        name = (kwargs.get("name") or "").strip()
        path = (kwargs.get("path") or "").strip()
        try:
            if action == "catalog":
                return json.dumps(_catalog(), indent=2)
            if action == "load":
                if not name:
                    return json.dumps({"error": "load requires 'name'"})
                return json.dumps(_load_one(name), indent=2)
            if action == "unload":
                if not name:
                    return json.dumps({"error": "unload requires 'name'"})
                return json.dumps(_unload_one(name), indent=2)
            if action == "loaded":
                return json.dumps({
                    "workspace": str(WORKSPACE),
                    "loaded": _loaded(),
                }, indent=2)
            if action == "load_stack":
                if not name:
                    return json.dumps({"error": "load_stack requires 'name'"})
                return json.dumps(_load_stack(name), indent=2)
            if action == "unload_stack":
                if not name:
                    return json.dumps({"error": "unload_stack requires 'name'"})
                return json.dumps(_unload_stack(name), indent=2)
            if action == "unload_all":
                return json.dumps(_unload_all(), indent=2)
            if action == "sync":
                return json.dumps(_sync(), indent=2)
            if action == "add_repo":
                return json.dumps(_add_repo(path), indent=2)
            if action == "remove_repo":
                return json.dumps(_remove_repo(path), indent=2)
            if action == "list_repos":
                return json.dumps(_list_repos(), indent=2)
            return json.dumps({
                "error": f"unknown action: {action}",
                "valid": [
                    "catalog", "load", "unload", "loaded",
                    "load_stack", "unload_stack", "unload_all",
                    "sync", "add_repo", "remove_repo", "list_repos",
                ],
            })
        except Exception as e:
            return json.dumps({
                "error": f"{type(e).__name__}: {e}",
                "action": action,
                "ts": datetime.now(timezone.utc).isoformat(),
            })
