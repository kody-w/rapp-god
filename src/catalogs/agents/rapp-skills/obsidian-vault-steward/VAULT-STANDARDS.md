# Vault Standards

## Obsidian Syntax

- **Wiki links**: `[[Note Name]]` or `[[Note Name|Display Text]]`
- **Tags**: `#tag` or nested `#parent/child`
- **Embeds**: `![[Note Name]]` to embed content
- **Frontmatter**: YAML block at top of file between `---` markers

## Note Types

| Type | Purpose | Naming |
|------|---------|--------|
| Permanent | Evergreen knowledge | `Topic Name.md` |
| Daily | Daily journal/log | `YYYY-MM-DD.md` |
| Project | Active project docs | `Project - Name.md` |
| Reference | External content summaries | `Source - Title.md` |

## Frontmatter Fields

```yaml
---
created: 2024-12-31
tags: []
type: permanent | daily | project | reference
status: active | complete | archived
---
```

## Organization Principles

1. **Atomic notes** - One idea per note when possible
2. **Descriptive titles** - Titles should be searchable and self-explanatory
3. **Liberal linking** - Connect related concepts with backlinks
4. **Inbox zero** - Process new notes into proper structure regularly

## File Locations

- Root level: Active notes and main topics
- Subdirectories: Group related notes (projects, areas, archives)
- `.obsidian/`: Configuration (do not modify directly)
