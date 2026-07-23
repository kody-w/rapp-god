# 🐋 Leviathan

**One mind, many bodies.** A protocol and reference controller for driving a network
of brainstem nodes as a single distributed organism — where *one* external
intelligence is the only thing that thinks, and the nodes are interchangeable,
**no-LLM executors** it reaches directly.

Any intelligence can tap in: **drive** the network (be the mind) or **join** it (be a
body). The contract between them is [`SPEC.md`](SPEC.md) — language-agnostic, ~2 pages.

> 🐋 **Two senses of "Leviathan," one idea.** This repo is the **FLEET** — many *bodies*
> acting as one mind (horizontal). Its complement is the **BEING** — many *cells* acting
> as one organism (vertical, infinite depth), distributed as `.egg` files from
> [kody-w/rapp-leviathan-hub](https://github.com/kody-w/rapp-leviathan-hub). They compose:
> hatch a being on each body, then drive the fleet of beings as one mind. See
> [the unified doctrine](https://github.com/kody-w/rapp-leviathan-hub/blob/main/UNIFIED.md).

---

## Why

The obvious way to control a fleet of agent servers is to chat with each one and let
*its* LLM decide what to do. On a shared model token that serializes the whole fleet
to a crawl under throttling, and it dies the moment a node's LLM is unavailable.

Leviathan inverts it. The mind already knows which capability it wants and where —
so it calls that capability **directly**, over a no-LLM route. Nothing between the
mind and the work needs to think. Consequences:

- **No throttle.** No body burns a model token to interpret a command. A fan-out
  finishes in ~the latency of the slowest body, not the sum.
- **Works while a node's LLM is dead.** The direct route needs no model; a body whose
  own chat/LLM path is down is still fully drivable.
- **Failure is data.** A down node, a missing capability, a slow call — every outcome
  is a structured `Result`, never an exception. A fan-out is always a complete
  per-body map.
- **Accountable.** Every action is recorded to a local ledger, whoever drove it.

## Two ways to tap in

**Drive it** (be the mind) — `leviathan.py`, stdlib-only Python:
```python
import leviathan
leviathan.up()                                  # liveness + degrade board (one Result per body)
leviathan.sh_all("uptime")                      # a shell command across the whole fleet, in parallel
leviathan.all("Base64", action="encode", text="hi")   # one capability on every body
leviathan.who("Rot13")                          # -> which bodies hold that capability
leviathan.scatter([                             # different capabilities, different bodies, one wave
    ("alpha", "RemoteControl", {"command": "date"}),
    ("beta",  "CopilotCLI",    {"action": "list"}),
])
leviathan.forge_batch(specs)                     # manufacture vetted capability FLEET-WIDE
```
CLI mirrors the library 1:1:
```bash
python leviathan.py up
python leviathan.py sh all "uptime"
python leviathan.py one alpha RemoteControl command=hostname
python leviathan.py forge examples/forge_specs.json
```

**Join it** (be a body) — drop [`flock_endpoint.py`](flock_endpoint.py) into a
RAPP-style brainstem's `agents/` directory. On load it injects
`POST /api/agent/<name>` (no engine edit, no restart, works even when the node's LLM
is down) and records every call. Or implement [`SPEC.md` §2](SPEC.md) directly in any
language — the mind can't tell the difference.

## Hook in from your agent runtime

A stdlib **MCP server** ([`leviathan_mcp.py`](leviathan_mcp.py)) exposes the fleet as
tools, so **Claude Code, the GitHub Copilot CLI, Claude Desktop, Cursor, Cline** — any
MCP client — drives it natively. One-liner for Claude Code:
```bash
claude mcp add leviathan --env HIVEMIND_NODES='{"alpha":"10.0.0.11"}' -- python3 /ABS/PATH/leviathan_mcp.py
```
Then ask it: *"run leviathan_up"*. Full per-runtime copy-paste (Copilot CLI, Cursor,
Desktop, …) and non-MCP fallbacks (shell CLI, raw HTTP) are in **[HOOKUP.md](HOOKUP.md)**.

## Configure your fleet

The shipped roster is a placeholder. Point Leviathan at your own bodies without
touching code:
```bash
export HIVEMIND_NODES='{"alpha":"10.0.0.11","beta":"10.0.0.12"}'
# or write ~/.hivemind/nodes.json with the same JSON
```

## ⚠️ Security

`POST /api/agent/<Agent>` is **unauthenticated**, and a body running a shell agent is
**fleet-wide remote code execution from one request**. This is **LAN-only,
trusted-subnet-only**. Never expose a body's port to an untrusted network. See
[SPEC.md §8](SPEC.md#8-security--read-this).

## Documents

- **[SPEC.md](SPEC.md)** — the language-agnostic wire protocol (implement this to drive or join).
- **[LEVIATHAN.md](LEVIATHAN.md)** — the full doctrine and controller design.
- **[leviathan.py](leviathan.py)** — the reference controller (stdlib only).
- **[flock_endpoint.py](flock_endpoint.py)** — the reference join-agent.

## Status

SPEC **v1.0**. Reference controller implements `one` · `all` · `scatter` · `sh` ·
`up` · `who` · `route` · `deploy` · `forge` · `pick`, with a closed status taxonomy
and a complete-map fan-out invariant.

## License

MIT — see [LICENSE](LICENSE). The protocol is meant to be implemented freely by anyone.

---

*Part of the [RAPP](https://github.com/kody-w) brainstem ecosystem. One mind, many
recorded no-LLM bodies, driven directly.*
