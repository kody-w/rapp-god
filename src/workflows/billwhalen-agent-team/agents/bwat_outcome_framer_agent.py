"""bwat_outcome_framer_agent — frame the outcome before any build work.

Bill Whalen Agent Team (BWAT) — Outcome Framer persona. The "why-first"
gate. Every issue passes through here before code is written. Without a
defined outcome, the team builds the wrong thing.

Single-file RAPP agent (Article XXXIII): one class, one perform, one
metadata dict. Drops into any brainstem's agents/ directory and runs.

Actions:
  frame_outcome      — turn a raw idea into a structured outcome statement
  define_kpi         — propose 1-3 measurable success criteria
  validate_feasibility — quick gut-check on whether the outcome is buildable
  get_status         — agent readiness probe
"""

from __future__ import annotations

import json

try:
    from agents.basic_agent import BasicAgent
except ImportError:
    from basic_agent import BasicAgent


_OUTCOME_TEMPLATE = (
    "## Outcome Statement\n\n"
    "**Use case:** {use_case}\n\n"
    "**Success looks like:** {success}\n\n"
    "**Who measures it:** {owner}\n\n"
    "**KPIs:**\n{kpis}\n\n"
    "**Done when:** {done_when}\n\n"
    "**Out of scope:** {out_of_scope}\n"
)


class BwatOutcomeFramerAgent(BasicAgent):
    metadata = {
        "name": "BwatOutcomeFramer",
        "description": (
            "Frames the outcome of any work item before build begins. "
            "Why-first gate: success metrics, KPI, owner, definition-of-done, "
            "explicit out-of-scope. Use this on any GitHub issue that doesn't "
            "yet have a defined outcome."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["frame_outcome", "define_kpi",
                             "validate_feasibility", "get_status"],
                    "description": "Which framing operation to perform.",
                },
                "use_case": {
                    "type": "string",
                    "description": "1-2 sentence description of the raw idea.",
                },
                "context": {
                    "type": "string",
                    "description": "Any prior conversation, constraints, or acceptance hints.",
                },
                "owner": {
                    "type": "string",
                    "description": "Who is accountable (a name, team, or role).",
                },
            },
            "required": ["action"],
        },
    }

    def __init__(self):
        self.name = "BwatOutcomeFramer"

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "get_status")
        if action == "get_status":
            return json.dumps({
                "ok": True, "agent": self.name,
                "ready": True, "actions": [
                    "frame_outcome", "define_kpi",
                    "validate_feasibility", "get_status",
                ],
            })

        use_case = (kwargs.get("use_case") or "").strip()
        if not use_case:
            return json.dumps({
                "ok": False,
                "error": "use_case is required for framing actions",
            })

        owner = (kwargs.get("owner") or "the requester").strip()
        context = (kwargs.get("context") or "").strip()

        if action == "frame_outcome":
            kpis = self._propose_kpis(use_case, context)
            kpi_md = "\n".join(f"  - {k}" for k in kpis)
            statement = _OUTCOME_TEMPLATE.format(
                use_case=use_case,
                success=self._infer_success(use_case),
                owner=owner,
                kpis=kpi_md,
                done_when=self._infer_done(use_case),
                out_of_scope=self._infer_oos(use_case),
            )
            return json.dumps({
                "ok": True,
                "schema": "bwat-outcome-statement/1.0",
                "outcome_markdown": statement,
                "kpis": kpis,
                "owner": owner,
                "next_step": (
                    "Paste the outcome_markdown into the issue body before any build "
                    "work begins. Re-frame if the success criteria don't match the ask."
                ),
            }, indent=2)

        if action == "define_kpi":
            kpis = self._propose_kpis(use_case, context)
            return json.dumps({"ok": True, "kpis": kpis}, indent=2)

        if action == "validate_feasibility":
            verdict, reasons = self._gut_check_feasibility(use_case, context)
            return json.dumps({
                "ok": True, "verdict": verdict, "reasons": reasons,
            }, indent=2)

        return json.dumps({"ok": False, "error": f"unknown action: {action}"})

    # ── heuristics (intentionally simple — the LLM does the heavy lift) ──
    def _propose_kpis(self, use_case: str, context: str) -> list[str]:
        u = use_case.lower()
        kpis: list[str] = []
        if any(w in u for w in ("dashboard", "report", "view", "see")):
            kpis.append("First successful render under 3 seconds end-to-end")
            kpis.append("Stakeholder reviews + signs off without revision")
        if any(w in u for w in ("automate", "bot", "agent", "pipeline")):
            kpis.append("Runs unattended for 7 consecutive days without manual intervention")
            kpis.append(">= 95% of triggered runs complete without error")
        if any(w in u for w in ("migrate", "upgrade", "replace")):
            kpis.append("Cutover happens with zero data loss vs source-of-truth diff")
            kpis.append("All downstream consumers continue working without code change")
        if any(w in u for w in ("integrate", "connect", "sync")):
            kpis.append("Round-trip data flow verified in staging within first sprint")
        if not kpis:
            kpis = [
                "Outcome owner can demonstrate the result in <5 min",
                "Two independent stakeholders confirm the result matches the ask",
            ]
        return kpis[:3]

    def _infer_success(self, use_case: str) -> str:
        return f"<owner can describe in one sentence what changed because of this work>"

    def _infer_done(self, use_case: str) -> str:
        return "All KPIs above are demonstrably met AND the OutcomeValidator agent has signed off."

    def _infer_oos(self, use_case: str) -> str:
        return "<list anything explicitly NOT being addressed in this work item>"

    def _gut_check_feasibility(self, use_case: str, context: str) -> tuple[str, list[str]]:
        u = (use_case + " " + context).lower()
        flags: list[str] = []
        if "production" in u and "no test" in u:
            flags.append("Heading to prod without a test path — schedule a hardening pass first.")
        if "by tomorrow" in u or "asap" in u or "today" in u:
            flags.append("Tight deadline — confirm scope is genuinely 1-day-shaped, not 1-week-compressed.")
        if "everyone" in u or "all users" in u:
            flags.append("Scope says 'everyone' — name the actual first cohort to derisk.")
        if "ai" in u and "decide" in u:
            flags.append("AI-makes-decision pattern — confirm a human-in-the-loop is in v1.")
        verdict = "proceed-with-caution" if flags else "no-blockers-detected"
        if not flags:
            flags = ["No obvious red flags. Confirm with PM that the sprint has bandwidth."]
        return verdict, flags
