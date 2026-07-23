# RAPPLICATION_SPEC — `rapp-application/1.0`

> **Frozen excerpt** of the canonical rapplication contract. Bundled at planting time on 2026-05-09T15:45:28Z.

A **rapplication** is a graduated agent: an organism with skin (UI) and a manifest. Same rappid format, same egg distribution, same bonding lifecycle as a bare agent — just a quality tier higher (per Constitution Article XXXVII, "Rapplications ARE organisms").

## Where rapplications live

The canonical store is [`kody-w/RAPP_Store`](https://github.com/kody-w/RAPP_Store). A planted neighborhood like THIS one can ALSO host its own rapplications — same shape, just under THIS repo's `apps/` directory. Every neighborhood is potentially its own micro-store.

## Required file layout

```
apps/@<publisher>/<id>/
├── manifest.json                          # rapp-application/1.0 envelope
├── singleton/<id>_agent.py                # the agent (one file)
└── ui/index.html                          # optional UI (skin)
```

## manifest.json (rapp-application/1.0)

```json
{
  "schema":      "rapp-application/1.0",
  "id":          "<lowercase-with-hyphens>",
  "name":        "<Display Name>",
  "version":     "0.1.0",
  "publisher":   "@<github-handle>",
  "kind":        "rapplication",
  "quality_tier": "experimental | community | verified | official",
  "summary":     "<1–2 sentences>",
  "tagline":     "<short hook>",
  "category":    "core | productivity | meta | demo | …",
  "tags":        ["…"],
  "license":     "BSD-style | MIT | CC0-1.0 | …",
  "homepage":    "https://github.com/kody-w/lumen-brainstem/tree/main/apps/@<publisher>/<id>",
  "repo_url":    "https://github.com/kody-w/lumen-brainstem",
  "_note":       "Optional free-form note about install/dependencies/etc."
}
```

## Singleton agent

Same contract as `AGENT_SPEC.md` — one file, one class, one `perform()`. Plus an optional `__manifest__` dict at module level for `.py.card`-style discovery.

## Optional UI

A single `ui/index.html` (no build step) that renders the rapplication's surface. The brainstem at `/chat` can hand off to the UI via slot delimiters or by linking out.

## Catalog entry

The store auto-generates `api/v1/rapplication/<id>.json` (`rapp-pokedex-rapp/1.0` schema) from the manifest. Operators don't author this file directly.

## Hard rules

- **One singleton per rapplication.** Multi-agent compositions are themselves agents that route to others.
- **Operator-mediated for installs.** Every rapplication ships an egg; install via `egg_hatcher` or `brainstem hatch <egg-url>`.
- **License compatibility with the store.** This neighborhood's accepted licenses are listed in `../neighborhood.json` (or default to repo's LICENSE).
- **Holocard required.** Every rapplication has a `card.json` per `HOLOCARD_SPEC.md` (rappcards/1.1.2). Generate via `tools/holo_card_generator.py` if available.

---

*Schema: `rapp-application/1.0`. Canonical store: kody-w/RAPP_Store. Local store (this neighborhood): `apps/`.*
