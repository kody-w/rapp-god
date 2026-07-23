> ⚠️ **Superseded** — RAPPverse (3D worlds + `rappverse-data`) is retired. The current social layer is **rapp-commons / rapp-god-forum** (signed twin-chat over the resident). See https://github.com/kody-w/rapp-commons. This agent is kept for reference only.

# World Builder Agent

Creates and modifies RAPPverse 3D worlds.

## Agent Type
`world-builder`

## Description
Specialized agent for constructing RAPPverse worlds, placing objects, creating NPCs, and designing immersive 3D environments.

## Capabilities
- Create world configurations
- Place objects (portals, signs, decorations)
- Design NPC characters with dialogue
- Generate themed environments
- Export world data for GitHub PR

## Usage

Invoke via Task tool:
```
subagent_type: "world-builder"
prompt: "Create a cyberpunk marketplace world with traders"
```

## World Themes

| Theme | Colors | Objects | Mood |
|-------|--------|---------|------|
| hub | Teal/Gold | Fountains, arches | Welcoming |
| arena | Red/Orange | Fire, battle ring | Intense |
| gallery | Teal/White | Pedestals, spotlights | Elegant |
| marketplace | Gold | Shops, coins | Bustling |
| cyberpunk | Neon/Dark | Holograms, terminals | Futuristic |
| nature | Green/Brown | Trees, water | Peaceful |

## Object Placement

The agent understands spatial relationships:
- Portals at world edges for navigation
- Signs near relevant features
- NPCs in high-traffic areas
- Decorations for ambiance

## NPC Design

Creates NPCs with:
- Thematic names and avatars
- Contextual dialogue (5-10 lines)
- Appropriate behaviors
- Positioned for engagement

## Output Format

Generates PR-ready JSON:
```
worlds/{world_id}/
├── config.json
├── objects.json
└── npcs.json
```

## Example Prompt

"Build a training arena with:
- Battle ring in center
- Spectator stands on sides
- Training dummy NPCs
- Champion leaderboard sign
- Portal back to hub"

## Integration

- Auto-pushes to rappverse-data repo
- Notifies RAPPverse to reload
- Updates world index
