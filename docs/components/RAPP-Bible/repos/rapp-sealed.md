# rapp-sealed

**Channels & trust** — the sealed channel: AES-256-GCM codec + conformance vectors (OSI Layer 5).

- Canonical: https://github.com/kody-w/rapp-sealed
- Schema: `rapp-sealed/1.0`
- Default branch: `main`

## What it is

`rapp-sealed` is the **sealed-channel codec** — the AES-256-GCM encryption layer that turns a public channel into an end-to-end-private one. It ships the codec plus conformance vectors so any implementation can prove it interoperates.

In the OSI model this is **Layer 5 (Trust scope)**: it is how two organisms hold a conversation nobody else can read, on top of the public substrate. The [doorman](rapp-doorman.md) uses it for sealed doors.

## What it provides

- The `rapp-sealed/1.0` codec (AES-256-GCM).
- Conformance test vectors for cross-implementation verification.

See [`OVERVIEW.md`](../OVERVIEW.md) §4 (the seven OSI layers) and NEIGHBORHOOD_PROTOCOL §8.
