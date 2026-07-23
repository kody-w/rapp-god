# RAPPcards Specification v1.1.2

**Status:** Stable · **Last updated:** 2026-04-17 · **Authors:** Wildhaven / RAPP community

This document is the portable, implementation-independent standard for **RAPPcards** — the universal
trading-card representation of single-file `*_agent.py` agents. Any binder, registry, wallet, game,
or viewer that conforms to this spec can trade, summon, display, and mint cards compatibly.

The two reference implementations are:

- **[kody-w/RAR](https://kody-w.github.io/RAR/)** — the canonical registry + minting authority.
- **[kody-w/RAPPcards](https://kody-w.github.io/RAPPcards/)** — the local-first twin binder.

RAPPcards predates and outlives any single binder. A card is portable data. A binder is a view of it.

---

## §1. Design principles

1. **The `agent.py` is sacred.** A RAPPcard is a *view* of a single-file Python agent. The card
   format MUST NOT require changes to the agent itself. The agent stands alone; the card is derived.
2. **Deterministic identity.** Every card has exactly one canonical 64-bit **seed** computed from
   the agent. Given the same agent source, every conforming implementation MUST derive the same seed.
3. **Registry is optional.** A card can be summoned from a seed alone. Registration with RAR is how
   you claim a name and publish to the global pool, but an agent + seed is a card even without it.
4. **Local-first.** A binder MUST be usable offline after first sync. No server requirement, no account.
5. **Lossless portability.** Any card, in any binder, MUST be exportable as a JSON document that
   another conforming binder can import with zero loss.
6. **One seed, many binders.** The same 64-bit seed resolves to the same card in RAR, RAPPcards,
   and any future binder. Cards are tradeable by speaking the incantation.

---

## §2. Card data model

A **Card** is a JSON object. Required fields are marked ✱.

```json
{
  "id": "@publisher/slug",            // ✱ composite identity
  "name": "Forge Master",             // ✱ display name
  "title": "Seven-hammered singularity",
  "seed": "4997715477691771520",      // ✱ 64-bit unsigned int as STRING (BigInt-safe)

  "hp": 180,                          // ✱ 10–300
  "stats": {                          // ✱ all four required, 0–255
    "atk": 140, "def":  95,
    "spd":  80, "int": 110
  },

  "agent_types": ["CRAFT", "LOGIC"],  // ✱ 1–3 entries from §2.1
  "weakness":   "SHIELD",             //   single type
  "resistance": "WEALTH",             //   single type

  "rarity_tier":  "mythic",           // ✱ starter | core | rare | mythic
  "rarity_label": "Legendary",        //   human label (see §2.3)

  "abilities": [                      // ✱ 1–4 entries
    {
      "name":   "Anvil Strike",
      "cost":    2,                   // 0–5 energy
      "damage":  60,                  // 0–300, optional
      "text":   "Deal 60 damage. If opponent is CRAFT, deal 30 more.",
      "type":   "CRAFT"               // optional, for typed damage
    }
  ],

  "typed_abilities": [...],           // optional; same shape as abilities, with .type required
  "retreat_cost": 2,                  // 0–5

  "evolution": {                      // optional
    "stage": 2,                       // 1=basic, 2=stage-1, 3=stage-2
    "label": "Stage 1",
    "icon":  "⚒"
  },

  "flavor_text": "Seven words hammered into one",
  "avatar_svg":  "<svg>…</svg>",      // optional, ≤64KB

  "meta": {                           // optional registry-style block (see §3)
    "version":      "1.0.0",
    "category":     "productivity",
    "author":       "kody-w",
    "quality_tier": "verified",
    "license":      "MIT"
  }
}
```

### §2.1 Type system

Exactly seven agent types, arranged in a directed attack cycle:

```
LOGIC → WEALTH → HEAL → CRAFT → SHIELD → SOCIAL → DATA → LOGIC
```

Attack relationship: **X → Y** means *X is strong against Y* (damage ×2 to Y).

Resistance relationship: the reverse step, **Y resists X** by one step.

Reference colors (hex) MAY be used for UI:

| Type   | Color   | Label              |
|--------|---------|--------------------|
| LOGIC  | #58a6ff | Logic (reason)     |
| DATA   | #3fb950 | Data (memory)      |
| SOCIAL | #bc8cff | Social (empathy)   |
| SHIELD | #d29922 | Shield (defense)   |
| CRAFT  | #ff7b72 | Craft (making)     |
| HEAL   | #7ee787 | Heal (support)     |
| WEALTH | #ffd480 | Wealth (economy)   |

### §2.2 Rarity tiers

| `rarity_tier` | `rarity_label` | `meta.quality_tier` source |
|---------------|----------------|----------------------------|
| `starter`     | Starter        | `experimental`             |
| `core`        | Core           | `community`                |
| `rare`        | Elite          | `verified`                 |
| `mythic`      | Legendary      | `official`                 |

### §2.3 Stat derivation

A conforming binder MAY display raw stats directly. Derived combat values (if used) follow:

- `total_power  = hp + atk + def + spd + int`
- `threat_score = atk * 1.0 + int * 0.8 + spd * 0.5`
- Damage formula is left to the game layer — the card carries the numbers, not the rules.

---

## §3. Seed protocol

### §3.1 Derivation

The canonical seed is computed from the agent source file using BLAKE2b-64:

```python
import hashlib
def canonical_seed(agent_source_bytes: bytes) -> int:
    h = hashlib.blake2b(agent_source_bytes, digest_size=8)
    return int.from_bytes(h.digest(), 'big')   # unsigned 64-bit
```

The seed is **derived**, not chosen. An agent cannot have two seeds, and two different agents have
vanishingly small collision probability (2⁻³²).

### §3.2 Mnemonic incantation

A **7-word incantation** is a lossless human-readable form of any 64-bit seed.

- **Wordlist:** exactly 1024 uppercase ASCII words, indexed 0–1023.
- **Authoritative source:** `MNEMONIC_WORDS` in
  [`kody-w/RAR/rapp_sdk.py`](https://github.com/kody-w/RAR/blob/main/rapp_sdk.py).
- The list begins: `FORGE ANVIL BLADE RUNE SHARD SMELT TEMPER …` and ends `… CRESCENT PINNACLE VERTEX`.
- **Encoding:** 10 bits per word × 7 words = 70 bits, which covers all 64-bit seeds with 6 bits of
  reserved zero-padding.

**Encode (seed → words):**

```python
def seed_to_words(seed: int) -> str:
    s = seed & ((1 << 64) - 1)
    idxs = []
    for _ in range(7):
        idxs.append(s & 0x3FF)   # low 10 bits
        s >>= 10
    return " ".join(MNEMONIC_WORDS[i] for i in reversed(idxs))
```

**Decode (words → seed):** reverse of above. Unknown words MUST fail loudly.

**Case insensitive** on input, UPPERCASE on output.

### §3.3 Why this wordlist

Any change to the order or contents of `MNEMONIC_WORDS` breaks every previously-minted incantation.
The wordlist is therefore considered **frozen in stone**. New implementations MUST ship the exact
same 1024 words in the exact same order. A conforming binder SHOULD verify its wordlist matches by
hashing and comparing:

```
blake2b-16("\n".join(MNEMONIC_WORDS)) == "TBD-after-freeze"   // informational
```

---

## §4. Composite ID (`@publisher/slug`)

A card's `id` is `@<publisher>/<slug>` where:

- `publisher` is the owner namespace — a GitHub handle, DID, or organization slug.
  - Format: `[a-z0-9][a-z0-9-]{0,38}`
  - The `@` prefix is literal and required.
- `slug` is the agent filename without the `_agent.py` suffix, kebab-cased.
  - Format: `[a-z0-9][a-z0-9-]{0,62}`

Example: `@kody-w/forge-master` ← `kody-w/forge_master_agent.py`.

The ID is a friendly label for humans. The **seed is the true identity**. Two IDs pointing at the
same agent source have the same seed; changing an agent's source produces a new seed (a new card).

---

## §5. Binder interoperability protocol

Every conforming binder MUST implement all of §5.1. §5.2 and §5.3 are strongly recommended.

### §5.1 URL hash protocol (required)

A binder MUST handle these URL hashes on page load and `hashchange`:

| Hash                             | Behavior                                                       |
|----------------------------------|----------------------------------------------------------------|
| `#add=<id>`                      | Resolve `<id>` from the registry and add to collection         |
| `#seed=<decimal-or-0xhex>`       | Resolve by seed, open detail, add if registered                |
| `#incant=<w1>+<w2>+…+<w7>`       | Decode words → seed → same as `#seed=`                         |
| `#collection` / `#browse` / `#summon` / `#manage` | Deep-link to a tab                            |

After consuming a summon hash, the binder MUST clear it (`history.replaceState`) so reloads don't
re-add the card. Share-link UI MUST encode with `+` as word separator and standard URL-encoding
otherwise.

### §5.2 Export / Import envelope (recommended)

```json
{
  "schema":    "rappcards-binder/1.0",
  "exported":  "2026-04-17T12:00:00Z",
  "generator": "rappcards-binder@1.0 (https://kody-w.github.io/RAPPcards/)",
  "count":     42,
  "cards": [
    {
      "_binder_key": "@kody-w/forge-master",
      "_added_at":   "2026-04-15T09:12:33Z",
      "id":          "@kody-w/forge-master",
      "seed_str":    "4997715477691771520",
      "meta":        { ... §3 meta ... }
    }
  ]
}
```

- `_binder_key` uniquely identifies a card in the binder (MAY equal `id`).
- `seed_str` is the seed as a decimal string (never a JS number; BigInt-safe).
- An importer MUST accept both this envelope AND a bare `[{…}, {…}]` array.
- Full card data MAY be omitted from the export — the binder re-fetches from the live registry on
  import. The minimum viable entry is `{_binder_key, id, seed_str}`.

### §5.3 BigInt-safe JSON handling (recommended)

JS `JSON.parse` loses precision on integers > 2⁵³. Conforming JS binders SHOULD either:

1. Store `seed` as a JSON string (recommended — forward-compatible with all parsers), or
2. Preprocess raw JSON text to quote large integers before parsing:
   ```js
   txt = txt.replace(/("seed"\s*:\s*)(-?\d{10,})/g, '$1"$2"');
   ```
   and re-wrap with `BigInt(value)` after parse.

Python binders have no such limitation.

### §5.4 Federated seed resolution (v1.1, required)

**The whole point of RAPPcards: speak the incantation in any binder, and the card appears.**

A binder MUST be able to resolve a seed it doesn't own by walking the federation. A binder MUST
publish a `seed-index.json` at a stable raw URL (typically
`https://raw.githubusercontent.com/<owner>/<repo>/main/seed-index.json`) with the following shape:

```json
{
  "schema":    "rappcards-seed-index/1.0",
  "binder":    "my-binder",
  "homepage":  "https://example.github.io/my-binder/",
  "cards_url": "https://raw.githubusercontent.com/ex/my-binder/main/cards.json",
  "count":     42,
  "seeds": {
    "4997715477691771520": {
      "id":           "@ex/forge-master",
      "name":         "Forge Master",
      "rarity_tier":  "mythic",
      "url":          "https://raw.githubusercontent.com/ex/my-binder/main/cards/forge-master.json",
      "binder":       "my-binder"
    }
  },
  "ids": {                                  // optional — same entries keyed by id
    "@ex/forge-master": { ... }
  }
}
```

Each entry maps a seed (decimal string) to a pointer to the **full card JSON** at a
raw-content URL. The pointer fields:

| Field           | Required | Purpose                                                          |
|-----------------|----------|------------------------------------------------------------------|
| `id`            | ✱        | Canonical `@publisher/slug`                                     |
| `url`           | ✱        | Raw URL to the card JSON (or to a bundle; see `url_is_bundle`)  |
| `name`          |          | Display name for lightweight listings                           |
| `rarity_tier`   |          | For sorting/badges without fetching                             |
| `binder`        |          | Owning binder name                                              |
| `url_is_bundle` |          | If `true`, `url` points at a multi-card registry; see below     |
| `bundle_key`    |          | Key to look up inside the bundle (typically same as `id`)       |

**Bundle handling.** If `url_is_bundle` is `true`, the binder fetches the URL, parses the result,
expects a top-level `cards` object (or bare map), and looks up `bundle_key` to extract the card.
Otherwise the URL returns the single card JSON directly.

#### Peer discovery: `peers.json`

Each binder MAY publish a `peers.json` at a stable raw URL declaring the federation it recognizes:

```json
{
  "schema":  "rappcards-peers/1.0",
  "updated": "2026-04-17",
  "peers": [
    {
      "binder":     "rar",
      "homepage":   "https://kody-w.github.io/RAR/",
      "seed_index": "https://raw.githubusercontent.com/kody-w/RAPPcards/main/seed-index.json",
      "role":       "registry"
    },
    {
      "binder":     "red-binder",
      "homepage":   "https://kody-w.github.io/red-binder/",
      "seed_index": "https://raw.githubusercontent.com/kody-w/red-binder/main/seed-index.json",
      "role":       "third-party"
    }
  ]
}
```

The **canonical peers list** lives at
[`https://raw.githubusercontent.com/kody-w/RAPPcards/main/peers.json`](https://raw.githubusercontent.com/kody-w/RAPPcards/main/peers.json).
New binders join the federation by PR'ing themselves in.

##### Optional peers.json fields (v1.1.1)

| Field                     | Level   | Purpose                                                            |
|---------------------------|---------|--------------------------------------------------------------------|
| `canonical`               | top     | `true` if this file **is** the canonical list                      |
| `canonical_source`        | top     | URL of the canonical `peers.json` this file mirrors                |
| `updated`                 | top     | ISO date string of last edit                                       |
| `peers[].role`            | peer    | Role hint: `registry` · `twin` · `third-party` · `archive`         |
| `peers[].cards_url`       | peer    | Raw URL of the peer's full card registry (convenience, optional)   |
| `peers[].note`            | peer    | Human-readable description surfaced in UIs                         |

**Role vocabulary** (non-exhaustive, case-insensitive):

- `registry` — authoritative minting repository. Typically one per federation.
- `twin` — publishes a seed-index that proxies another peer (usually the registry).
- `third-party` — independent binder with its own original cards.
- `archive` — historical binder; may be read-only or no longer accepting submissions.

Unknown roles MUST be treated as `third-party` for UX purposes. Binders SHOULD NOT use the `role`
field as a trust signal — it's a label, not an authorization claim.

A peer file with `canonical: true` SHOULD be preferred when multiple copies are known. A peer file
with `canonical_source` set SHOULD revalidate against that URL at load time if possible.

#### Resolution algorithm

When a binder receives an incantation or seed it doesn't own locally, it MUST:

1. Convert the incantation to a seed via §3.2.
2. Load its own `peers.json` (or the canonical list).
3. For each peer, **skip entries whose `binder` equals the resolver's own `binder` identity** — a
   binder never walks its own seed-index. This prevents self-recursion and redundant I/O.
4. For each remaining peer, fetch the peer's `seed-index.json`. Look up the seed string.
5. On first hit: fetch the pointer's `url`. If `url_is_bundle` is true, parse the response as a
   registry (top-level `cards` map or bare map) and extract the card at `bundle_key`. Otherwise
   parse the response as a single card object.
6. **Normalize the foreign card into the resolver's local shape.** Binders differ in field naming
   conventions (`agent_types` vs `types`, `rarity_tier` vs `rarity`, BigInt vs string seeds, etc.).
   The resolver SHOULD coerce fields it recognizes and leave unknown fields untouched. See §5.4.1.
7. Display the card. The resolver SHOULD surface the `binder` name of the source peer to the user
   (e.g. "Federated from `red-binder`") so provenance is never hidden.
8. **Auto-persist on resolve (MANDATORY for v1.1.2+).** When a federation walk returns a hit,
   the binder MUST store it locally with source metadata (`_foreign_binder`, `_foreign_home`,
   `_foreign_id`, or equivalent) before rendering. Resolution is ownership. Separate
   "Add to binder" UX is NOT permitted as a gate between resolving and owning.

   Rationale: incantations are content-addressed 7-word mnemonics. A user who knows their
   incantations MUST be able to reconstruct their entire collection by speaking them into any
   empty compliant binder. See Appendix B.

   Synthetic fallbacks (cards generated locally from a seed with no peer backing) MAY remain
   unsaved — only registered or federated cards become owned.

A binder MAY cache seed-index responses for up to 15 minutes. A binder MUST NOT cache them longer
than 24 hours without revalidation.

##### §5.4.1 Foreign-card normalization (recommended)

Binders SHOULD coerce a foreign card's fields using this mapping on ingestion, preserving all
original fields in the stored object:

| From (foreign)                   | To (local convention)          |
|----------------------------------|--------------------------------|
| `agent_types` (array)            | `types`                        |
| `rarity_tier` (string)           | `rarity`                       |
| `seed` (string if > 2⁵³)         | `seed` (BigInt in JS)          |
| `typed_abilities`                | `abilities`                    |
| `type_line` (string)             | kept verbatim                  |

Binders MUST NOT mutate a foreign card's `seed` value, `id`, `avatar_svg`, or ability effects —
these are the content-addressed core. Only naming conventions may be remapped, and the original
fields SHOULD remain intact alongside their mapped equivalents.

#### Why this works

- **No coordination.** Adding a new binder is a git PR, not a protocol negotiation.
- **Static JSON only.** Everything rides on `raw.githubusercontent.com`. No servers, no APIs.
- **Content-addressed.** The seed is BLAKE2b of the agent — two binders cannot claim the same
  seed without bit-identical agent source. Forgery is cryptographically prevented.
- **Federation is optional.** A binder that wants to be an island can simply not implement §5.4
  — it's still SPEC v1.0 compliant and can live alone.

The incantation is the universal URL. 7 words. Any binder. Any time.

---

## §6. Trust, minting, and registry

RAPPcards are **self-sufficient**. RAR is **the optional central mint**.

| Action               | Requires registry? | Notes                                                         |
|----------------------|-------------------|---------------------------------------------------------------|
| Run an agent         | No                | `agent.py` is the runtime — just execute it.                  |
| Compute seed         | No                | BLAKE2b of the source.                                        |
| Speak an incantation | No                | Math on the seed + wordlist.                                  |
| Show a card          | No                | Any binder can render from derived stats.                     |
| Publish a **named** card with authoritative `meta` | **Yes — RAR** | The RAR submission pipeline validates the `__manifest__` and mints. |
| Resolve `@pub/slug` → canonical card | Yes — registry | Name ownership lives in the registry.                         |

Registration with RAR requires:

1. `__manifest__` dict in the agent source (see RAR submission docs).
2. A pull request to `kody-w/RAR` adding the agent.
3. CI validation via `rapp_sdk.py`.

A card not in the registry is still a card. A binder MAY display and trade unregistered cards; when
it does, it SHOULD mark them with an "Unregistered" badge and link to the RAR mint form.

---

## §7. Security & privacy

- A binder MUST NOT execute agent code in the browser context.
- A binder MUST sanitize `avatar_svg`: strip `<script>` tags, inline event handlers, and external
  URIs. Render in a sandboxed `<iframe>` or via a strict allowlist parser.
- A binder MUST NOT transmit binder contents to a server without explicit user action.
- Import MUST validate types and reject entries with invalid `seed_str`, wrong `schema`, or
  unregistered publisher formats.

---

## §8. Versioning

This spec uses [SemVer 2.0](https://semver.org/). Breaking changes to the card data model or seed
protocol require a major version bump. Additive changes (new optional fields, new types) are minor.
Binders SHOULD advertise the spec version they support via a `<meta name="rappcards-spec">` tag or
equivalent.

```html
<meta name="rappcards-spec" content="1.0">
```

---

## §9. Reference implementations

| Component            | Repo                                | Path                             |
|----------------------|-------------------------------------|----------------------------------|
| Seed + mnemonic      | `kody-w/RAR`                        | `rapp_sdk.py`                    |
| Registry data        | `kody-w/RAR`                        | `cards/holo_cards.json`          |
| Canonical binder     | `kody-w/RAR`                        | `binder.html`                    |
| Local-first binder   | `kody-w/RAPPcards`                  | `binder.html`                    |
| Card index view      | `kody-w/RAPPcards`                  | `index.html`                     |
| Third-party binder   | `kody-w/red-binder`                 | `binder.html`                    |
| Rebuild-from-memory  | `kody-w/twin-binder`                | `binder.html`                    |
| Submission pipeline  | `kody-w/RAR`                        | `submit.html` + CI               |

The `twin-binder` ships empty — a pure view over the federation — and demonstrates
Appendix B (a user holding a list of incantations reconstructs their collection by
speaking them into any empty v1.1.2+ binder).

All implementations MUST be reproducible from this document alone. Where this document and
`rapp_sdk.py` disagree, `rapp_sdk.py` wins for seed/mnemonic semantics, and this document wins for
everything else.

---

## §10. Change log

- **v1.1 (2026-04-17)** — Adds §5.4 **Federated seed resolution**. Defines `seed-index.json` and
  `peers.json` schemas. Establishes the canonical peers list at
  `https://raw.githubusercontent.com/kody-w/RAPPcards/main/peers.json`. A binder can now resolve
  any seed from any federated binder via static raw-URL lookups. Fully backward compatible: v1.0
  binders remain conformant, they simply won't resolve foreign seeds.
- **v1.1.2 (2026-04-17)** — **Mnemonic-as-ownership.** §5.4 step 8 upgraded from permissive
  ("if the user adds…") to mandatory: binders MUST auto-persist foreign cards on successful
  resolution. Resolution IS ownership. Adds Appendix B formalizing the rebuild-from-memory
  guarantee: an empty v1.1.2+ binder, given a list of incantations, reconstructs to the same
  owned state as the source binder. Wire format unchanged — this is a UX/storage contract
  tightening. v1.1.1 binders that only display foreign cards are non-conformant under v1.1.2.
- **v1.1.1 (2026-04-17)** — Clarifications to §5.4 based on real-world multi-binder deployment
  (RAR + RAPPcards + red-binder):
  - Documents optional `peers.json` fields: `canonical`, `canonical_source`, `updated`,
    `peers[].role`, `peers[].cards_url`, `peers[].note`.
  - Defines a non-exhaustive role vocabulary (`registry`, `twin`, `third-party`, `archive`) and
    states roles are labels, not trust signals.
  - Adds explicit walker self-skip rule (a binder never walks its own seed-index).
  - Adds §5.4.1 foreign-card normalization table (`agent_types → types`, `rarity_tier → rarity`,
    BigInt seed handling) with a `MUST NOT` on mutating content-addressed fields.
  - Strengthens provenance language: resolvers SHOULD surface the source binder name to the user.
  - No wire-format changes; any v1.1 binder is already v1.1.1 compliant.
- **v1.1 (2026-04-17)** — Adds §5.4 **Federated seed resolution**. Defines `seed-index.json` and
  `peers.json` schemas. Establishes the canonical peers list at
  `https://raw.githubusercontent.com/kody-w/RAPPcards/main/peers.json`. A binder can now resolve
  any seed from any federated binder via static raw-URL lookups. Fully backward compatible: v1.0
  binders remain conformant, they simply won't resolve foreign seeds.
- **v1.0 (2026-04-17)** — Initial public spec. Freezes wordlist, card schema, hash protocol, export
  envelope. Supersedes all prior informal conventions.

---

## Appendix A — Minimal conformance checklist

A binder is **RAPPcards-compatible v1.1.2** if and only if it:

- [ ] Parses cards matching §2's data model, including `seed` as BigInt/string.
- [ ] Ships the authoritative 1024-word mnemonic (§3.2).
- [ ] Encodes and decodes 7-word incantations per §3.2.
- [ ] Responds to the URL hash protocol in §5.1 (at minimum `#add`, `#seed`, `#incant`).
- [ ] Exports/imports the envelope in §5.2 with zero loss.
- [ ] Publishes a `seed-index.json` per §5.4 and resolves foreign seeds by walking `peers.json`.
- [ ] Skips its own entry when walking peers (§5.4 step 3).
- [ ] Surfaces the source `binder` name for any card displayed via federation (§5.4 step 7).
- [ ] **Auto-persists any card resolved via federation to local storage (§5.4 step 8).**
- [ ] Sanitizes SVG avatars (§7).
- [ ] Advertises `rappcards-spec` version (§8) — current value `1.1.2` or higher.

A binder is **RAPPcards-compatible v1.0** (legacy) if it meets all bullets above except the
federation and auto-persist items.

Everything else is UX.

---

## Appendix B — Rebuildable binders (v1.1.2+)

The fundamental guarantee of a v1.1.2+ binder:

> A user who knows their incantations can reconstruct their entire collection by speaking them
> into any empty compliant binder.

Formally: let `I = {i₁, i₂, …, iₙ}` be a set of 7-word incantations owned by a user. Let `B₀`
be any empty v1.1.2+ binder with access to the canonical `peers.json`. After the user enters
each `iₖ ∈ I` into `B₀`, the resulting binder state `B′` MUST contain `n` owned cards, each
resolvable to the same `(seed, canonical source, card contents)` tuple as in the user's
original binder (modulo normalization per §5.4.1).

This works because:

1. Incantations are content-addressed (§3.2): `words ↔ seed` is a bijection.
2. Seeds are content-addressed to canonical sources via `peers.json` federation (§5.4).
3. Resolution is ownership (§5.4 step 8): every successful resolve writes to local storage.

The binder is therefore a **view over the federation**, not a local database. The 7 words
in the user's head are the canonical source of truth for what they own. Losing the binder
is survivable. Forgetting the words is not.

This is why §3.2 fixes the 1024-word mnemonic: any change to the wordlist would invalidate
every incantation ever spoken. The mnemonic is permanent because ownership is permanent.

---

*The card is the agent made visible. The seed is its true name. Speak the words in any binder, and
the same card appears — because the universe agrees on the math.*
