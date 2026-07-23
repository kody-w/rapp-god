# Microsoft 365 Team

A planted RAPP neighborhood for Microsoft Solution Engineers. Local-first workflow + per-operator workspaces + sha256-pinned agents + sneakernet-portable + integrated with Microsoft 365 via WorkIQ.

## What's in here

| Layer | What |
|---|---|
| **Workflow** | Intake / OutcomeFramer / Pm / OutcomeValidator / EngagementFactory — the gate-everything-on-outcome SE pattern |
| **M365 connector** | `WorkIQ` agent — natural-language access to your tenant's emails / calendar / docs / Teams (via `@microsoft/workiq` CLI) |
| **Twin** | Microsoft-stack-shaped twin with field patterns for Copilot Studio YAML, AppReg consent delays, Power Platform stack-routing, AI grounding |
| **Dashboard** | Per-operator HTML dashboard hydrated deterministically from the workflow agents |
| **Workspace primitive** | Each operator gets a per-handle workbench at `~/.brainstem/workbenches/microsoft-365-team/<handle>/` — customer data stays on device, never enters this repo |

## Get set up in one chat

You have a brainstem running and the `egg_hatcher_agent.py` in your `agents/` directory.

**From the egg you received (sneakernet flow):**
```
hatch the egg I just downloaded
```

**Or from this repo (online flow):**
```
join the kody-w/microsoft-365-team neighborhood
```

The bootstrap unpacks, sha256-verifies, installs all 11 workflow agents, mints your rappid + per-handle workspace + local data dir, records the subscription. ONE chat, complete setup.

## Use this as YOUR template

This repo is a GitHub template. Click "Use this template" in the GitHub UI to fork your own copy under your handle, then mutate the soul / agents / branding for your specific MS team. The `EggHatcher pack_egg=true` workflow lets you re-pack your fork as a fresh sneakernet payload to share with your colleagues.

## Reading order

1. [`onboarding.html`](onboarding.html) — friendly visual entry
2. [`QUICK_START.md`](QUICK_START.md) — 1-page reference
3. [`SETUP.md`](SETUP.md) — all three setup modes (egg / repo / pack)
4. [`SKILL.md`](SKILL.md) — feed to your LLM to drive setup
5. [`CONSTITUTION.md`](CONSTITUTION.md) — 8 articles governing this neighborhood (PII never leaks back to repo, etc.)
6. [`specs/`](specs/) — agent contract, neighborhood protocol, manifest format

## What goes where (per kernel PUBLIC_PRIVATE_BOUNDARY §1.5+§1.7+§1.8)

| Lives in this repo (the bones) | Lives ONLY on YOUR device (the substance) |
|---|---|
| `agents/*` — sha256-pinned workflow | Customer names, contracts, emails, contacts |
| `ses/<your-handle>/projects.json` — slugs + status only | `~/.brainstem/neighborhoods/microsoft-365-team/<handle>/customers/<slug>/` — all customer data |
| `members.json` — handles + roles | Personal notes, drafts, attachments |
| `CONSTITUTION.md` + `rar/index.json` + `soul.md` | Every WorkIQ query result, every M365 context pull |
| **ZERO PII by default** | Everything that would identify your customer |

The repo's `.gitignore` excludes `.brainstem/` so customer data physically cannot be `git add`ed even by accident.

## Identity

- **Rappid:** see `rappid.json`
- **Owner:** `kody-w`
- **Slug:** `microsoft-365-team`
- **Visibility:** see `neighborhood.json` (`visibility` field)
- **Parent:** [kody-w/RAPP](https://github.com/kody-w/RAPP) (the kernel)
- **Template:** [kody-w/microsoft-365-team](https://github.com/kody-w/microsoft-365-team)
