"""bill_twin_agent — Bill Whalen's digital twin in the neighborhood.

A solution-engineer's-best-friend persona: when a new operator joins
the BWAT neighborhood, they often don't know what to ask, in what
order, with what context. Bill (the twin) does. He walks them
through the workflow — outcome-first, intake-second, validate-last —
in the voice and rhythm of someone who's set up a hundred customer
engagements.

Single-file RAPP agent. Stateless across sessions; reads the local
backlog (BwatIntake's data file) to ground its suggestions.

Actions:
  walkthrough     — step the joiner through their first hour
  next_move       — given current state, suggest the next action
  field_pattern   — recall a Bill-shaped pattern for a customer scenario
  intro           — friendly orientation message for a fresh joiner
  get_status      — agent readiness probe
"""

from __future__ import annotations

import json
import os

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


def _backlog_size() -> int:
    p = _data_path()
    if not os.path.exists(p):
        return 0
    try:
        with open(p) as f:
            return sum(1 for line in f if line.strip())
    except Exception:
        return 0


_FIELD_PATTERNS = {
    "first_customer_call": (
        "Don't try to scope the build on the first call. Use the call to learn "
        "ONE thing: what does the customer measure that they wish were better? "
        "That sentence becomes the Outcome Framer's input. Everything downstream "
        "snaps into place once the metric is named. If they can't name a metric, "
        "the engagement isn't ready — schedule a 30-minute follow-up to find it."
    ),
    "demo_in_60_minutes": (
        "Ship a working demo in the customer's tenant in 60 minutes by skipping "
        "everything that isn't the spine: outcome → one agent → one trigger → one "
        "visible result. The customer doesn't care about your architecture diagram; "
        "they care that something happened in their environment that wasn't there "
        "before. PowerShell-provision the entity, drop the agent, wire the trigger, "
        "screenshot the result. Architecture lecture comes after sign-off."
    ),
    "stuck_on_consent": (
        "When a customer's IT blocks consent for a Copilot Studio agent, don't "
        "argue the technical case — find the human who owns the AppReg policy and "
        "ask them what their approval criteria are. Then meet them. 80% of consent "
        "delays are organizational, not technical."
    ),
    "stalled_engagement": (
        "If the engagement has been quiet for 5 days, it's not waiting on you — "
        "it's waiting on a decision the customer can't make alone. Send the owner "
        "a one-line message: 'What's blocking the decision on X?' Don't offer to "
        "help yet. Just surface the block."
    ),
    "scope_creep": (
        "When the customer says 'and could it also...' on a small build, write the "
        "ask down in the BWAT intake backlog and tell them you'll come back to it "
        "AFTER the v1 ships. Most 'also' asks evaporate once v1 is in their hands. "
        "The ones that don't get their own outcome statement next sprint."
    ),
    "ai_hallucinates_data": (
        "When the customer's pilot complains 'the AI made up a number,' the fix is "
        "almost always grounding, not prompt engineering. Wire the agent to fetch "
        "from a Dataverse view or an AI Search index instead of relying on the "
        "model's recall. Hallucination is a missing-data-source problem, not a "
        "model-quality problem."
    ),
}


