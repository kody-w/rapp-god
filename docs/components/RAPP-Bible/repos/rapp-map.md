# rapp-map

**Identity & registry** — the ecosystem index (which repo houses which part) + the neuron mesh; the second grail mirror of `ecosystem-spec.json`.

- Canonical: https://github.com/kody-w/rapp-map
- Spec mirror: https://raw.githubusercontent.com/kody-w/rapp-map/main/ecosystem-spec.json
- Default branch: `main`

## What it is

rapp-map answers "**which repo houses which part?**" — it is the ecosystem index. It also hosts the **neuron mesh** (`neurons.json`): a set of file-specialist nodes, one per canonical file, that can be fanned out in parallel to answer any "is X consistent everywhere?" drift question.

It is **leg three of the drift triangle**: it carries a byte-identical copy of `ecosystem-spec.json` + `ECOSYSTEM_SPEC.md`. rapp-map and [rapp-god](rapp-god.md) must `sha256`-match; the moment they don't, something drifted.

## What it provides

- `ecosystem-spec.json` — the byte-identical spec mirror (v1.2.0).
- `neurons.json` — the neuron mesh (`rapp-neuron-mesh/1.0`), indexed by schema version.
- The part-to-repo index.

See [`DRIFT_TRIANGLE.md`](../DRIFT_TRIANGLE.md) and [`SCHEMAS.md`](../SCHEMAS.md).
