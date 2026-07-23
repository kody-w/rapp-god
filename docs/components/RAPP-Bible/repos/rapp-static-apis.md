# rapp-static-apis

**Identity & registry** — APIs on GitHub raw, no server (`rapp-static-api/1.0`).

- Canonical: https://github.com/kody-w/rapp-static-apis
- Schema: `rapp-static-api/1.0`
- Default branch: `main`

## What it is

`rapp-static-apis` demonstrates the **first principle made concrete**: an API that is just JSON on `raw.githubusercontent.com`, with no server behind it. PokeAPI-style static catalogs — an entry JSON, a sprite, a downloadable artifact — served by the CDN GitHub already paid for.

This is how the stores and registries work: they are static files, fetched by raw URL, with no backend to run or pay for. "Use everyone else's hardware to run the network" includes "use everyone else's CDN to serve your API."

## What it provides

- The `rapp-static-api/1.0` pattern.
- Reference static catalogs served entirely from GitHub raw.

See [`OVERVIEW.md`](../OVERVIEW.md) §1 (the first principle).
