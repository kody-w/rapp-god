# AGENT_SPEC — single-file `*_agent.py` (rapp-agent/1.0)

> **Frozen excerpt** of the canonical agent contract. Bundled at planting time on 2026-05-09T15:45:28Z.

A RAPP agent is **one file = one class = one `metadata` dict = one `perform()` method.** That's the entire contract. Drop the file in `agents/`; the brainstem auto-discovers it on next request — no restart, no build step, no framework.

## Required structure

```python
"""<one-line description>.

<Longer description: what this agent does, when to use it, what it returns.>
"""

try:
    from agents.basic_agent import BasicAgent
except ImportError:
    from basic_agent import BasicAgent


class MyExampleAgent(BasicAgent):
    metadata = {
        "name":        "MyExample",
        "description": "<what this agent does — read by the LLM to know when to call>",
        "parameters":  {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "..."},
            },
            "required": ["topic"],
        },
    }

    def __init__(self):
        self.name = "MyExample"

    def perform(self, **kwargs) -> str:
        topic = kwargs.get("topic", "")
        # do work
        return json.dumps({"schema": "rapp-my-example-result/1.0", "ok": True, ...})
```

## Filename convention

`<verb>_<object>_agent.py` — e.g. `manage_memory_agent.py`, `bond_rhythm_agent.py`, `plant_seed_agent.py`. Lives in `agents/` (NOT subdirectories — flat only).

## What `perform()` returns

A JSON-serializable string. Conventionally: `{"schema": "rapp-<name>-result/1.0", "ok": bool, ...payload}`. The brainstem feeds this back to the LLM as the tool result.

## What metadata.parameters declares

OpenAI function-calling schema — the LLM uses it to decide when + how to call this agent. Required fields go in `required`; optional fields just appear in `properties`.

## Neighborhood-local agents

This neighborhood can ship its OWN agents in `../agents/` (alongside the rar/ kit). They're discovered + loaded by any brainstem that subscribes to this neighborhood. Same contract as the canonical kernel agents.

## Hard rules

- **One file, one class, one perform.** No sibling imports; no build step.
- **Operator-mediated for global writes.** Default `dry_run=True` for any agent that touches the network or shared state (per ANTIPATTERNS §9).
- **No fake/deterministic mode.** Real LLM calls or real work — never pre-scripted persona shortcuts (per `feedback_no_fake_mode`).
- **Use the right schema.** Search `HOLOCARD_SPEC.md` and the parent's ECOSYSTEM_MAP first. Don't reinvent envelopes.

---

*Schema: `rapp-agent/1.0`. The plugin unit is always called an **agent** — never `skill` / `routine` / `loop` / `plugin` (per ANTIPATTERNS §1).*