class BillTwinAgent(BasicAgent):
    metadata = {
        "name": "BillTwin",
        "description": (
            "Bill Whalen's digital twin in the BWAT neighborhood. The "
            "solution engineer's friend: walks new joiners through the "
            "workflow, suggests the next move based on current state, "
            "and recalls field-tested patterns for common customer "
            "scenarios. Use when you're not sure what to do next."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["walkthrough", "next_move", "field_pattern",
                             "intro", "get_status"],
                },
                "scenario": {
                    "type": "string",
                    "description": (
                        "For field_pattern: which scenario to recall. "
                        f"Available: {', '.join(sorted(_FIELD_PATTERNS.keys()))}."
                    ),
                },
                "joiner_name": {
                    "type": "string",
                    "description": "Optional first name for personalized intro.",
                },
            },
            "required": ["action"],
        },
    }

    def __init__(self):
        self.name = "BillTwin"

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "intro")

        if action == "get_status":
            return json.dumps({
                "ok": True, "agent": self.name, "ready": True,
                "patterns_known": len(_FIELD_PATTERNS),
                "actions": ["walkthrough", "next_move",
                            "field_pattern", "intro", "get_status"],
            })

        if action == "intro":
            who = (kwargs.get("joiner_name") or "").strip() or "you"
            return json.dumps({
                "ok": True,
                "voice": "bill",
                "message": (
                    f"Hey {who} — welcome to the BWAT neighborhood. I'm a "
                    "twin of Bill Whalen, here to help you get useful "
                    "before you get clever. Three rules of the road:\n\n"
                    "1. Outcome before build. If you can't say what success "
                    "looks like in one sentence, ask BwatOutcomeFramer first.\n"
                    "2. Log everything. Even half-formed ideas. BwatIntake "
                    "is your friend; you cannot have too much in the backlog.\n"
                    "3. Nothing closes without OutcomeValidator's say-so. "
                    "If your AI built the wrong thing, that's how we catch it.\n\n"
                    "When you're stuck, ask me: BillTwin.next_move. I'll "
                    "look at where you are and tell you what I'd do."
                ),
            }, indent=2)

        if action == "walkthrough":
            return json.dumps({
                "ok": True,
                "voice": "bill",
                "steps": [
                    {"step": 1, "action": "BwatIntake.log_idea",
                     "why": "Capture the raw ask before you forget the words the customer used."},
                    {"step": 2, "action": "BwatOutcomeFramer.frame_outcome",
                     "why": "Turn the ask into a measurable success statement. This is the gate."},
                    {"step": 3, "action": "BwatPm.propose_sprint",
                     "why": "Pick what's actually going to ship this cycle. Be honest about capacity."},
                    {"step": 4, "action": "<your build agents do their thing>",
                     "why": "Now and only now do you build. The framing protects the build from drift."},
                    {"step": 5, "action": "BwatOutcomeValidator.validate_outcome",
                     "why": "Did we ship what we said we'd ship? If yes, request sign-off. If no, surface gaps."},
                    {"step": 6, "action": "BwatOutcomeValidator.archive_outcome",
                     "why": "Close the loop. The archive is the canonical record of what shipped."},
                ],
                "next_step": (
                    "Run BillTwin.next_move whenever you're unsure which step "
                    "you're actually on. The twin reads your local backlog and tells you."
                ),
            }, indent=2)

        if action == "next_move":
            n = _backlog_size()
            if n == 0:
                msg = (
                    "Your backlog is empty. Step 0: log your first idea. "
                    "Run BwatIntake.log_idea with title and body. "
                    "Then come back."
                )
            elif n < 3:
                msg = (
                    f"You have {n} item(s) in the backlog. Before sprinting, "
                    "frame at least one of them: "
                    "BwatOutcomeFramer.frame_outcome with the use_case from "
                    "the intake entry. The framing is what protects the build."
                )
            elif n < 10:
                msg = (
                    f"Backlog is at {n}. Time to propose a sprint: "
                    "BwatPm.propose_sprint with sprint_capacity=5. "
                    "Pick what genuinely ships this cycle."
                )
            else:
                msg = (
                    f"Backlog is at {n} — that's a lot. Before another sprint, "
                    "run BwatPm.detect_conflicts to find duplicate work, then "
                    "BwatPm.prioritize to see which items the heuristic favors. "
                    "Cull aggressively; a backlog over 20 is just hopes and dreams."
                )
            return json.dumps({
                "ok": True,
                "voice": "bill",
                "backlog_size": n,
                "next_move": msg,
            }, indent=2)

        if action == "field_pattern":
            scenario = (kwargs.get("scenario") or "").strip().lower()
            if scenario not in _FIELD_PATTERNS:
                return json.dumps({
                    "ok": False,
                    "error": f"unknown scenario: {scenario!r}",
                    "available": sorted(_FIELD_PATTERNS.keys()),
                })
            return json.dumps({
                "ok": True,
                "voice": "bill",
                "scenario": scenario,
                "pattern": _FIELD_PATTERNS[scenario],
            }, indent=2)

        return json.dumps({"ok": False, "error": f"unknown action: {action}"})
