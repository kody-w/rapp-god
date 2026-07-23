# `rapp-hologram` API

Every module is a UMD-ish IIFE: in the browser it attaches a global; in Node it is `module.exports`.
All are **pure and deterministic** (no network, no deps). Signatures below are verified against source.

```js
// Node
const Organism = require("./organism.js");
const Homeostasis = require("./homeostasis.js");
// Browser
// <script src="organism.js"></script> → window.Organism
```

---

## `Organism` — spacetime → organism (`organism.js`)

- **`organismFromStamp(ms, loc?)`** → record. Mints the one organism a coordinate produces. `ms` = UTC
  milliseconds; optional `loc = {lat, lng}` binds it to a place (geohash domain). Deterministic.
- **`fromPk(pk)`** → record. Regenerate the genesis genome from an address (`sky·<ms>` or `<geohash9>·<ms>`).
  Zero-lookup "dialing" — the address *is* the organism.
- **`pkFor(ms, loc?)`** → `"sky·<ms>"` or `"<geohash9>·<ms>"`.
- **`verifyCoordinate(record)`** → `bool`. The **birth-proof**: regenerate genesis frames from `pk` and assert
  the record's `u`-less frames are byte-identical. MUST hold at every revision.
- **`geohash(lat, lng, prec)`**, **`geohashDecode(hash)`**, **`nameFromPk(pk)`**, **`BIOMES`** (the 5 biomes).

## `Homeostasis` — the survival law (`homeostasis.js`)

- **`homeostasis(organism)`** → `{ alive, stable, generation, frames, stress, vitality }`. **`vitality = max(0, 1 - stress/STRESS_LIMIT)`**; `alive` once `stress < STRESS_LIMIT`.
- **`reconcile(organism, frame)`** → `{ accepted, survives, kind, organism }`. `kind ∈ {refined, redundant,
  resisted}` — absorb consistent frames, ignore duplicates, resist contradictions (stress rises).
- **`valueAt(organism, at)`**, **`contradicts(a, b)`**, **`STRESS_LIMIT` = 12**.

## `Fingerprint` — similarity (`fingerprint.js`)

- **`fingerprint(moment)`** → `number[]` (~40-D): per-field mean/std/range, an 8-bin hue histogram + circular
  mean, and motion/jerk/glow/spike **energy**. Absolute scales → comparable across the whole warehouse.
- **`rank(target, items)`** → items sorted by distance, each annotated `{ score: 1/(1+dist), dist }`.
- **`similar(a, b)`** → score in `(0,1]`. **`expand(moment, N)`** → N interpolated frames.

## `Rappid` — RAPP Eternity ids (`rappid.js`)

- **`ofMoment(pk)`** → `rappid:moment:<64hex>` (`sha256("moment:"+pk)`).
- **`ofKeeper(pubx)`** → `rappid:keeper:<64hex>`. **`parse(id)`**, **`canonicalize(legacy)`**,
  **`sha256(str)`** → hex, **`SIG_SUITE` = "ecdsa-p256"**.

## `Ownership` — transferable deeds (`ownership.js`)

- **`newTransfer(rappid, from, to, prevHash, ts)`** → unsigned transfer `{…, hash}`; caller signs
  `transferBody(t)` and attaches `sig`+`pub` (`pub.x` MUST equal `from`).
- **`deedChain(rappid, mintOwner, transfers)`** → `{ owner, ownerRappid, transfers, history, tip }`. Walks the
  owner-authorized, hash-linked chain from the minter. `transfers` must be signature-verified by the caller.
- **`transferBody(t)`**, **`transferHash(t)`**.

## `Fidelity` — growth over time (`fidelity.js`)

- **`refineOverTime(organism, frame)`**, **`nextRefineAt(organism)`**, **`finestResolution(organism)`**,
  **`weaveCheck(a, mid, b, tol?)`**, **`weaveFrame(organism, frame)`** — fold a grown frame into the coarsest
  interval only if it stays consistent with its two neighbours (the dream-catcher weave).

## `Resolve` — the Gateway (`resolve.js`)

- **`document(m, opts?)`** → one ERC-721/OpenSea-compatible JSON document:
  `name, description, image, animation_url, external_url, attributes` **+** RAPP Eternity extensions
  (`rappid, pk, born, owner, sig_suite, chain, dimension, spec, sources`). `animation_url` is the live
  `?dial=<pk>` hologram — embed it and the **actual walkable Moment renders in-place**.
  `opts`: `{ base, image, gen, dimension, owner, sources }`.
- **`metaTags(doc)`** → OpenGraph/Twitter-player `<meta>` string. **`BASE`** → the player base URL.

---

## Player URL surfaces (`index.html` + `moment.js`)

| URL | Shows |
|---|---|
| `./` | the feed |
| `?m=<token>` | play a Moment from a self-contained token |
| `?dial=<pk>` | summon a Moment by spacetime address (no data fetch) |
| `?zoo` | your local menagerie (keyed by your browser key) |
| `?keeper=<fp>` | a zookeeper's public menagerie |
| `?dial=<pk>&{bio,grew,at,lineage}` | git-as-harness views (when lineage artifacts are present) |
| `fractal.html?m=<token>` | nested Moments — render a Moment whose record carries an `embed` (a child token, or `"self"`), with the child played in an in-world portal that recurses ([rapp-moment SPEC §11⅞](https://github.com/kody-w/rapp-moment/blob/main/SPEC.md)). Depth-capped. |
| `fractal.html?demo={chain,mirror}` | baked demos — `chain` = 4 distinct nested worlds, `mirror` = a Moment that embeds itself (hall of mirrors) |

`fractal.html` reads each record's `embed` and mounts `index.html?m=<embed>` as a portal, then recurses — the whole nesting travels inside the one token. It honors §11⅞'s rules: unknown-field-inert (a plain player just plays the host organism) and a finite recursion cap.

The token format is the standard's canonical share token: `base64url(JSON.stringify(record))`, padding
stripped. See [`rapp-moment` examples](https://github.com/kody-w/rapp-moment/blob/main/examples/TOKENS.md).
