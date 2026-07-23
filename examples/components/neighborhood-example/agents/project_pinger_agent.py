"""customer_project_pinger_agent — cross-team + personal portfolio snapshot.

Two views, one agent. Per the this neighborhood's architecture:

  - Repo holds BONES: each SE has ses/<handle>/projects.json with
    sanitized project slugs + status enums + last-touched. Visible to
    the whole team.
  - Local device holds SUBSTANCE: ~/.bwat-data/<handle>/customers/<slug>/
    holds the actual customer data (status.json, outcome.md, notes, etc.).
    NEVER in the repo.

The pinger reads both:
  - Team view (`team_status`, `team_blockers`) — walks ses/*/projects.json
    in the cloned repo. Sees everyone's project counts + statuses
    without seeing customer data.
  - Personal view (`status`, `find_blockers`, `stale`) — walks
    ~/.bwat-data/<handle>/customers/. Deep view of YOUR customers.

Auto-discovers handle (gh api user) + workspace (NB_WORKSPACE env var
or ~/.brainstem/neighborhoods.json subscription).

Actions:
  status            — personal portfolio snapshot (your local customers)
  team_status       — team-wide snapshot (repo ses/*/projects.json)
  find_blockers     — personal projects flagged with non-empty blockers
  team_blockers     — team-wide blockers across all SEs
  stale             — personal projects untouched > N days
  list_projects     — bare list of your project slugs
  get_status        — agent readiness probe
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone, timedelta

try:
    from agents.basic_agent import BasicAgent
except ImportError:
    from basic_agent import BasicAgent


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(s: str):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def _gh_handle() -> str | None:
    p = subprocess.run(
        ["gh", "api", "user", "--jq", ".login"],
        capture_output=True, text=True,
    )
    if p.returncode == 0 and p.stdout.strip():
        return p.stdout.strip()
    return None


def _resolve_workspace() -> str | None:
    env = os.environ.get("NB_WORKSPACE")
    if env and os.path.isdir(os.path.expanduser(env)):
        return os.path.expanduser(env)
    sub = os.path.expanduser("~/.brainstem/neighborhoods.json")
    if os.path.exists(sub):
        try:
            data = json.load(open(sub))
            for s in data.get("subscribed", []):
                wp = s.get("workspace_path")
                if wp and os.path.isdir(wp):
                    return wp
        except Exception:
            pass
    fallback = os.path.expanduser("~/brainstem-workspace")
    if os.path.isdir(fallback):
        # Look for a child with a customers/ or ses/ dir
        for entry in os.listdir(fallback):
            cand = os.path.join(fallback, entry)
            if os.path.isdir(os.path.join(cand, "ses")):
                return cand
    return None


def _local_data_dir(handle: str) -> str:
    base = os.path.expanduser(
        os.environ.get("NB_DATA_HOME", "~/.brainstem/neighborhoods/__SLUG__")
    )
    return os.path.join(base, handle, "customers")


def _read_local_project(project_dir: str) -> dict:
    info: dict = {"slug": os.path.basename(project_dir),
                  "path": project_dir, "files_present": []}
    for fname in ("status.json", "outcome.md", "intake.md",
                   "validations.md", "notes.md"):
        if os.path.isfile(os.path.join(project_dir, fname)):
            info["files_present"].append(fname)
    sp = os.path.join(project_dir, "status.json")
    if os.path.isfile(sp):
        try:
            info.update(json.load(open(sp)))
        except Exception:
            info["status_parse_error"] = True
    return info


def _read_se_projects(repo_root: str) -> dict[str, dict]:
    """Returns {se_handle: parsed-projects.json}."""
    ses_dir = os.path.join(repo_root, "ses")
    if not os.path.isdir(ses_dir):
        return {}
    out: dict[str, dict] = {}
    for entry in sorted(os.listdir(ses_dir)):
        full = os.path.join(ses_dir, entry)
        pj = os.path.join(full, "projects.json")
        if os.path.isdir(full) and os.path.isfile(pj):
            try:
                out[entry] = json.load(open(pj))
            except Exception:
                out[entry] = {"_parse_error": True}
    return out


class ProjectPingerAgent(BasicAgent):
    metadata = {
        "name": "ProjectPinger",
        "description": (
            "Portfolio snapshots across the this neighborhood's workflow. "
            "TEAM view walks the repo's ses/*/projects.json (sanitized "
            "slugs + status only — no customer data). PERSONAL view "
            "walks ~/.bwat-data/<your-handle>/customers/ (your local-"
            "only deep view). Run at start of day or before a standup."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["status", "team_status", "find_blockers",
                             "team_blockers", "stale", "list_projects",
                             "get_status"],
                },
                "handle": {
                    "type": "string",
                    "description": "Override auto-detected GitHub handle.",
                },
                "stale_days": {
                    "type": "integer",
                    "description": "For stale action: cutoff in days (default 7).",
                },
            },
            "required": ["action"],
        },
    }

    def __init__(self):
        self.name = "ProjectPinger"

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "get_status")
        handle = (kwargs.get("handle") or "").strip() or _gh_handle()
        ws = _resolve_workspace()

        if action == "get_status":
            local_dir = _local_data_dir(handle) if handle else None
            return json.dumps({
                "ok": True, "agent": self.name,
                "handle": handle,
                "workspace": ws,
                "local_data_dir": local_dir,
                "local_data_present": (
                    os.path.isdir(local_dir) if local_dir else False
                ),
                "actions": [
                    "status", "team_status", "find_blockers",
                    "team_blockers", "stale", "list_projects", "get_status",
                ],
            })

        if action in ("team_status", "team_blockers"):
            if not ws:
                return json.dumps({"ok": False,
                                    "error": "No workspace; run Joiner first."})
            se_data = _read_se_projects(ws)
            if action == "team_status":
                summary = []
                for se, payload in se_data.items():
                    projects = payload.get("projects", [])
                    by_status: dict = {}
                    for p in projects:
                        s = (p.get("status") or "(unknown)") if isinstance(p, dict) else "(unknown)"
                        by_status[s] = by_status.get(s, 0) + 1
                    summary.append({
                        "se": se, "project_count": len(projects),
                        "by_status": by_status,
                    })
                return json.dumps({
                    "ok": True, "scope": "team", "ses_count": len(se_data),
                    "per_se": summary,
                }, indent=2)
            # team_blockers
            blocked: list[dict] = []
            for se, payload in se_data.items():
                for p in payload.get("projects", []):
                    if isinstance(p, dict) and p.get("blockers"):
                        blocked.append({"se": se, "slug": p.get("slug"),
                                         "blockers": p.get("blockers"),
                                         "last_touched": p.get("last_touched")})
            return json.dumps({
                "ok": True, "scope": "team",
                "blocked_count": len(blocked), "blocked": blocked,
            }, indent=2)

        # personal actions
        if not handle:
            return json.dumps({
                "ok": False,
                "error": "Couldn't detect handle. Pass handle='your-github-username'.",
            })
        local_dir = _local_data_dir(handle)
        if not os.path.isdir(local_dir):
            return json.dumps({
                "ok": False,
                "error": (
                    f"No local data dir at {local_dir}. Run SesWorkspaceInit "
                    f"first to set it up."
                ),
            })

        projects = []
        for entry in sorted(os.listdir(local_dir)):
            full = os.path.join(local_dir, entry)
            if os.path.isdir(full) and not entry.startswith("."):
                projects.append(_read_local_project(full))

        if action == "list_projects":
            return json.dumps({
                "ok": True, "scope": "personal", "handle": handle,
                "count": len(projects),
                "projects": [p["slug"] for p in projects],
            }, indent=2)

        if action == "find_blockers":
            blocked = [p for p in projects if p.get("blockers")]
            return json.dumps({
                "ok": True, "scope": "personal", "handle": handle,
                "blocked_count": len(blocked),
                "blocked": [{"slug": p["slug"],
                             "blockers": p.get("blockers"),
                             "owner": p.get("owner"),
                             "last_touched": p.get("last_touched")}
                            for p in blocked],
            }, indent=2)

        if action == "stale":
            days = int(kwargs.get("stale_days") or 7)
            cutoff = _now() - timedelta(days=days)
            stale = []
            for p in projects:
                ts = _parse_iso(p.get("last_touched", ""))
                if ts and ts < cutoff:
                    stale.append({"slug": p["slug"],
                                   "last_touched": p.get("last_touched"),
                                   "days_since": (_now() - ts).days})
            return json.dumps({
                "ok": True, "scope": "personal", "handle": handle,
                "cutoff_days": days, "stale_count": len(stale),
                "stale": stale,
            }, indent=2)

        # status — personal full snapshot
        by_status: dict = {}
        for p in projects:
            s = p.get("status") or "(unknown)"
            by_status[s] = by_status.get(s, 0) + 1
        return json.dumps({
            "ok": True, "scope": "personal", "handle": handle,
            "local_data_dir": local_dir,
            "total_projects": len(projects),
            "by_status": by_status,
            "projects": [{"slug": p["slug"], "status": p.get("status"),
                          "owner": p.get("owner"),
                          "last_touched": p.get("last_touched"),
                          "files_present": p.get("files_present", []),
                          "blockers": p.get("blockers")}
                         for p in projects],
        }, indent=2)
