# One-Click Deploy — placeholder (to be landed)

> **Status: scaffold only.** This repo is a **mirror** of
> [kody-w/AI-Agent-Templates](https://github.com/kody-w/AI-Agent-Templates) — the stack library that
> the one-click deploy operates on. The deploy pipeline itself is **not built here yet**; this file
> reserves the shape so it can be landed cleanly.

## Try it

- **Live demo (this process, end-to-end):** [`oneclick-demo/`](oneclick-demo/) — a synced,
  scan-to-watch **M365 Copilot** demo of one-click deploying the **Predictive Asset Maintenance
  Intelligence** stack (8 agents → one Copilot Studio agent). Open it, drive it with **Next ▶**; hit
  **📷 Share** and scan the QR to watch it live on another device.
  → https://kody-w.github.io/ai-agent-templates-mirror/oneclick-demo/
- **Conversational agent (shell):** [`OneClick_agent.py`](OneClick_agent.py) — a single-file agent
  pointed at this repo. Drop it in a brainstem and say *"deploy the predictive asset maintenance
  stack to Copilot Studio."* Shell/demo: it reads this repo's `manifest.json`, finds the stack, and
  narrates the sequential MCS deploy. The real pipeline lands below. (All synthetic — no PII.)

## Goal

One-click deploy each agent stack to **Microsoft Copilot Studio (MCS)** — agent-by-agent, with a
**stack folder as the unit of deployment** (see [`STACK_LIBRARY_SPEC.md`](STACK_LIBRARY_SPEC.md) for
the on-disk layout this consumes).

## The process this lands (per the 05/18–05/22 deployment work)

- **Standalone MCS agent model** (the bypass Azure Function approach was refactored out) for
  maintainability, scalability, and architectural alignment.
- **Sequential one-click**: agent-by-agent import flow, not bulk import.
- **Stack-level folder deployment**: each `agent_stacks/{industry}_stacks/{stack_id}/` folder is
  processed as one deployment unit.
- **Single- and multi-agent stacks**: including cases where multiple `*_agent.py` files are
  **merged** and processed as one agent.
- **Validation + reporting**: success / failure / partial-success captured clearly in the
  Azure DevOps build summary.

## Where it lands (reserved)

```
.github/workflows/one-click-deploy.yml   # ADO/GitHub pipeline trigger (TODO)
deploy/                                   # the MCS deploy scripts (TODO)
  ├── deploy_stack.py                     # process one stack folder → MCS agent(s)
  ├── merge_agents.py                     # merge multi-agent stacks into one .py
  └── report.py                           # success/failure/partial → build summary
```
Two deploy paths already exist alongside this for reference:
`azuredeploy.json` (one-click Azure Function deploy) and the stack catalogue's `index.html`.

## Known blockers / dependencies (from the deployment notes)

- **Key Vault networking** access must be enabled to retrieve secrets at deploy time.
- **Microsoft-hosted agent minutes** are capped (200 min/month) — budget pipeline test runs.
- Some **native connectors are disabled by DLP** — affected agents/connectors:
  BeehiivRSS (RSS), Dynamics365CRUD / Dynamics365DemoDataSeeder / MeetingPrep / m365_demo_updater
  (Dataverse), ContextMemoryAgent / ManageMemoryAgent (Azure File Share), SalesforceQuery
  (Salesforce), ServiceNow (ServiceNow).

## Land-it checklist

- [ ] Add the ADO/GitHub pipeline (`one-click-deploy.yml`) — sequential, stack-by-stack.
- [ ] Add `deploy/deploy_stack.py` (standalone MCS agent model) + `merge_agents.py`.
- [ ] Wire success/failure/partial reporting into the build summary.
- [ ] Resolve Key Vault networking + DLP connector exceptions per environment.
- [ ] Test against industry-level stacks on the customer repository.
