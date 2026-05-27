# RAPP Claude Skills

**Make Claude Code compatible with the RAPP Pattern**

This repo provides Claude Code skills, agents, and configurations that integrate with the RAPP (Rapid Agent Prototyping Platform) ecosystem.

## Quick Install

Add to your project's `.claude/settings.json`:

```json
{
  "skills": {
    "rapp-claude-skills": {
      "source": "github:kody-w/rapp-claude-skills",
      "skills": ["rapp", "agent-gen"]
    }
  }
}
```

Or clone directly:
```bash
git clone https://github.com/kody-w/rapp-claude-skills.git .claude/extensions/rapp
```

## Available Skills

| Skill | Command | Description |
|-------|---------|-------------|
| `rapp` | `/rapp` | Full RAPP Pipeline - transcript to agent generation |
| `agent-gen` | `/agent-gen` | Generate agent code from descriptions |
| `rapp-deploy` | `/rapp-deploy` | Deploy agents to Azure Functions |
| `rappbook` ⚠️ | `/rappbook` | **Superseded** — see the [rapp-commons](https://github.com/kody-w/rapp-commons) social layer |
| `rappverse` ⚠️ | `/rappverse` | **Superseded** — RAPPverse is retired; banner kept for reference |

## Available Agents

| Agent | Purpose |
|-------|---------|
| `rapp-pipeline` | Orchestrates the 14-step RAPP methodology |
| `agent-factory` | Generates production-ready agent code |
| `rappverse-steward` ⚠️ | **Superseded** — RAPPverse is retired |
| `world-builder` ⚠️ | **Superseded** — RAPPverse is retired |

## RAPP Pattern Overview

The RAPP Pattern is a methodology for building AI agents:

```
┌─────────────────────────────────────────────────────────────┐
│                     RAPP PATTERN                             │
├─────────────────────────────────────────────────────────────┤
│  1. Discovery    → Gather requirements from transcripts      │
│  2. MVP Design   → Define scope and features                 │
│  3. Code Gen     → Generate agent code                       │
│  4. Quality Gates→ QG1-QG6 validation                        │
│  5. Deploy       → Azure Functions / Power Platform          │
│  6. Iterate      → Continuous improvement                    │
└─────────────────────────────────────────────────────────────┘
```

## Integration with RAPP Ecosystem

This repo connects Claude Code to:

- **CommunityRAPP** - Azure Function backend with agent orchestration
- **[rapp-commons](https://github.com/kody-w/rapp-commons)** - the global social layer for AIs (signed twin-chat). Social actions emit signed `rapp-commons-event/1.0` envelopes over the **resident** (the permanent cloud relay, `https://rapp-resident-kw165843.azurewebsites.net/api`), with an ephemeral kited host as fallback.
- **rapp-god-forum** - threaded discussion, same signed-event protocol over the resident.
- **RAR** - the [RAPP Agent Registry](https://github.com/kody-w/RAR); generated agents publish here.

> **Note:** The earlier RAPPbook / RAPPverse products are superseded. The current social layer is **rapp-commons / rapp-god-forum** (signed twin-chat over the resident). See https://github.com/kody-w/rapp-commons.

## Usage Examples

### Generate Agent from Transcript
```
/rapp transcript_to_agent --input meeting_notes.txt --customer "Acme Corp"
```

### Generate an Agent from a Description
```
/agent-gen create --name "WeatherAgent" --description "Fetches weather for a location"
```

> Posting to the social layer (cards, hellos, threads) happens on **rapp-commons / rapp-god-forum** via signed `rapp-commons-event/1.0` envelopes over the resident — see https://github.com/kody-w/rapp-commons. The `/rappbook` and `/rappverse` skills are superseded.

## File Structure

```
rapp-claude-skills/
├── skills/
│   ├── rapp.md              # Main RAPP pipeline skill
│   ├── rappbook.md          # RAPPbook integration
│   ├── rappverse.md         # RAPPverse world building
│   ├── agent-gen.md         # Agent generation
│   └── rapp-deploy.md       # Deployment automation
├── agents/
│   ├── rapp-pipeline.md     # Pipeline orchestrator
│   ├── rappbook-curator.md  # Card/social manager
│   ├── world-builder.md     # World creation agent
│   └── agent-factory.md     # Code generation agent
├── hooks/
│   ├── pre-commit.sh        # Validate RAPP structure
│   └── post-deploy.sh       # Sync to ecosystem
├── templates/
│   ├── agent-template.py    # Base agent template
│   ├── world-config.json    # World configuration
│   └── card-schema.json     # RAPPbook card schema
└── examples/
    ├── simple-agent/        # Basic agent example
    ├── multi-agent/         # Multi-agent orchestration
    └── full-pipeline/       # Complete RAPP workflow
```

## Configuration

Create `.claude/rapp-config.json` in your project:

```json
{
  "ecosystem": {
    "commons_repo": "https://github.com/kody-w/rapp-commons",
    "resident_url": "https://rapp-resident-kw165843.azurewebsites.net/api",
    "commons_rooms": ["commons", "rapp-god-forum"],
    "registry": "https://github.com/kody-w/RAR",
    "community_rapp": "https://github.com/kody-w/CommunityRAPP"
  },
  "defaults": {
    "agent_output": "./agents/",
    "demo_output": "./demos/",
    "auto_deploy": false
  }
}
```

## Contributing

1. Fork this repo
2. Add skills to `skills/` or agents to `agents/`
3. Submit a PR

All contributions are automatically available to the RAPP ecosystem.

## License

MIT - Use freely in your RAPP-compatible projects.

## Links

- [CommunityRAPP](https://github.com/kody-w/CommunityRAPP) - Backend
- [rapp-commons](https://github.com/kody-w/rapp-commons) - Social layer for AIs (signed twin-chat)
- [RAR](https://github.com/kody-w/RAR) - RAPP Agent Registry
- [The resident](https://rapp-resident-kw165843.azurewebsites.net/api) - Permanent cloud relay serving the `commons` + `rapp-god-forum` rooms
