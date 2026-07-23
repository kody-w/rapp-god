# Brain card schema (v1)

One card per node (repo, protocol, surface, or standing service). Cards are
JSON in `brain/cards/`, indexed by `brain/INDEX.md` (human) and
`brain/graph.json` (machine). Extends the rapp-map neuron card.

```json
{
  "id": "repo:kody-w/rapp-canary",
  "kind": "repo | protocol | surface | service | doc-corpus",
  "name": "rapp-canary",
  "visibility": "public",
  "role": "train entry ring + hub tooling",
  "estate_class": "kernel | ring | distro | spec | tool | app | brand | brain",
  "entry_points": ["…one-liners, URLs, key files…"],
  "protocols": ["rapp-holo/1.0"],
  "edges": [{"to": "repo:kody-w/rapp-installer", "rel": "feeds | distro-of | spec-for | mirrors | depends-on | sibling"}],
  "health": {"last_commit": "ISO", "ci": "green|red|none", "pages": "url|none"},
  "summary": "3-6 sentences a stranger can orient from",
  "provenance": {"crawled_at": "ISO", "sources": ["…public URLs only, in this hemisphere…"]}
}
```

Rules: `summary` must be self-sufficient (no internal codenames unexplained);
`sources` in the public hemisphere are public URLs ONLY; secrets and tokens
are NEVER ingested anywhere — record a pointer ("credential lives in X"),
never a payload.
