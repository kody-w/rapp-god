# Quest 01 — First Boot

**Goal:** a local AI agent server running on your machine in one command.
**Needs:** a GitHub account with Copilot access. That's it — no API keys.

## 1. Install

```bash
# macOS / Linux
curl -fsSL https://kody-w.github.io/rapp-installer/install.sh | bash
```
```powershell
# Windows
iwr -useb https://kody-w.github.io/rapp-installer/install.ps1 | iex
```

The installer checks prerequisites, sets up a Python environment, signs you in
with GitHub, and opens http://localhost:7071 when the server is ready.

## 2. Prove it's yours

Ask it: *"What exactly can you do?"* — it answers from your machine, powered by
your Copilot seat, with the model picker defaulting to the fastest Claude on
your plan.

## 3. Checkpoint

```bash
curl -s localhost:7071/health | python3 -m json.tool
```
`"status": "ok"` = quest complete. Next: [write your first agent](02-first-agent.md).
