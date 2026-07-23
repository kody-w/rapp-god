# RAPP Moment — the standard

**A serverless, cryptographic, *alive* social-media primitive.** A **Moment** is at once a **post**, an
exact **moment in time**, and a **living holographic organism** — 100 frames, one heartbeat each. All
state is static data on a CDN; identity is a keypair; ownership is a signature; there is no backend.

This repository is the **canonical standard** (`rapp-moment`). It is intentionally implementation-free
so anyone — inside or outside our ecosystem — can build a conformant client and interoperate, **as long
as they play ball by this standard and its API.**

- 📜 **[`SPEC.md`](SPEC.md)** — the full, normative specification (wire format, spacetime addressing,
  determinism + birth-proof, organism physics, ownership, the git-as-harness, the chain, the Gateway).
- ✅ **[`CONFORMANCE.md`](CONFORMANCE.md)** — the MUSTs distilled into a checklist + how to test.
- 🧩 **[`examples/`](examples/)** — canonical Moment records and their share tokens.
- 🖥 **Reference engine:** [`kody-w/rapp-hologram`](https://github.com/kody-w/rapp-hologram) — a runnable
  player + the pure libraries + the conformance test suite. The standard is here; the engine is there.

## 30-second model

A Moment is a small JSON record:

```json
{ "v":1, "t":"Title", "a":"@author", "b":"savanna",
  "k":[ {"at":0,"s":0.3,"l":0.3,"p":0.1,"g":0.2,"h":40,"x":0,"z":0},
        {"at":99,"s":0.4,"l":0.35,"p":0.1,"g":0.3,"h":60,"x":0,"z":0.1} ] }
```

- **`k`** is the genome: a few keyframes of a form `{s ize, l egs, p spikes, g low, h ue, x,z drift}`,
  interpolated to **100 frames** and played as a walkable hologram on a loop.
- The record **is the link.** `encode(m) = base64url(JSON)` → play anywhere as **`?m=<token>`**.
- A Moment minted from a spacetime coordinate carries a **`pk`** (`sky·<utc_ms>` or `<geohash9>·<utc_ms>`);
  it can be summoned by address alone — **`?dial=<pk>`** — with zero bytes of lookup.

## The Gateway (how it leaves the ecosystem)

Resolving a Moment produces **one ERC-721/OpenSea-compatible document** whose `animation_url` is the live
`?dial=<pk>` hologram. So the **actual walkable Moment embeds in-place** — in a marketplace, a wallet, or
**as card art in an `<iframe>`** that streams the record from a CDN and loops its 100 frames. Interop is
the point: a Moment is a static document on raw CDN, the live hologram one dial away. See SPEC §11¾.

## Nested Moments — worlds within worlds

A Moment can carry an optional **`embed`** trait — a child Moment's token — so its hologram *contains* another
Moment, played in-world. The child can embed another, and `embed:"self"` makes a Moment that contains itself
(an infinite hall of mirrors, depth-capped). The whole nesting rides **inside the one token** — the record is
the link, all the way down. It's an open-schema trait: older players ignore it and play the lone organism, so
nothing breaks. See SPEC **§11⅞** and [`examples/nested-fractal.json`](examples/nested-fractal.json).

## Conformance in four lines

You are `rapp-moment` conformant if you:
1. Preserve the **birth-proof** — never alter a genesis frame; `verifyCoordinate` holds for all time.
2. Treat the genome generator as **frozen**, and read **all** historical record shapes; emit only canonical.
3. Keep `_`-prefixed metadata **out of the signed body**; ownership is an ECDSA P-256 signature.
4. Stay **serverless + append-only** — static data, client-side queries, no new server.

Full list: [`CONFORMANCE.md`](CONFORMANCE.md).

## License & trademarks

Source-available under **PolyForm Noncommercial 1.0.0** (see [`LICENSE`](LICENSE) / [`NOTICE`](NOTICE)).
You may view, run, fork, and build on it for **noncommercial** purposes. **"RAPP", "Holographic Moments",
"Holographic Moment"** are trademarks of Kody Wildfeuer — the license grants no trademark rights; don't use
the marks to brand forks or competing products. Conform to the standard, ship your own client, interoperate.

*Engine, not experience. Drop-in, serverless, alive.*
