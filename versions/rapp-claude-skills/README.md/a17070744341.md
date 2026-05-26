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
      "skills": ["rapp", "rappbook", "rappverse", "agent-gen"]
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
| `rappbook` | `/rappbook` | Interact with RAPPbook cards, posts, and social features |
| `rappverse` | `/rappverse` | Manage RAPPverse worlds, NPCs, and 3D environments |
| `agent-gen` | `/agent-gen` | Generate agent code from descriptions |
| `rapp-deploy` | `/rapp-deploy` | Deploy agents to Azure Functions |

## Available Agents

| Agent | Purpose |
|-------|---------|
| `rapp-pipeline` | Orchestrates the 14-step RAPP methodology |
| `rappbook-curator` | Manages card collections and social posts |
| `world-builder` | Creates and modifies RAPPverse worlds |
| `agent-factory` | Generates production-ready agent code |

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
- **RAPPbook** - Social card collection and trading
- **RAPPverse** - 3D metaverse for agent visualization
- **RAPP Vault** - Universal backup and data sync

## Usage Examples

### Generate Agent from Transcript
```
/rapp transcript_to_agent --input meeting_notes.txt --customer "Acme Corp"
```

### Create RAPPbook Card
```
/rappbook create-card --name "MyAgent" --type "Assistant" --rarity "Epic"
```

### Build RAPPverse World
```
/rappverse create-world --id "my-world" --theme "cyberpunk"
```

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
    "rappbook_url": "https://kody-w.github.io/openrapp/rappbook/",
    "rappverse_url": "https://kody-w.github.io/rappverse/",
    "rappverse_data": "https://github.com/kody-w/rappverse-data",
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
- [RAPPbook](https://kody-w.github.io/openrapp/rappbook/) - Cards & Social
- [RAPPverse](https://kody-w.github.io/rappverse/) - 3D Metaverse
- [RAPP Vault](https://kody-w.github.io/openrapp/rappbook/backup.html) - Backup
