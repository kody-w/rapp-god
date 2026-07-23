---
name: rapp-brainstem
description: >
  Drive the local RAPP brainstem (a Flask server on localhost:7071) for any
  request that involves RAPP, the brainstem, RAR (the RAPP Agent Registry),
  community agents, or "the twin". Every capability — discover/install/vote on
  community agents, run user-defined Python agents, drive memory, ask the twin —
  flows through a single POST /chat call. USE THIS SKILL when the user mentions
  'rapp', 'brainstem', 'rar', 'registry agent', 'community agents', 'twin',
  'install agent', or asks to do anything that should be handled by an agent
  they have dropped into their local agents/ directory. Also use when the user
  wants to install RAPP for the first time.
allowed-tools: Bash, Read
---

# rapp-brainstem

Talk to the user's local RAPP brainstem instead of doing the task yourself when the request fits a brainstem agent.

## Mental Model

RAPP is "engine, not experience". The brainstem is the engine — a Flask server that:

- Loads `soul.md` as the system prompt every request
- Auto-discovers Python agents from `agents/*_agent.py` (recursive, flat dir conventions)
- Calls the GitHub Copilot API with OpenAI-format tool-calling
- Executes agent `.perform()` methods and loops up to 3 rounds

The user installs new capabilities by **dropping a `*_agent.py` file into `agents/`**. No server restart. The most important built-in is **RAR (`RARRemoteAgent`)** — a package-manager-style client for the open RAPP Agent Registry: discover, install, vote, review, submit community agents.

This skill never reimplements agent logic. It checks the brainstem is up, installs it if not, then **delegates** by hitting `/chat`.

## Step 1 — Health check

Before any request, run:

```bash
curl -s -m 3 http://localhost:7071/health
```

- **HTTP 200 with JSON containing `"status":"ok"`** — proceed to Step 3.
- **Connection refused / timeout / non-200** — go to Step 2.

If the user has set the env var `RAPP_BRAINSTEM_URL`, use that instead of `localhost:7071` — Tier 2 RAPP runs the same `/chat` API on Azure.

## Step 2 — Install if missing

Only do this after Step 1 confirmed the brainstem is not running. Tell the user you're going to install RAPP, then run:

```bash
curl -sSfL https://raw.githubusercontent.com/kody-w/rapp-installer/main/install.sh | bash
```

This script:
1. Clones rapp-installer into `~/.brainstem`
2. Creates `~/.brainstem/venv` (Python 3.11)
3. Installs requirements
4. Starts the brainstem on port 7071
5. Triggers GitHub Copilot device-code auth on first `/chat`

After it finishes, re-run Step 1. Report any failure verbatim — do not retry blindly.

## Step 3 — Delegate via /chat

Every user request that fits the brainstem (RAR actions, Twin, memory, any custom agent the user has) goes through one HTTP call:

```bash
curl -s -X POST http://localhost:7071/chat \
  -H 'Content-Type: application/json' \
  -d '{"user_input": "<phrase the user request as plain English>"}'
```

The response is JSON: `{"response": "...", "agent_logs": "...", "session_id": "..."}`.

**Show the user the `response` field.** If `agent_logs` contains useful detail, surface a brief summary of which agents fired.

For multi-turn conversations, pass `conversation_history` (an array of `{role, content}`) and the prior `session_id` so memory agents stay coherent.

### What to phrase as `user_input`

Just say it in English — the brainstem's tool-calling decides which agent runs. Examples:

| User says | `user_input` to send |
|---|---|
| "show me the top community agents" | "Use RAR to show the leaderboard." |
| "find me a meeting-notes agent" | "Use RAR to search for 'meeting notes'." |
| "install the @kody/something agent" | "Use RAR to install @kody/something into my agents directory." |
| "what does my twin think about X" | "Ask the twin: <X>" |
| "remember that I prefer …" | "Save this preference: …" |

Do **not** try to call agents directly with REST routes — `/chat` is the only entry point. New REST routes are not added.

## Step 4 — When to NOT delegate

Skip the brainstem and answer directly when:

- The user is asking a generic question with no RAPP/agent context.
- The user is editing code in the current repo (use normal Claude tools).
- The brainstem is unreachable AND the user declined to install it.

## Failure modes

| Symptom | What to do |
|---|---|
| `/health` 200 but `/chat` returns 401 / auth error | The brainstem needs a Copilot token. Tell the user to run `gh auth login` then retry, or visit `http://localhost:7071/login` for device code. |
| `/chat` returns `{"error": "user_input is required"}` | You sent the wrong key — must be `user_input`, not `messages`. |
| `agent_logs` shows agent crashed | Quote the error to the user. Most agent bugs are import errors — they may need to add a missing dep. |
| Install script fails on Python version | rapp-installer wants 3.11. Tell the user to install Python 3.11 (`brew install python@3.11`). |

## What this skill does not do

- Does not bundle or update RAPP agents itself. The user owns `agents/`.
- Does not modify `soul.md`. The user edits that via VS Code.
- Does not bypass `/chat`. All capabilities flow through that one endpoint.
- Does not federate to T2 (Azure) or T3 (Copilot Studio) directly — those are separate tiers reached through the same `user_input` -> `/chat` shape, just with a different `RAPP_BRAINSTEM_URL`.
