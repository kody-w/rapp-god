---
name: transcript-miner
description: Mine Claude Code session history for usage patterns, mistakes, and automation candidates. Use when Kody says "audit my sessions", "what am I doing wrong in Claude Code", "usage audit", "mine my transcripts", "analyze my Claude Code history", "what should be a skill", or asks how he's using Claude Code across past sessions. Extracts tool stats, error signatures, Read:Edit ratios, my-message categories (corrections/rejections), and permission denials from ~/.claude/projects JSONL — with evidence, never vibes.
---

# transcript-miner

Turns the raw `~/.claude/projects/<project>/<session>.jsonl` archive into a
usage audit. One JSON message per line (type, content blocks, tool_use,
timestamps). Sessions are large — this NEVER reads whole transcripts into
context; it runs a streaming extractor and returns aggregates.

## Run it

```
python3 ~/.claude/skills/transcript-miner/scripts/mine.py --window 40 --json /tmp/audit.json
```

Flags: `--window N` (last N substantial sessions), `--min-bytes N` (size floor,
default 200KB), `--project SUBSTR` (filter to one project), `--json OUT` (full
per-session rows).

## Turn signals into findings

The script gives you the numbers; you write the audit. Rules:
- **Every claim cites a session file + excerpt.** No uncited findings.
- **Rank by frequency × cost**, label single-anecdote vs recurring.
- **Findings schema:** `{finding, evidence, frequency, impact, confidence, fix}`.
- **Fixes are behavioral rules, not principles** — "never `cd`, pass absolute
  paths" not "be tidy". Each recurring failure → one rule / skill / hook.
- Read:Edit ratio: >6 = research-first (good), <2 = edit-first — but bulk
  file-generation sessions (estate sweeps) skew it low legitimately; note that.
- Always include a "could not verify / out of scope" section.

## Output

An evidence-backed report + draft SKILL.md for the top skill candidates + hook
configs for the top automations. See the P2 audit for the reference shape.
