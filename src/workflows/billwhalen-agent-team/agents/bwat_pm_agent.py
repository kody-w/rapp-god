"""bwat_pm_agent — sprint planning, backlog, status reporting.

Bill Whalen Agent Team (BWAT) — PM persona. Reads the local intake
backlog, proposes a sprint, surfaces conflicts and dependencies,
emits status reports the owner can paste into a stand-up.

Single-file RAPP agent. Reads from the same .brainstem_data/bwat_intake.jsonl
the Intake agent writes to — no separate datastore.

Actions:
  propose_sprint    — pick N items from the backlog for a sprint
  status_report     — markdown status report (newest 7 days)
  detect_conflicts  — flag items with overlapping use cases
  prioritize        — rank backlog by simple heuristic
  get_status        — agent readiness probe
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone, timedelta

try:
    from agents.basic_agent import BasicAgent
except ImportError:
    from basic_agent import BasicAgent


def _data_path() -> str:
    base = os.environ.get(
        "BRAINSTEM_DATA",
        os.path.join(os.path.expanduser("~"), ".brainstem", ".brainstem_data"),
    )
    return os.path.join(base, "bwat_intake.jsonl")


def _read_backlog() -> list[dict]:
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
    return [e for e in out if e.get("kind") in ("idea", "solution")]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(s: str) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


class BwatPmAgent(BasicAgent):
    metadata = {
        "name": "BwatPm",
        "description": (
            "Project Manager persona. Reads the local backlog, proposes "
            "sprints, generates status reports, surfaces conflicting work "
            "items. Operates entirely on local data — no GitHub round-trip "
            "required for the iteration loop."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["propose_sprint", "status_report",
                             "detect_conflicts", "prioritize", "get_status"],
                },
                "sprint_capacity": {
                    "type": "integer",
                    "description": "How many items the sprint should hold (default 5).",
                },
                "lookback_days": {
                    "type": "integer",
                    "description": "Days back to include for status report (default 7).",
                },
            },
            "required": ["action"],
        },
    }

    def __init__(self):
        self.name = "BwatPm"

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "get_status")

        if action == "get_status":
            backlog = _read_backlog()
            return json.dumps({
                "ok": True, "agent": self.name, "ready": True,
                "backlog_size": len(backlog),
                "actions": [
                    "propose_sprint", "status_report",
                    "detect_conflicts", "prioritize", "get_status",
                ],
            })

        backlog = _read_backlog()

        if action == "propose_sprint":
            cap = int(kwargs.get("sprint_capacity") or 5)
            ranked = self._rank(backlog)
            picked = ranked[:cap]
            return json.dumps({
                "ok": True,
                "sprint_capacity": cap,
                "available": len(ranked),
                "picked": [{"id": e["id"], "title": e["title"],
                            "kind": e["kind"], "score": e.get("_score")}
                           for e in picked],
                "next_step": (
                    "Send each picked item through BwatOutcomeFramer.frame_outcome "
                    "if not yet framed, then to the build agents."
                ),
            }, indent=2)

        if action == "status_report":
            days = int(kwargs.get("lookback_days") or 7)
            cutoff = _now() - timedelta(days=days)
            recent = [e for e in backlog if (_parse_iso(e.get("logged_at", "")) or _now()) >= cutoff]
            md = self._format_status(recent, days)
            return json.dumps({
                "ok": True,
                "lookback_days": days,
                "items_in_window": len(recent),
                "report_markdown": md,
            }, indent=2)

        if action == "detect_conflicts":
            conflicts = self._find_conflicts(backlog)
            return json.dumps({
                "ok": True,
                "conflict_count": len(conflicts),
                "conflicts": conflicts,
            }, indent=2)

        if action == "prioritize":
            ranked = self._rank(backlog)
            return json.dumps({
                "ok": True,
                "ranked": [
                    {"id": e["id"], "title": e["title"], "score": e.get("_score")}
                    for e in ranked
                ],
            }, indent=2)

        return json.dumps({"ok": False, "error": f"unknown action: {action}"})

    # ── heuristics ────────────────────────────────────────────────────
    def _rank(self, backlog: list[dict]) -> list[dict]:
        # simple priority: solutions first, then newer ideas, age boosts urgency
        now = _now()
        for e in backlog:
            score = 0.0
            if e.get("kind") == "solution":
                score += 5
            ts = _parse_iso(e.get("logged_at", ""))
            if ts:
                age_days = (now - ts).total_seconds() / 86400.0
                # newer = higher; but old open items need attention
                score += min(3.0, 3.0 / (1.0 + age_days * 0.3))
                if age_days > 14:
                    score += 1.5  # stale-bonus
            t = (e.get("title") or "").lower()
            if any(w in t for w in ("bug", "broken", "outage", "blocker")):
                score += 4
            e["_score"] = round(score, 2)
        return sorted(backlog, key=lambda e: -e["_score"])

    def _format_status(self, items: list[dict], days: int) -> str:
        if not items:
            return f"## BWAT status — last {days} days\n\nNo intake activity in window.\n"
        ideas = [e for e in items if e["kind"] == "idea"]
        sols = [e for e in items if e["kind"] == "solution"]
        lines = [
            f"## BWAT status — last {days} days",
            "",
            f"- **New ideas:** {len(ideas)}",
            f"- **Solutions logged:** {len(sols)}",
            "",
            "### Recent (newest first)",
            "",
        ]
        for e in items[:10]:
            ts = (e.get("logged_at") or "")[:10]
            lines.append(f"- `{ts}` **{e['kind']}** — {e['title']}")
        return "\n".join(lines) + "\n"

    def _find_conflicts(self, backlog: list[dict]) -> list[dict]:
        # crude: items whose titles share >= 3 significant words
        def sig_words(s: str) -> set[str]:
            return {w.lower().strip(".,!?:;()") for w in s.split()
                    if len(w) > 3} - {"with", "from", "that", "this",
                                       "into", "their", "have", "more", "less",
                                       "make", "build", "need", "want"}
        conflicts: list[dict] = []
        seen: set[str] = set()
        for i, a in enumerate(backlog):
            for b in backlog[i + 1:]:
                pair_key = "::".join(sorted([a["id"], b["id"]]))
                if pair_key in seen:
                    continue
                wa = sig_words(a.get("title", ""))
                wb = sig_words(b.get("title", ""))
                shared = wa & wb
                if len(shared) >= 3:
                    seen.add(pair_key)
                    conflicts.append({
                        "a": {"id": a["id"], "title": a["title"]},
                        "b": {"id": b["id"], "title": b["title"]},
                        "shared_terms": sorted(shared),
                    })
        return conflicts
