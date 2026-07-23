# Hook in — drive the Leviathan from Claude Code, Copilot CLI, Cursor, or anything

The Leviathan ships an **MCP server** (`leviathan_mcp.py`, stdlib only, zero deps).
Any agent runtime that speaks the Model Context Protocol becomes "the mind" and
drives your fleet of no-LLM bodies natively. Below: a one-time setup, then copy-paste
for each runtime, then non-MCP fallbacks.

## 0. One-time

```bash
git clone https://github.com/kody-w/leviathan && cd leviathan
# point it at YOUR fleet (logical name -> ip of a body running flock_endpoint.py):
export HIVEMIND_NODES='{"alpha":"10.0.0.11","beta":"10.0.0.12"}'
#   ...or write the same JSON to  ~/.hivemind/nodes.json  (no env needed)
ABS=$(pwd)/leviathan_mcp.py    # absolute path you'll paste below
python3 leviathan.py up        # sanity check it can see your fleet
```
The server exposes 8 tools: `leviathan_up`, `leviathan_sh`, `leviathan_one`,
`leviathan_all`, `leviathan_scatter`, `leviathan_who`, `leviathan_deploy`,
`leviathan_forge`.

## Claude Code

```bash
claude mcp add leviathan --env HIVEMIND_NODES='{"alpha":"10.0.0.11"}' -- python3 /ABS/PATH/leviathan_mcp.py
```
Or commit a project-scoped `.mcp.json`:
```json
{ "mcpServers": { "leviathan": {
  "command": "python3",
  "args": ["/ABS/PATH/leviathan_mcp.py"],
  "env": { "HIVEMIND_NODES": "{\"alpha\":\"10.0.0.11\",\"beta\":\"10.0.0.12\"}" }
} } }
```
Then just ask: *"run leviathan_up"* or *"use leviathan_sh to run `uptime` on all bodies."*

## GitHub Copilot CLI

The Copilot CLI reads `~/.copilot/mcp-config.json`:
```json
{ "mcpServers": { "leviathan": {
  "command": "python3",
  "args": ["/ABS/PATH/leviathan_mcp.py"],
  "env": { "HIVEMIND_NODES": "{\"alpha\":\"10.0.0.11\"}" }
} } }
```
…or pass it per-session: `copilot --additional-mcp-config @/ABS/PATH/leviathan-mcp.json`.
Inside the CLI, `/mcp` lists it; then ask it to use the `leviathan_*` tools.

## Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or
`%APPDATA%\Claude\claude_desktop_config.json` (Windows), then restart:
```json
{ "mcpServers": { "leviathan": {
  "command": "python3",
  "args": ["/ABS/PATH/leviathan_mcp.py"],
  "env": { "HIVEMIND_NODES": "{\"alpha\":\"10.0.0.11\"}" }
} } }
```

## Cursor / Cline / Windsurf / Continue / any MCP client

Same server. Cursor: `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (project):
```json
{ "mcpServers": { "leviathan": { "command": "python3", "args": ["/ABS/PATH/leviathan_mcp.py"] } } }
```
Cline/Continue/Windsurf expose an MCP settings file or UI — give it the same
`command`/`args`/`env`.

## No MCP? Two universal fallbacks

- **Shell / CLI** — anything that can run a command (any agent, any script, cron):
  ```bash
  python3 leviathan.py up
  python3 leviathan.py sh all "uptime"
  python3 leviathan.py one alpha RemoteControl command=hostname
  python3 leviathan.py forge examples/forge_specs.json
  ```
- **HTTP** — any language: implement the controller calls in [`SPEC.md`](SPEC.md) §2
  directly. A body is just `POST http://<ip>:7071/api/agent/<Agent>` with JSON kwargs.

## Verify

After registering, ask your agent to **"run leviathan_up"** — you should get the
fleet's liveness board. If a body shows `llm:down` but `ok`, that's expected: it's
still fully drivable, because the Leviathan path never touches a body's LLM.

> ⚠️ The bodies expose unauthenticated remote execution — **LAN-only, trusted-subnet
> only** (see [SPEC.md §8](SPEC.md#8-security--read-this)). The MCP server inherits
> whatever fleet you point `HIVEMIND_NODES` at.
