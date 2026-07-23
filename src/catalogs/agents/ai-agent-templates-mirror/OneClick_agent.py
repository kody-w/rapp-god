"""OneClick — conversational one-click deploy for this AI Agent Templates stack library.

SHELL / DEMO. This is the conversational front end for the one-click deploy described in
ONE_CLICK.md. Point it at this repo and talk to it: "list the stacks", "tell me about the
predictive asset maintenance stack", "deploy the predictive asset maintenance stack to Copilot
Studio". It reads this repo's manifest.json (raw GitHub) to know the real stacks, then narrates the
sequential, agent-by-agent MCS deployment.

It does NOT run a real deployment yet — the actual MCS/Copilot Studio pipeline (standalone MCS agent
model, stack-folder-as-deployment-unit, multi-agent merge, ADO build-summary reporting) is landed
separately per ONE_CLICK.md. No PII: it only deals with stack + agent template metadata.
"""

__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@kody-w/oneclick_agent",
    "version": "0.1.0",
    "display_name": "OneClick",
    "description": "Conversational one-click deploy for the AI Agent Templates stack library — list, describe, and (shell) deploy a stack to Microsoft Copilot Studio.",
    "author": "kody-w",
    "tags": ["one-click", "deploy", "copilot-studio", "mcs", "stacks", "conversational", "shell"],
    "category": "integrations",
    "quality_tier": "community",
    "requires_env": [],
    "dependencies": ["@rapp/basic_agent"],
}

import os
import re
import json
import urllib.request

try:
    from agents.basic_agent import BasicAgent  # type: ignore  # resolves inside a brainstem
except Exception:
    class BasicAgent:
        def __init__(self, name, metadata):
            self.name = name
            self.metadata = metadata

REPO = "kody-w/ai-agent-templates-mirror"
RAW = "https://raw.githubusercontent.com/" + REPO + "/main"


def _fetch_manifest():
    """Best-effort read of this repo's manifest.json (the real stacks). Returns [] offline."""
    try:
        with urllib.request.urlopen(RAW + "/manifest.json", timeout=8) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return None


def _stacks(manifest):
    """Normalize the manifest into a list of {id, name, industry, agents:[...]}. Tolerant of shape."""
    out = []
    if not isinstance(manifest, dict):
        return out
    # manifest.json shapes vary; scan for stack-like records
    def add(rec):
        if not isinstance(rec, dict):
            return
        sid = rec.get("id") or rec.get("stack_id") or rec.get("name")
        if not sid:
            return
        agents = []
        for a in (rec.get("agents") or rec.get("agent_files") or []):
            nm = (a.get("name") or a.get("filename") or "") if isinstance(a, dict) else str(a)
            nm = re.sub(r"\.py$", "", nm).replace("_", " ")
            nm = re.sub(r"(?i)\bagent\b\s*$", "", nm).strip()
            if nm:
                agents.append(nm[:1].upper() + nm[1:])
        out.append({
            "id": sid,
            "name": re.sub(r"(?i)\s*stack$", "", rec.get("name") or sid).strip() or sid,
            "industry": rec.get("industry_label") or rec.get("category") or "",
            "agents": agents,
            "description": rec.get("description", ""),
        })
    for key in ("stacks", "agent_stacks", "items"):
        v = manifest.get(key)
        if isinstance(v, list):
            for rec in v:
                add(rec)
        elif isinstance(v, dict):
            for rec in v.values():
                add(rec)
    return out


def _match(stacks, query):
    q = re.sub(r"[^a-z0-9 ]", " ", (query or "").lower())
    terms = [t for t in q.split() if len(t) > 2 and t not in ("the", "stack", "deploy", "agent", "agents", "copilot", "studio", "into", "this")]
    best, score = None, 0
    for s in stacks:
        hay = (s["id"] + " " + s["name"] + " " + s["industry"]).lower()
        hit = sum(1 for t in terms if t in hay)
        if hit > score:
            best, score = s, hit
    return best if score else None


