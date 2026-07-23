# Spec: RAPP single-file agent contract

> Self-contained reference for the LLM that's bootstrapping this neighborhood. Tells you everything you need to know about what makes a valid RAPP agent so you can read, validate, install, and (if asked) generate them correctly.

## The contract

A RAPP agent is **one Python file** containing:

1. **One class** that extends `BasicAgent`.
2. **One `perform(self, **kwargs) -> str` method** that returns a JSON string.
3. **One `metadata` dict** declaring the agent's name, description, and OpenAI-compatible parameter schema.

That's it. No build step. No registration file. No multi-file imports beyond `agents.basic_agent`. No framework. No scaffolding.

## Minimum valid agent

```python
"""hello_agent — minimum-viable RAPP agent example."""

import json

try:
    from agents.basic_agent import BasicAgent
except ImportError:
    from basic_agent import BasicAgent


class HelloAgent(BasicAgent):
    metadata = {
        "name": "Hello",
        "description": "Greets the operator. Use when they say hello.",
        "parameters": {
            "type": "object",
            "properties": {
                "who": {"type": "string", "description": "Name to greet."},
            },
            "required": [],
        },
    }

    def __init__(self):
        self.name = "Hello"

    def perform(self, **kwargs) -> str:
        who = kwargs.get("who", "world")
        return json.dumps({"ok": True, "greeting": f"hello, {who}"})
```

## File naming

Filename pattern: `<slug>_agent.py`. Lowercase, underscore-separated, ends in `_agent.py`. The brainstem auto-discovers via glob `agents/*_agent.py`.

## Discovery + hot-load

The brainstem reads the `agents/` directory on EVERY chat request. To add an agent: drop the file in. No restart. No registration. To remove: delete the file.

Default `AGENTS_PATH` is `<brainstem_dir>/agents/`. Override via env var.

## perform() rules

- MUST return a `str`. Recommended: `json.dumps({...})`.
- MUST NOT raise. Catch your own exceptions and return `{"ok": false, "error": "..."}`.
- SHOULD be idempotent where possible.
- May call other agents directly (import + instantiate + call) — this is the rapplication-renderer pattern.

## metadata dict rules

- `name` — short PascalCase identifier the LLM uses to reference the agent.
- `description` — one paragraph telling the LLM when to use this agent. Put trigger words ("use when...", "use this for...") at the start.
- `parameters` — OpenAI tool-calling schema. JSON Schema subset. The LLM uses this to fill in arguments.

## What an agent CAN do

- Read/write files anywhere the operator's user can.
- Make HTTP calls (urllib, requests if installed).
- Shell out via subprocess.
- Import other agents.
- Read/write `~/.brainstem/.brainstem_data/<name>.json` for shared state.

## What an agent MUST NOT do

- Modify `~/.brainstem/rappid.json` (immutable per kernel Article XLVI).
- Modify `~/.brainstem/bonds.json` outside the bond.py contract.
- Push to the public internet without explicit operator consent.
- Commit + push git changes without explicit operator consent.
- Write customer data into the this neighborhood workspace repo (Article I — Local Device Is Canonical).

## Validating an agent before installing

1. File ends in `_agent.py`.
2. File has `from agents.basic_agent import BasicAgent` (or the fallback).
3. File defines exactly one class extending `BasicAgent`.
4. The class has both `metadata` and `perform`.
5. The file's sha256 matches the manifest entry in `rar/index.json` if installing from a rar.

If you (the LLM) are asked to write a new agent, follow this contract exactly. If asked to install one from disk, run the five validation checks first.

## See also

- this neighborhood neighborhood constitution: `../CONSTITUTION.md`
- Manifest format: `RAR_INDEX.md`
- How agents fit into the neighborhood: `NEIGHBORHOOD_PROTOCOL.md`
- Kernel constitution Article XXXIII (single-file agents): https://github.com/kody-w/RAPP/blob/main/CONSTITUTION.md
