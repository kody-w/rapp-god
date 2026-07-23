# CommunityRAPP

**Memory & social** — the RAPP Hippocampus (persistent memory, local-first → Azure).

- Canonical: https://github.com/kody-w/CommunityRAPP
- Default branch: `main`

## What it is

CommunityRAPP is the **hippocampus** — the persistent memory layer for the ecosystem. It is local-first (memory lives in `.brainstem_data/` as JSON) with a transparent migration path to Azure for shared / cloud memory. It backs the three-tier memory model: device-local, public (`memory.json`), and per-user private (GitHub Issues).

## What it provides

- The persistent memory store, local-first.
- The transparent local → Azure migration path.

The god agent does the *local* memory tier natively; deep memory (public commits + per-user private Issue memories + ascended export) is install-routed via `manage_memory_agent.py` / `context_memory_agent.py`. See [`CAPABILITIES.md`](../CAPABILITIES.md), Memory & Recall.
