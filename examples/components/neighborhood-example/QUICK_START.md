# Quick start

The terse 1-pager. For the visual version see `onboarding.html`. For all setup modes see `SETUP.md`.

## You have a brainstem + the egg

```
1. Drag egg_hatcher_agent.py into your brainstem's agents/ folder
2. In chat:  EggHatcher from_egg=/path/to/neighborhood-example.egg
```

Done. Ask `Twin intro` for orientation.

## You have a brainstem + GitHub access

```
1. Drag egg_hatcher_agent.py into your brainstem's agents/ folder
2. In chat:  EggHatcher from_repo=kody-w/neighborhood-example
```

## You don't have a brainstem yet

One-time install:

```
curl -fsSL https://kody-w.github.io/RAPP/installer/install.sh | bash
```

Then either of the above.

## Let your LLM drive

Open `SKILL.md` in any chat with Claude / GPT / Copilot / local Ollama. The LLM walks you through, refusing to violate the constitution.

## What you have after setup

| Agent | Try it |
|---|---|
| `Twin` | `Twin intro` · `Twin walkthrough` · `Twin next_move` |
| `Intake` | `Intake log_idea title="..." body="..."` |
| `OutcomeFramer` | `OutcomeFramer frame_outcome use_case="..." owner=<handle>` |
| `Pm` | `Pm propose_sprint sprint_capacity=3` |
| `OutcomeValidator` | `OutcomeValidator validate_outcome ...` |
| `EngagementFactory` | `EngagementFactory slug=acme customer_name="Acme" ask="..."` |
| `ProjectPinger` | `ProjectPinger team_status` · `ProjectPinger status` |
| `DashboardRender` | `DashboardRender` (then open the file URL it returns) |
| `EggHatcher` | `EggHatcher pack_egg=true` (lay a new egg to share) |

## The boundary

Customer data lives ONLY at `~/.brainstem/neighborhoods/neighborhood-example/<your-handle>/customers/`. The workspace's `.gitignore` excludes `.brainstem/`. Never `git add` customer data. See [Article I](CONSTITUTION.md#article-i--the-local-device-is-canonical).