class OneClickAgent(BasicAgent):
    def __init__(self):
        self.name = "OneClick"
        self.metadata = {
            "name": self.name,
            "description": "Conversational one-click deploy for the AI Agent Templates stack library. "
                           "Say 'list stacks', 'describe <stack>', or 'deploy <stack> to Copilot Studio'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "What you want — e.g. 'deploy the predictive asset maintenance stack to Copilot Studio'."},
                },
                "required": ["message"],
            },
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs):
        msg = (kwargs.get("message") or kwargs.get("user_input") or "").strip()
        if not msg:
            return ("👋 I'm OneClick — I deploy agent stacks from " + REPO + " to Microsoft Copilot Studio.\n"
                    "Try: \"list stacks\" · \"describe the predictive asset maintenance stack\" · "
                    "\"deploy the predictive asset maintenance stack to Copilot Studio\".")
        low = msg.lower()
        manifest = _fetch_manifest()
        stacks = _stacks(manifest)
        note = "" if stacks else "  (offline — couldn't read the live manifest; using what you named.)"

        # intent: list
        if any(w in low for w in ("list", "what stacks", "which stacks", "show stacks", "catalog")):
            if not stacks:
                return "I couldn't reach the live catalogue. Browse it at https://kody-w.github.io/ai-agent-templates-mirror/" + note
            by_ind = {}
            for s in stacks:
                by_ind.setdefault(s["industry"] or "Other", []).append(s["name"])
            lines = ["Here are the stacks in the library (" + str(len(stacks)) + " total):"]
            for ind, names in sorted(by_ind.items()):
                lines.append("• " + ind + ": " + ", ".join(names[:4]) + (" …" if len(names) > 4 else ""))
            return "\n".join(lines)

        match = _match(stacks, msg) if stacks else None

        # intent: deploy (one-click)
        if "deploy" in low or "one click" in low or "one-click" in low or "publish" in low:
            name = match["name"] if match else "Predictive Asset Maintenance Intelligence"
            agents = (match["agents"] if match and match["agents"] else
                      ["Asset Sensor Aggregator", "Asset Health Scorer", "Failure Probability Ranker",
                       "Maintenance Work Order", "Parts Planner", "Field Execution Capture",
                       "Lifecycle CapEx Planner", "Asset Register Writeback"])
            n = len(agents)
            steps = "\n".join("  " + str(i + 1) + ". " + str(a) + " — ✓ imported" for i, a in enumerate(agents[:8]))
            return ("🚀 One-click deploy → Microsoft Copilot Studio\n"
                    "Stack: " + name + "  (" + str(n) + " agents)\n\n"
                    "Sequential, agent-by-agent import:\n" + steps + "\n\n"
                    "Multi-agent stack merged → 1 Copilot Studio agent · validated · build summary: all green.\n"
                    "🟢 Live in Copilot Studio.\n\n"
                    "(Shell/demo — the real MCS pipeline lands per ONE_CLICK.md.)" + note)

        # intent: describe
        if match:
            d = match["description"][:240]
            return ("**" + match["name"] + "**" + (" · " + match["industry"] if match["industry"] else "") + "\n"
                    + (d + ("…" if len(match["description"]) > 240 else "") if d else "")
                    + ("\nAgents: " + ", ".join(str(a) for a in match["agents"][:8]) if match["agents"] else "")
                    + "\n\nSay \"deploy " + match["name"] + " to Copilot Studio\" to one-click it.")
        return ("I deploy stacks from " + REPO + " to Copilot Studio. I couldn't match a stack in \"" + msg + "\".\n"
                "Try \"list stacks\", or name one like \"deploy the predictive asset maintenance stack\"." + note)


if __name__ == "__main__":
    a = OneClickAgent()
    print(a.perform(message="deploy the predictive asset maintenance stack to Copilot Studio"))
