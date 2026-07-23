"""twin_agent — M365 Solution Engineer twin.

A twin agent themed for Microsoft 365 / Power Platform / Azure / Copilot
work. Walks operators through the Microsoft-stack engagement pattern,
recalls field-tested patterns specific to the Microsoft ecosystem, and
suggests next moves based on the operator's local backlog.

Action set:
  intro          — friendly orientation message
  walkthrough    — 6-step M365 engagement pattern
  next_move      — read backlog + suggest next action
  field_pattern  — recall a Microsoft-stack-specific pattern
  get_status     — agent readiness probe
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
    return os.path.join(base, "intake.jsonl")


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
        "That sentence becomes the OutcomeFramer's input. Microsoft customers "
        "often have rich telemetry already — find the metric in their Power BI "
        "dashboard or M365 admin center; that's where the truth lives."
    ),
    "demo_in_60_minutes": (
        "Ship a working demo in the customer's tenant in 60 minutes by skipping "
        "everything that isn't the spine: outcome → one Copilot Studio agent → "
        "one trigger → one visible result in their tenant. Customer doesn't "
        "care about your architecture diagram; they care that something happened "
        "in their tenant that wasn't there before. PowerShell-provision the "
        "Dataverse entity, drop the Copilot Studio topic, wire the trigger, "
        "screenshot the result. Architecture lecture comes after sign-off."
    ),
    "stuck_on_consent": (
        "When IT blocks consent for a Copilot Studio agent or an Entra app reg, "
        "don't argue the technical case — find the human who owns the AppReg "
        "approval policy and ask them what their approval criteria are. Then "
        "meet them. 80% of consent delays are organizational, not technical."
    ),
    "stalled_engagement": (
        "If the engagement has been quiet for 5 days, it's not waiting on you — "
        "it's waiting on a decision the customer can't make alone. Send the "
        "owner a one-line message: 'What's blocking the decision on X?' "
        "Don't offer to help yet. Just surface the block."
    ),
    "scope_creep": (
        "When the customer says 'and could it also...' on a small build, write "
        "the ask down in the intake backlog and tell them you'll come back to "
        "it AFTER the v1 ships. Most 'also' asks evaporate once v1 is in their "
        "hands. The ones that don't get their own outcome statement next sprint."
    ),
    "ai_hallucinates_data": (
        "When the customer's pilot complains 'the AI made up a number,' the "
        "fix is almost always grounding, not prompt engineering. Wire the "
        "Copilot Studio agent to fetch from a Dataverse view, AI Search index, "
        "or SharePoint document library instead of relying on the model's "
        "recall. Hallucination is a missing-data-source problem, not a "
        "model-quality problem."
    ),
    "copilot_studio_yaml_error": (
        "Copilot Studio topic YAML errors are usually one of three things: (1) "
        "missing `string()` cast on a variable that's used in a string context, "
        "(2) `allowInterruption` not set on the trigger, or (3) `kind: Skills` "
        "missing on a Power Automate flow you're calling. Skim the YAML for "
        "those three before debugging anything else."
    ),
    "workiq_setup": (
        "If the operator hasn't run `WorkIQ` against their tenant before: "
        "(1) `npm install -g @microsoft/workiq` (2) `workiq accept-eula` "
        "(3) `workiq ask 'list my recent emails'` to trigger the Entra ID "
        "device-code login. After that, the WorkIQ agent in this neighborhood "
        "can pull email/calendar/Teams/SharePoint context on demand."
    ),
}


class TwinAgent(BasicAgent):
    metadata = {
        "name": "Twin",
        "description": (
            "Microsoft-stack solution engineer twin for the Microsoft 365 Team "
            "neighborhood. Walks new operators through the M365 / Copilot Studio / "
            "Power Platform / Azure engagement pattern. Recalls field-tested "
            "patterns. Suggests next moves based on the operator's local backlog. "
            "Use when stuck or starting an engagement."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["intro", "walkthrough", "next_move",
                             "field_pattern", "get_status"],
                },
                "scenario": {
                    "type": "string",
                    "description": (
                        "For field_pattern: scenario name. Available: "
                        f"{', '.join(sorted(_FIELD_PATTERNS.keys()))}."
                    ),
                },
                "operator_name": {
                    "type": "string",
                    "description": "Optional first name for personalized intro.",
                },
            },
            "required": ["action"],
        },
    }

    def __init__(self):
        self.name = "Twin"

    def perform(self, **kwargs) -> str:
        action = kwargs.get("action", "intro")

        if action == "get_status":
            return json.dumps({
                "ok": True, "agent": self.name, "ready": True,
                "patterns_known": len(_FIELD_PATTERNS),
                "actions": ["intro", "walkthrough", "next_move",
                             "field_pattern", "get_status"],
            })

        if action == "intro":
            who = (kwargs.get("operator_name") or "").strip() or "you"
            return json.dumps({
                "ok": True, "voice": "ms-se",
                "message": (
                    f"Hey {who} — welcome to the Microsoft 365 Team neighborhood. "
                    "I'm a twin shaped for the Microsoft-stack solution engineer "
                    "pattern: M365, Copilot Studio, Power Platform, Azure AI "
                    "Foundry. Three rules of the road:\n\n"
                    "1. Outcome before build. If you can't say what success "
                    "looks like in one sentence, ask OutcomeFramer first.\n"
                    "2. Log everything. Even half-formed asks. Intake captures; "
                    "Pm prioritizes.\n"
                    "3. Nothing closes without OutcomeValidator's say-so. "
                    "Demo doesn't count; signed sign-off does.\n\n"
                    "When you're stuck, ask me: `Twin next_move`. I'll look at "
                    "where you are and tell you what I'd do."
                ),
            }, indent=2)

        if action == "walkthrough":
            return json.dumps({
                "ok": True, "voice": "ms-se",
                "steps": [
                    {"step": 1, "action": "Intake.log_idea",
                     "why": "Capture the customer's raw ask before you forget the words they used."},
                    {"step": 2, "action": "OutcomeFramer.frame_outcome",
                     "why": "Turn the ask into a measurable success statement. The why-first gate."},
                    {"step": 3, "action": "Pm.propose_sprint",
                     "why": "Pick what's actually going to ship this cycle. Be honest about capacity."},
                    {"step": 4, "action": "(optional) WorkIQ.ask",
                     "why": "Pull M365 context — emails, meetings, docs, Teams messages — relevant to the engagement."},
                    {"step": 5, "action": "<your build agents do their thing>",
                     "why": "Now and only now do you build. The framing protects the build from drift."},
                    {"step": 6, "action": "OutcomeValidator.validate_outcome",
                     "why": "Did we ship what we said we'd ship? If yes, request sign-off. If no, surface gaps."},
                    {"step": 7, "action": "OutcomeValidator.archive_outcome",
                     "why": "Close the loop. The archive is the canonical record of what shipped."},
                ],
                "next_step": (
                    "Run `Twin next_move` whenever you're unsure which step "
                    "you're on. I read your local backlog and tell you."
                ),
            }, indent=2)

        if action == "next_move":
            n = _backlog_size()
            if n == 0:
                msg = (
                    "Your backlog is empty. Step 0: log your first idea. "
                    "Run Intake.log_idea with title and body. Then come back."
                )
            elif n < 3:
                msg = (
                    f"You have {n} item(s) in the backlog. Before sprinting, "
                    "frame at least one: OutcomeFramer.frame_outcome with the "
                    "use_case from the intake entry. Framing protects the build."
                )
            elif n < 10:
                msg = (
                    f"Backlog at {n}. Time to propose a sprint: Pm.propose_sprint "
                    "with sprint_capacity=5. Pick what genuinely ships this cycle."
                )
            else:
                msg = (
                    f"Backlog at {n} — that's a lot. Run Pm.detect_conflicts to "
                    "find duplicate work, then Pm.prioritize. Cull aggressively; "
                    "a backlog over 20 is hopes and dreams, not a plan."
                )
            return json.dumps({
                "ok": True, "voice": "ms-se",
                "backlog_size": n, "next_move": msg,
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
                "ok": True, "voice": "ms-se",
                "scenario": scenario,
                "pattern": _FIELD_PATTERNS[scenario],
            }, indent=2)

        return json.dumps({"ok": False, "error": f"unknown action: {action}"})
