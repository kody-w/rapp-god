# rapp-brainstem-sdk

`vbrainstem_sdk.py` — a single‑file, **stdlib‑only** headless SDK that runs RAPP single‑file agents
in real CPython and serves the **`brainstem.py` `/chat` contract** over a port. The headless twin of
the browser [vBrainstem](https://github.com/kody-w/vbrainstem): same agents, same contract, no
browser — so `curl`, a skill, an agent, CI, or any MCP client can drive a brainstem.

Everything reaches the brainstem through the one wire (`/chat` — "Chat Is The Only Wire"); these
are all Layer-2 callers of it, not new units. MCP is just another transport on that wire:
[rapp-mcp](https://github.com/kody-w/rapp-mcp) (`rapp_brainstem_mcp.py`, `rapp-mcp-spec/1.0`)
bridges a running brainstem over the full `/chat` (LLM + memory + agents) to any MCP host — the
transport-layer sibling of this SDK.

## Use it

```bash
python3 vbrainstem_sdk.py serve --port 7173          # HTTP API on a port (CORS-enabled)
python3 vbrainstem_sdk.py run @kody-w/hello_world_agent "hi"
python3 vbrainstem_sdk.py agents --grep fraud
python3 vbrainstem_sdk.py eval "import sys; print(sys.version)"
```

HTTP:

```
GET  /health                       → {status, agents, runtime, registry}
GET  /agents[?grep=]               → {agents:[…]}
POST /run   {slug, request, args}  → {executed, output|error, ran_class, agent, slug}
POST /eval  {code}                 → {output}
POST /chat  {user_input, conversation_history, session_id}
                                   → {response, session_id, agent_logs, voice_mode}   # brainstem.py contract
```

It loads the live [RAR](https://github.com/kody-w/RAR) registry and runs agents in real CPython
(full stdlib, real network + filesystem), so secret/network agents work. Secrets via `os.environ`.

Part of the RAPP ecosystem — see the [map](https://github.com/kody-w/rapp-map). Also: bring this
into any MCP host via [rapp-mcp](https://github.com/kody-w/rapp-mcp) (the same `/chat` over an MCP
transport). MIT © Kody Wildfeuer.
