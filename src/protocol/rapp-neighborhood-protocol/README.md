# rapp-neighborhood-protocol

**The canonical specification of the RAPP kited neighborhood** — `rapp-neighborhood-protocol/1.0`.

This repo is the **single source of truth** for the protocol and its vocabulary. It owns:

- **vTwin · Kited · Kited Twin · the String · Tethered · Kited Neighborhood · Neighbor ·
  Scan‑to‑Join · Sealed · Doorman · Cloud Neighborhood** — and the **kite mark**.
- The `rapp-twin-chat/1.0` envelope, the §5 transports, the §8 sealed channel, the §9 session
  model, §10 multiplayer, §13 the kited demo, §14 cloud neighborhoods, §15 agent‑in‑a‑link sharing.

👉 **The spec:** [`NEIGHBORHOOD_PROTOCOL.md`](NEIGHBORHOOD_PROTOCOL.md)

## Don't fork the words — reference them

Anything that implements or documents the neighborhood (the [vBrainstem](https://github.com/kody-w/vbrainstem)
reference runtime, the [RAR](https://github.com/kody-w/RAR) registry, agents, posts) should **link
to this spec**, not copy it. Copies drift; this doesn't. Mirrors that must keep a local copy run a
CI check that fails if they diverge from this file.

## Related canonical repos

| Repo | Owns |
|------|------|
| **rapp-neighborhood-protocol** (this) | the spec + vocabulary |
| [rapp-sealed](https://github.com/kody-w/rapp-sealed) | the `rapp-sealed/1.0` AES‑256‑GCM codec + conformance vectors (§8) |
| [kite-mark](https://github.com/kody-w/kite-mark) | the kite mark (the visual identity, §2) |
| [vbrainstem](https://github.com/kody-w/vbrainstem) | the reference implementation (consumes this spec) |

## Versioning

The schema is `rapp-neighborhood-protocol/1.0`. Breaking changes bump the version; the vocabulary
and the kite mark are stable identity and change only by deliberate amendment.

MIT © Kody Wildfeuer.
