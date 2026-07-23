# RAPP Hologram — the engine

The **reference engine** for [**RAPP Moment**](https://github.com/kody-w/rapp-moment): living, 100-frame
holographic organisms you can walk, grow, own, and embed. Pure, dependency-free libraries + a serverless
browser **player** + the **resolve Gateway** that makes a Moment render in-place anywhere (NFT marketplace,
wallet, or an `<iframe>` as animated card art).

> The **standard** is [`rapp-moment`](https://github.com/kody-w/rapp-moment). This repo is one conformant
> **implementation** of it — vendored to run standalone so you can embed it, port it, or build on it,
> **as long as you play ball by the standard and this API.**

**Live:** https://kody-w.github.io/rapp-hologram/ · **Player:** `?m=<token>` · **Dial:** `?dial=<pk>`

## Quickstart

```bash
git clone https://github.com/kody-w/rapp-hologram && cd rapp-hologram
python3 -m http.server 8080        # any static server; the engine is serverless
open http://localhost:8080/        # the feed; ?m=<token> plays a Moment, ?dial=<pk> summons one
npm test                           # run the conformance suite (pure Node, no deps)
```

There is **no build step** and **no backend**. The libraries are plain `<script>` includes; the player
runs from any static host. The Moment record *is* the link.

## Card art = a live hologram in an iframe

A Moment is portable, self-contained card art. Embed the looping 100-frame hologram anywhere:

```html
<iframe src="https://kody-w.github.io/rapp-hologram/?m=<TOKEN>"
        width="320" height="320" loading="lazy" style="border:0;border-radius:12px"></iframe>
```

The token is `base64url(JSON.stringify(moment))` — the data streams in via the URL (or from a CDN raw file),
and the iframe plays frames 1→100 on a loop. This is the Gateway `animation_url` from the standard (§11¾):
`Resolve.document(m).animation_url` is exactly this URL, so marketplaces embed the *actual walkable Moment*.

## Libraries (the API)

Eight pure modules, usable in the browser (globals) or Node (`require`). Full reference: **[`API.md`](API.md)**.

| Module | Global | Purpose |
|---|---|---|
| `organism.js` | `Organism` | mint/regenerate an organism from a spacetime coordinate (`organismFromStamp`, `fromPk`, `verifyCoordinate`) |
| `homeostasis.js` | `Homeostasis` | the survival law — `reconcile`, `homeostasis()` → `{alive, vitality, generation, stress}` |
| `fingerprint.js` | `Fingerprint` | the ~40-D similarity descriptor — `fingerprint`, `rank`, `similar` |
| `rappid.js` | `Rappid` | RAPP Eternity ids — `ofMoment(pk)`, `ofKeeper(pubx)`, `sha256` |
| `ownership.js` | `Ownership` | transferable deeds — `deedChain`, `newTransfer`, `transferHash` |
| `fidelity.js` | `Fidelity` | growth over time — `refineOverTime`, `weaveFrame`, `weaveCheck` |
| `resolve.js` | `Resolve` | the Gateway — `document(m)` → ERC-721/OpenSea-compatible JSON + `metaTags` |
| `moment.js` | (player) | the browser player/UI glue for `index.html` |
| `fractal.html` | (surface) | nested Moments (SPEC §11⅞) — renders a Moment's `embed` (a child token, or `"self"`) as an in-world portal that recurses; `?demo={chain,mirror}` |

## Conformance

`npm test` runs the pure conformance suite (`tests/test_*.js`) — generator determinism, the **birth-proof**,
homeostasis, the fingerprint, ownership deeds, and the resolve document. If your own implementation
reproduces these vectors, you interoperate. See the standard's
[`CONFORMANCE.md`](https://github.com/kody-w/rapp-moment/blob/main/CONFORMANCE.md).

## License & trademarks

Source-available under **PolyForm Noncommercial 1.0.0** ([`LICENSE`](LICENSE) / [`NOTICE`](NOTICE)) —
noncommercial view/run/fork/build. **"RAPP", "Holographic Moments"** are trademarks of Kody Wildfeuer; the
license grants no trademark rights. Conform to the standard, ship your own engine, interoperate.

*Engine, not experience. Drop-in, serverless, alive.*
