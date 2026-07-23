"""bwat_outcome_validator_agent — verify the outcome before any close.

Bill Whalen Agent Team (BWAT) — Outcome Validator persona. The "nothing
closes without a verified outcome" gate. Pairs with BwatOutcomeFramer:
the framer defines what success looks like; the validator confirms it
happened.

Single-file RAPP agent.

Actions:
  validate_outcome  — check the stated outcome was actually delivered
  check_kpi_met     — compare current state against the KPI list
  request_sign_off  — produce a sign-off request for the named owner
  archive_outcome   — emit the canonical archive record for closing
  get_status        — agent readiness probe
"""

from __future__ import annotations

import json

try:
    from agents.basic_agent import BasicAgent
except ImportError:
    from basic_agent import BasicAgent


class BwatOutcomeValidatorAgent(BasicAgent):
    metadata = {
        "name": "BwatOutcomeValidator",
        "description": (
            "Validates that a stated outcome was actually delivered before "
            "any work item closes. Compares evidence against KPIs, requests "
            "owner sign-off, and emits the canonical archive record. Use "
            "before closing any issue with an outcome statement attached."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["validate_outcome", "check_kpi_met",
                             "request_sign_off", "archive_outcome",
                             "get_status"],
                },
                "outcome_statement": {
                    "type": "string",
                    "description": "The original outcome markdown from BwatOutcomeFramer.",
                },
                "kpis": {
                    "type": "array", "items": {"type": "string"},
                    "description": "List of KPI strings to validate against.",
                },
                "evidence": {
                    "type": "string",
                    "description": "What was actually delivered (links, screenshots-as-text, metrics).",
                },
                "owner_handle": {"type": "string"},
            },
            "required": ["action"],
        },
    }

    def __init__(self):
        self.name = "BwatOutcomeValidator"

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "get_status")

        if action == "get_status":
            return json.dumps({
                "ok": True, "agent": self.name, "ready": True,
                "actions": [
                    "validate_outcome", "check_kpi_met",
                    "request_sign_off", "archive_outcome", "get_status",
                ],
            })

        if action == "validate_outcome":
            return self._validate_outcome(kwargs)
        if action == "check_kpi_met":
            return self._check_kpis(kwargs)
        if action == "request_sign_off":
            return self._request_sign_off(kwargs)
        if action == "archive_outcome":
            return self._archive(kwargs)

        return json.dumps({"ok": False, "error": f"unknown action: {action}"})

    def _validate_outcome(self, kwargs: dict) -> str:
        outcome = (kwargs.get("outcome_statement") or "").strip()
        evidence = (kwargs.get("evidence") or "").strip()
        if not outcome or not evidence:
            return json.dumps({
                "ok": False,
                "error": "outcome_statement AND evidence required",
            })
        gaps = self._gap_check(outcome, evidence)
        return json.dumps({
            "ok": True,
            "verdict": "passes" if not gaps else "needs-more-evidence",
            "gaps": gaps,
            "next_step": (
                "If gaps is empty, run request_sign_off then archive_outcome. "
                "If gaps is non-empty, surface them to the build agents and "
                "do not close the issue yet."
            ),
        }, indent=2)

    def _check_kpis(self, kwargs: dict) -> str:
        kpis = kwargs.get("kpis") or []
        evidence = (kwargs.get("evidence") or "").lower()
        if not kpis:
            return json.dumps({"ok": False, "error": "kpis (list) required"})
        results = []
        for k in kpis:
            kw = self._signal_words(k)
            hits = [w for w in kw if w in evidence]
            results.append({
                "kpi": k,
                "evidence_signal_count": len(hits),
                "verdict": ("met" if len(hits) >= max(1, len(kw) // 2)
                            else "unclear" if hits else "not-evidenced"),
                "matched_signals": hits,
            })
        all_met = all(r["verdict"] == "met" for r in results)
        return json.dumps({
            "ok": True, "all_met": all_met, "per_kpi": results,
        }, indent=2)

    def _request_sign_off(self, kwargs: dict) -> str:
        owner = (kwargs.get("owner_handle") or "bill").strip()
        outcome = (kwargs.get("outcome_statement") or "").strip()
        if not outcome:
            return json.dumps({"ok": False, "error": "outcome_statement required"})
        comment_md = (
            f"@{owner} — requesting outcome sign-off on this work item.\n\n"
            f"### Outcome under review\n\n{outcome}\n\n"
            f"### Validator verdict\n\nReady for your sign-off; mark this "
            f"issue with the `outcome-validated` label or reply 'approved' "
            f"to confirm. The OutcomeValidator agent will then archive "
            f"and close.\n"
        )
        return json.dumps({
            "ok": True,
            "owner": owner,
            "comment_markdown": comment_md,
            "next_step": (
                "Post the comment_markdown to the issue. Wait for "
                "owner-approval-or-label, then call archive_outcome."
            ),
        }, indent=2)

    def _archive(self, kwargs: dict) -> str:
        outcome = (kwargs.get("outcome_statement") or "").strip()
        evidence = (kwargs.get("evidence") or "").strip()
        if not outcome:
            return json.dumps({"ok": False, "error": "outcome_statement required"})
        archive = {
            "schema": "bwat-outcome-archive/1.0",
            "outcome_statement": outcome,
            "delivered_evidence": evidence,
            "validator": self.name,
            "ready_to_close": True,
        }
        return json.dumps({
            "ok": True,
            "archive": archive,
            "next_step": (
                "Post archive as a final comment on the issue, then close. "
                "The archive is the canonical record of what shipped."
            ),
        }, indent=2)

    # ── helpers ────────────────────────────────────────────────────────
    def _gap_check(self, outcome: str, evidence: str) -> list[str]:
        gaps: list[str] = []
        outcome_l = outcome.lower()
        evidence_l = evidence.lower()
        if "kpi" in outcome_l and "kpi" not in evidence_l:
            gaps.append("Outcome named KPIs; evidence doesn't reference KPI measurement.")
        if "owner" in outcome_l and "@" not in evidence_l and "approved" not in evidence_l:
            gaps.append("Outcome named an owner; no sign-off in evidence.")
        if "demonstrably" in outcome_l and "demo" not in evidence_l \
                and "screenshot" not in evidence_l and "log" not in evidence_l:
            gaps.append("Outcome required demonstrable result; evidence has no demo/screenshot/log reference.")
        return gaps

    def _signal_words(self, kpi: str) -> list[str]:
        words = [w.strip(".,!?:;()").lower() for w in kpi.split()]
        return [w for w in words
                if len(w) > 3 and w not in {"the", "and", "with", "from",
                                             "that", "this", "into", "first",
                                             "their", "have", "more", "less"}]
