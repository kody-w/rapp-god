# RAPP Skills

Portable [Agent Skills](https://agentskills.io/) for non-RAPP agent systems.
Each capability lives in its own directory with a standards-compatible
`SKILL.md`.

This repository is also a design staging area for RAPP agents. A skill can be
prototyped here for broad compatibility, then converted into a single-file
`*_agent.py` implementation with its actual source and manifest preserved.
RAPP runtime capabilities remain **agents**, not skills.

## Skills

| Skill | Purpose | RAPP conversion target |
|---|---|---|
| [`deep-research`](deep-research/SKILL.md) | Evidence-first research using independent collection, experiment, verification, and synthesis tracks | `deep_research_agent.py` |
| [`rapp1-compliance-sweep`](rapp1-compliance-sweep/SKILL.md) | Literal file/archive RAPP/1 rev-5 audits, target-owned remediation, trust-aware verdicts, and estate recursion | `rapp1_compliance_sweep_agent.py` |

## Workflow skills (RAPP working set)

Battle-tested skills imported from the RAPP (Rapid Agent Prototyping Platform)
workflow — automation verbs for building, deploying, verifying, and demoing AI
agents, plus general working-style skills. Sanitized for publication:
environment-specific values are placeholders like `<function-app>` /
`<resource-group>`; adapt paths, resource names, and trigger phrasing to your
own setup.

### RAPP / agent pipeline
- [`rapp-brainstem`](rapp-brainstem/SKILL.md) — drive the local RAPP brainstem (Flask on :7071) through its single `/chat` endpoint; installs RAPP if missing.
- [`rapp-pipeline`](rapp-pipeline/SKILL.md) — run the transcript→agent pipeline: projects, quality gates, Copilot Studio + Azure DevOps outputs.
- [`brainstem-reset`](brainstem-reset/SKILL.md) — verified fresh-install test of the brainstem, exactly as a first-time user would get it.

### Deploy + verify (the "never hand back unverified" family)
- [`demo-ship`](demo-ship/SKILL.md) — deploy agents to an Azure Function, prove them e2e against the LIVE endpoint, generate an M365-styled HTML demo page, open, notify.
- [`mcs-deploy`](mcs-deploy/SKILL.md) — Copilot Studio solution import/publish with fresh version naming, children-first publish order, and real question/answer verification.
- [`ship`](ship/SKILL.md) — commit → push → GitHub Pages → marker-verified live URL.
- [`exec-proof`](exec-proof/SKILL.md) — pre-demo smoke test on a machine that is NOT yours; GO/NO-GO per platform with evidence.
- [`flex-unbrick`](flex-unbrick/SKILL.md) — runbook for Azure Flex Consumption apps bricked by a tenant policy that silently disables storage public network access (includes `scripts/unbrick.sh`).
- [`film-m365`](film-m365/SKILL.md) — film a Copilot Studio agent in the real M365 Copilot surface via Playwright + CDP recording, with a QA gate.

### Working style
- [`msft-deck`](msft-deck/SKILL.md) — build/restyle/revise .pptx decks in a Microsoft Fluent style with a mandatory visual self-review loop.
- [`muscle`](muscle/SKILL.md) — the cortex/muscle delegation loop: hand bulk artifact generation to a background CLI model, gate-check the result hands-on, add judgment last.
- [`overnight`](overnight/SKILL.md) — an unattended improve-to-120 loop with a verifiable ledger and per-pass commits.
- [`wow`](wow/SKILL.md) — demo-prompt generator with a persistent ledger so suggestions never repeat.
- [`transcript-miner`](transcript-miner/SKILL.md) — mine your own Claude Code session JSONL for usage patterns, error signatures, and skill candidates (includes `scripts/mine.py`).
- [`estate-sweep`](estate-sweep/SKILL.md) — clone-and-lint drift sweep across all public repos (includes `scripts/sweep.sh`).
- [`fy27-priority-agents`](fy27-priority-agents/SKILL.md) — a report-refresh pipeline pattern: grounded extraction → human verification → template-preserving render.

### Vault / twin
- [`obsidian-vault-steward`](obsidian-vault-steward/SKILL.md) — treat an Obsidian vault as the primary memory system (includes VAULT-STANDARDS.md).
- [`harvest`](harvest/SKILL.md) — distill a finished vault project into a reusable wiki article.
- [`digital-twin-builder`](digital-twin-builder/SKILL.md) — analyze vault content into a digital-twin profile with confidence scoring.
- [`kody-twin`](kody-twin/SKILL.md) — the twin persona that represents the author from the learned profile (rename for your own twin).

## Use

Copy or symlink a skill directory into the Agent Skills location supported by
your host:

```bash
git clone https://github.com/kody-w/rapp-skills.git
```

For Claude Code, for example:

```bash
ln -s "$PWD/rapp-skills/deep-research" ~/.claude/skills/deep-research
```

Other compatible hosts can consume the same directory unchanged. If a host
does not support automatic skill discovery, provide `SKILL.md` as an
instruction file.

## Add a skill

1. Create `<skill-name>/SKILL.md`.
2. Use the canonical Agent Skills frontmatter: `name` and `description`.
3. Keep the main file under 500 lines; place details in `references/`.
4. Add the intended `*_agent.py` conversion target to this README.
5. Validate before committing:

```bash
python3 scripts/validate_skills.py
```

The staging-to-RAPP mapping is documented in
[`deep-research/references/rapp-agent-conversion.md`](deep-research/references/rapp-agent-conversion.md).

## License

MIT
