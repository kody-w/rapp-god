# RAPPcards Roadmap

Tracking work across the federation (RAPPcards spec + all compliant binders).
For the authoritative spec see [`SPEC.md`](./SPEC.md). For the canonical peers
list see [`peers.json`](./peers.json).

---

## Shipped

### v1.1.2 — Mnemonic-as-ownership (2026-04-17)
- SPEC §5.4 step 8 upgraded to MANDATORY auto-persist on resolution
- SPEC Appendix B formalizes the rebuild-from-memory guarantee
- All four binders (rar, rappcards, red-binder, twin-binder) updated to auto-save on summon
- `kody-w/twin-binder` ships as the reference rebuild-from-memory demo (empty binder, 24 demo incantations, federation walker trace log, `⚡ All` button)

### v1.1.1 — Federation clarifications (2026-04-17)
- §5.4.1 foreign-card normalization table
- Role vocabulary (`registry`, `twin`, `third-party`, `archive`)
- Walker self-skip rule made explicit
- `peers.json` optional fields documented

### v1.1 — Federated seed resolution (2026-04-17)
- `seed-index.json` + `peers.json` schemas
- Canonical federation bootstrap URL
- Cross-binder seed resolution via static raw-URL lookups

### v1.0 — Initial spec (2026-04-17)
- Card data model, 1024-word mnemonic, hash protocol, export envelope

---

## In progress

_(nothing actively in flight — next priorities below)_

---

## Next

### `rapp-sdk-js` + `rapp-sdk-py` — the incantation primitive
Expose federation resolution as a reusable library so third-party agents and
apps don't need to re-implement the walker. Minimum surface:

```js
import { resolveIncantation, seedToWords, wordsToSeed } from 'rapp-sdk-js';
const card = await resolveIncantation('FORGE ANVIL BLADE RUNE SHARD SMELT TEMPER');
// → { id, card, peer } or null
```

- Zero runtime dependencies (fetch only, BigInt built-in)
- Ships the authoritative 1024-word mnemonic
- Uses the canonical `peers.json` by default; configurable
- Parallel to `kody-w/RAR/rapp_sdk.py` which already has the hash primitives
- Publish via unpkg / jsdelivr for in-browser use; npm + PyPI for tooling

**Why it matters:** lowers the bar for new binders, agent plugins, and voice
interfaces. Today every binder reimplements ~80 lines of the walker.

### `peers.json` schema linter (GitHub Action)
Automated validation on PRs to `kody-w/RAPPcards/peers.json`:

- Required fields present (`binder`, `seed_index`, `role`)
- `seed_index` URL returns HTTP 200 and valid `rappcards-seed-index/1.0` JSON
- `binder` slug is unique across peers
- `role` value is in the approved vocabulary
- Self-consistency check: fetch the peer's `binder.html`, confirm its
  `<meta name="rappcards-binder">` matches the claimed slug and
  `rappcards-spec` is ≥ 1.1.2

**Why it matters:** federation is permissionless by design (PR to add a peer),
so the trust model depends on structural checks. Catches typos and
non-conforming binders before they break the walker for everyone else.

### Twin-binder import round-trip
Twin-binder currently exports JSON but doesn't import. Add symmetric import so
users can move a collection between binders without re-speaking every
incantation. The import path already exists in RAPPcards and red-binder — port
it down.

**Why it matters:** the rebuild-from-memory contract makes this redundant in
theory (you can always re-speak), but in practice users will want to migrate
decks directly.

### Voice interface reference
A standalone page at `kody-w/RAPPcards/voice.html` that listens for 7-word
incantations via Web Speech API and resolves them to cards. Red-binder and RAR
already have voice paths — factor out into a shared reference implementation
that any binder can embed.

**Why it matters:** speaking the words IS the contract. A polished voice
interface makes the metaphor literal.

---

## Later

- **Multi-registry federation** — today all verified cards flow through RAR.
  The spec doesn't require this. Nothing stops a second registry from existing;
  the walker finds whoever has the seed. Document the pattern for minting
  authorities that want to coexist with RAR without forking.
- **Deck sharing via URL** — pack an entire deck's incantations into a
  shareable URL fragment so you can hand a friend "your binder" as a link, and
  their empty binder reconstructs on open.
- **Offline-first PWA manifest** — service worker caches `peers.json` +
  `seed-index.json` + bundles so the federation walk works offline after first
  visit.
- **Card diff UI** — when a card updates (same seed, changed metadata via
  re-mint), show the diff and let the binder pin a specific version.
- **Federation health dashboard** — static page that pings every peer's
  `seed-index.json` + `peers.json` and visualizes the topology. Useful for
  catching silent breakage.

---

*Incantations in your head. Cards on the chain. Binders as views. The roadmap
is the path to keep that contract legible as the federation grows.*
