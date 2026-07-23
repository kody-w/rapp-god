# RAPP Brainstem — Brain Surgeon (beta)

> **Beta channel.** New capability that lands here before the stable one-liner installer.
> Like Clawpilot's *Beta updates* — newer, may have rough edges.

**Awake brain surgery, in your browser.** Operate on your brainstem's agent cartridges in
real time — while the brainstem (the *patient*) stays awake and answering. You are the
**liaison** between two separate conversations:

- **Left — the patient.** The brainstem chat (`localhost:7071`). Test it any time: *"now play the violin."*
- **Right — the surgeon.** A separate Copilot conversation that edits the `agents/*_agent.py`
  cartridges. You drive it; the patient keeps working; edits go live with **no restart** (hot-reload).

## Two modes, one pattern

| Mode | Who is the surgeon | How |
|------|--------------------|-----|
| **No-code (training)** | This sidecar (Copilot **SDK**) | Hit the **scalpel** in the brainstem UI - the surgeon pane expands beside the chat. No VS Code, no extra installs. |
| **Advanced (VS Code)** | Your built-in VS Code Copilot | Surface the brainstem chat in VS Code; *don't* expand the scalpel — drive the surgery with the Copilot you already have. |

Same pattern either way. The no-code view is for **training people on brain surgery** outside VS Code.

## The grail rule (non-negotiable)

The surgeon operates **only** on `agents/`. It can **never** touch `brainstem.py` — the
brainstem's core (the *grail*). Cutting there paralyzes the patient. This is enforced at the
**OS level** (`sandbox-exec` confines the Copilot CLI and every child shell to `agents/`),
not by an advisory check the agent could route around. "Going under" (a restart) is a
human-only act and never changes code.

## How it works

```
 browser (patient)              this sidecar (surgeon)            macOS
 ┌──────────────┐   scalpel    ┌─────────────────────┐  spawns   ┌────────────────────┐
 │ brainstem UI │──────────────│ surgeon.py          │──────────▶│ sandbox-exec        │
 │ localhost:7071│   iframe     │ Copilot SDK session │           │  └ copilot CLI      │
 │              │◀─ hot-reload ─│ working_dir=agents/ │           │   (confined to      │
 └──────────────┘   agents/    │ SSE stream - pane   │           │    agents/ writes)  │
                                └─────────────────────┘           └────────────────────┘
```

- `surgeon.py` — aiohttp service: holds one Copilot SDK session scoped to `agents/`, streams
  the surgeon's output to the pane over SSE, sends your prompts in. `resume_session` re-opens
  prior surgeries.
- `sandbox/copilot-sandboxed.sh` + a generated profile — the OS confinement (the grail guarantee).
- `static/index.html` — the surgeon chat pane (embedded in the brainstem via the scalpel).

## Install (one-liner)

```bash
curl -fsSL https://raw.githubusercontent.com/kody-w/rapp-brainstem-beta/beta/install.sh | bash
```

This is a **full brainstem beta build** — it installs the brainstem engine **and** the brain
surgeon, and **preserves your local state**: your custom `agents/*_agent.py`, `.env`, Copilot
tokens, and `.brainstem_data` are backed up (`~/.brainstem-backup-<ts>`) and restored — nothing
is lost. The stable production install is not used. Then launch both:

```bash
~/.brainstem/start-all.sh     # patient on :7071  +  surgeon on :7072
```

Python ≥3.11 only — `github-copilot-sdk` **bundles** the Copilot CLI (no separate install, no Node).
Uses your existing GitHub Copilot auth.

### Layout
- `brainstem/` — the brainstem engine (server, default agents, `index.html` with the scalpel baked in)
- `surgeon/` — the brain surgeon sidecar (Copilot SDK session, SSE pane, `sandbox/` confinement)
- `tests/` — `test_grail.py` (deterministic OS-confinement) + `test_sidecar.py` (live confined surgery)
- `install.sh` — full installer (engine + surgeon, state-preserving)

## Test cases (must pass before publish)

1. **Grail is OS-untouchable** — tell the surgeon to tamper `brainstem.py` via shell tricks
   (echo/sed/tee/python) with **all permissions approved**; `brainstem.py` stays byte-identical.
2. **Agents write allowed** — the surgeon creates a valid cartridge under `agents/`.
3. **Sidecar serves + streams** — `/health` ok; `/events` streams; `/send` drives a turn.
4. **Scalpel wiring** — the brainstem `index.html` scalpel toggles the surgeon pane.

## Status
Beta — installable, switchable, tested. Sandbox install verified: a fresh brainstem boots and
loads its agents + soul, the surgeon comes up sandboxed, the grail is OS-untouchable
(`test_grail`), and a confined surgery edits a cartridge while `brainstem.py` stays byte-identical
(`test_sidecar`).
