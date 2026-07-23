# 🧠 rapp-dataverse

**Run RAPP on out-of-the-box Dataverse — no custom tables, no custom fields, no solution import.**
A public static **vTwin** so you're never blocked by lacking an environment, and a **CLI** that
hatches the brainstem into a real instance by twin sync, ready to chat in **Copilot Studio**.

→ **The spec: [`SPEC.md`](SPEC.md)** (`rapp-dataverse/1.0`).

## What's here

| Path | What |
|------|------|
| [`SPEC.md`](SPEC.md) | The spec: OOTB encoding, the brainstem loop, the vTwin, the hatcher, conformance |
| [`chat/`](chat/) | **Browser vBrainstem** — live chat grounded by the vTwin, reasoning via the GitHub Copilot API |
| [`twin/`](twin/) | The **vTwin** — a server-less, OData-shaped Dataverse Web API (a 1:1 digital twin) |
| [`cli/`](cli/) | **`rapp-dv`** — the CLI hatcher (twin sync into a real Dataverse via an application user) |
| [`brainstem/`](brainstem/) | The OOTB mapping, AI Builder **router prompt**, and Power Automate **orchestrator flow** |

## Chat with it now (browser, GitHub Pages)

[**`chat/`**](https://kody-w.github.io/rapp-dataverse/chat/) is a single-page vBrainstem:
**grounding** (soul, agents, memory, history) is read live from the static **Dataverse vTwin**, and
the **GitHub Copilot API** drives the reasoning and tool-calls — the same brainstem loop as
`brainstem.py`, but with the inference engine swapped for Copilot instead of Power Platform AI
Builder. Add a GitHub token (with Copilot access) in Settings — it's exchanged for a Copilot token
in your browser and never leaves it.

## Quickstart — zero setup (no Dataverse needed)

The CLI defaults to the **global vTwin**, so every read works out of the box:

```bash
cd cli
python3 rapp_dv.py whoami        # Mode: vTwin · global static Dataverse
python3 rapp_dv.py agents list   # EchoAgent, CalculatorAgent … (live from the vTwin)
python3 rapp_dv.py chat "what is 6 * 7?"   # grounded brainstem context (shared vs user memory)
python3 rapp_dv.py compare       # diff against the global brainstem
```

Live vTwin: `https://kody-w.github.io/rapp-dataverse/twin/` ·
raw: `https://raw.githubusercontent.com/kody-w/rapp-dataverse/main/twin/`

## Hatch into a real Dataverse

```bash
export RAPP_DV_URL=https://yourorg.crm.dynamics.com
export RAPP_DV_TENANT=<tenant>  RAPP_DV_CLIENT_ID=<app>  RAPP_DV_CLIENT_SECRET=<secret>

python3 rapp_dv.py hatch         # replicate the global brainstem into your instance (identical)
python3 rapp_dv.py compare       # ✅ IN SYNC with the global brainstem
```

Then wire a **Copilot Studio** topic to the [orchestrator flow](brainstem/orchestrator_flow.md) and
you have a grounded chatbot. Full app-user setup + Copilot Studio steps: [`cli/README.md`](cli/README.md).

## How it maps (RAPP → OOTB Dataverse)

`account` "RAPP System" (soul) · `contact` (users) · `annotation` (everything else: agents with
`agent.py` in `notetext.sourcecode`, memory, conversations, messages — discriminated by a `rapp.*`
`subject`). Memory scope = the note's regarding object (account = shared, contact = user). See
[`brainstem/OOTB_MAPPING.md`](brainstem/OOTB_MAPPING.md).

MIT © Kody Wildfeuer. Part of the RAPP ecosystem. The vTwin is served per
[`rapp-static-api/1.0`](https://github.com/kody-w/rapp-static-apis).
