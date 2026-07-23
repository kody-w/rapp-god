"""bwat_intake_agent — capture raw ideas, log solutions, escalate to owner.

Bill Whalen Agent Team (BWAT) — Intake / Logger persona. The first
touchpoint for any new idea. Decides: needs framing? Needs Bill?
Needs nothing — just log and let it sit?

Single-file RAPP agent. Append-only local backlog at
.brainstem_data/bwat_intake.jsonl so the operator's own brainstem
holds the canonical record (no GitHub round-trip required for the
local iteration loop).

Actions:
  log_idea         — append a raw idea to the local backlog
  log_solution     — append a solution-shaped artifact to the backlog
  flag_for_owner   — mark an existing entry as needs-bill / needs-owner
  get_backlog      — list current open backlog entries (newest first)
  get_status       — agent readiness probe
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone

try:
    from agents.basic_agent import BasicAgent
except ImportError:
    from basic_agent import BasicAgent


def _now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _data_path() -> str:
    base = os.environ.get(
        "BRAINSTEM_DATA",
        os.path.join(os.path.expanduser("~"), ".brainstem", ".brainstem_data"),
    )
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "bwat_intake.jsonl")


def _append(entry: dict) -> None:
    with open(_data_path(), "a") as f:
        f.write(json.dumps(entry) + "\n")


def _read_all() -> list[dict]:
    p = _data_path()
    if not os.path.exists(p):
        return []
    out = []
    with open(p) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    return out


class BwatIntakeAgent(BasicAgent):
    metadata = {
        "name": "BwatIntake",
        "description": (
            "Captures raw ideas and solution drafts into the team's local "
            "backlog. Flags items that need the human owner (Bill, by "
            "default). Use first whenever a new ask lands and you need to "
            "register it without losing it."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["log_idea", "log_solution", "flag_for_owner",
                             "get_backlog", "get_status"],
                },
                "title": {"type": "string"},
                "body":  {"type": "string"},
                "owner_handle": {
                    "type": "string",
                    "description": "Who to flag for (default: 'bill').",
                },
                "entry_id": {
                    "type": "string",
                    "description": "ID of an existing entry (for flag_for_owner).",
                },
                "limit": {
                    "type": "integer",
                    "description": "How many backlog entries to return (default 20).",
                },
            },
            "required": ["action"],
        },
    }

    def __init__(self):
        self.name = "BwatIntake"

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "get_status")

        if action == "get_status":
            entries = _read_all()
            return json.dumps({
                "ok": True, "agent": self.name,
                "backlog_size": len(entries),
                "data_file": _data_path(),
                "actions": [
                    "log_idea", "log_solution", "flag_for_owner",
                    "get_backlog", "get_status",
                ],
            })

        if action == "log_idea":
            return self._log("idea", kwargs)
        if action == "log_solution":
            return self._log("solution", kwargs)
        if action == "flag_for_owner":
            return self._flag(kwargs)
        if action == "get_backlog":
            return self._dump(int(kwargs.get("limit") or 20))

        return json.dumps({"ok": False, "error": f"unknown action: {action}"})

    def _log(self, kind: str, kwargs: dict) -> str:
        title = (kwargs.get("title") or "").strip()
        body = (kwargs.get("body") or "").strip()
        if not title:
            return json.dumps({"ok": False, "error": "title required"})
        entry = {
            "id": uuid.uuid4().hex[:12],
            "kind": kind,
            "title": title,
            "body": body,
            "logged_at": _now_iso(),
            "flagged_for": None,
            "status": "open",
        }
        _append(entry)
        return json.dumps({
            "ok": True,
            "logged": entry,
            "next_step": (
                "Run BwatOutcomeFramer.frame_outcome on this id to turn it "
                "into a structured outcome statement before any build."
            ),
        }, indent=2)

    def _flag(self, kwargs: dict) -> str:
        entry_id = (kwargs.get("entry_id") or "").strip()
        owner = (kwargs.get("owner_handle") or "bill").strip()
        if not entry_id:
            return json.dumps({"ok": False, "error": "entry_id required"})
        # Append a flag event (jsonl is append-only; query layer reconciles)
        flag = {
            "id": uuid.uuid4().hex[:12],
            "kind": "flag",
            "ref_id": entry_id,
            "flagged_for": owner,
            "logged_at": _now_iso(),
        }
        _append(flag)
        return json.dumps({"ok": True, "flagged": flag}, indent=2)

    def _dump(self, limit: int) -> str:
        all_entries = _read_all()
        # Reconcile flags: latest flag-for wins per ref_id
        flags = {e["ref_id"]: e["flagged_for"]
                 for e in all_entries if e.get("kind") == "flag"}
        items = [e for e in all_entries if e.get("kind") in ("idea", "solution")]
        for e in items:
            if e["id"] in flags:
                e["flagged_for"] = flags[e["id"]]
        items.sort(key=lambda e: e.get("logged_at", ""), reverse=True)
        return json.dumps({
            "ok": True,
            "count": len(items),
            "showing": min(limit, len(items)),
            "entries": items[:limit],
        }, indent=2, default=str)
