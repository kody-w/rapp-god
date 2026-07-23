# rapp-god

**Identity & registry** — the registry of every part *and every version*; the drift observatory; one of the two grail mirrors that host `ecosystem-spec.json`.

- Canonical: https://github.com/kody-w/rapp-god
- Spec mirror: https://raw.githubusercontent.com/kody-w/rapp-god/main/api/v1/ecosystem-spec.json
- Default branch: `main`

## What it is

rapp-god is the **god's-eye registry**: a content-addressed catalog of every part in the ecosystem and every version of it. It is the drift observatory — because it records versions, it can tell you when a part has drifted from its declared schema.

It is also **leg two of the drift triangle**: it hosts `ecosystem-spec.json` (the machine spec) and `ECOSYSTEM_SPEC.md` (the human one), published byte-identical to its sibling mirror [rapp-map](rapp-map.md). The two mirrors must `sha256`-match; any divergence is drift.

## What it provides

- `api/v1/ecosystem-spec.json` — the canonical machine spec this Bible renders (v1.2.0).
- `api/v1/registry.json` — every part + version, content-addressed.
- The drift observatory surface — what version of what lives where.

See [`DRIFT_TRIANGLE.md`](../DRIFT_TRIANGLE.md) for how rapp-god, rapp-map, the one agent, and this Bible stay in sync.
