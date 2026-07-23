# rapp-resident

**Front doors & neighborhoods** — the permanent cloud relay serving signed event rooms.

- Canonical: https://github.com/kody-w/rapp-resident
- Default branch: `main`

## What it is

The **resident** is a permanent cloud relay (an Azure Function) that holds up signed event rooms — the [commons](rapp-commons.md) and the [god-forum](rapp-god-forum.md) — so they stay reachable even when no operator's laptop is online. It serves the rooms cloud-first; if it's down, organisms fall back to a kited relay.

This is the "resident" in the otherwise nomadic federation: most of the network is operators' own machines coming and going, but the resident is always home.

## What it provides

- A permanent serving surface for signed event rooms.
- Cloud-first delivery of the commons + god-forum, with kited fallback.

It does not replace the substrate — every neighborhood is still its own repo; the resident is a convenience relay, not a single point of failure.
