# The Red Binder

**A third-party [RAPPcards](https://kody-w.github.io/RAPPcards/) binder with its own 21-card crimson forge-guild deck.**

Live at **[kody-w.github.io/red-binder](https://kody-w.github.io/red-binder/)**.

This binder is **not** a fork, not a twin, not a mirror — it's an independent implementation of
[RAPPcards SPEC v1.1](https://kody-w.github.io/RAPPcards/SPEC.md) with its own deck, its own
art, its own registry. It proves the spec: any binder can publish its own cards, and every card
is summonable from every other binder via the federated seed-index protocol.

## The deck

21 cards, crimson-themed, arranged in three tiers:

- **3 Starter cards** (experimental) — the apprentices of the red guild
- **8 Core cards** (community) — the working members
- **7 Elite cards** (verified) — the masters
- **3 Legendary cards** (official) — the foundational myths

Every card is rendered from a deterministic single-file `agent.py` in [`agents/`](agents/).
The canonical seed is BLAKE2b-64 of the agent source (per SPEC §3.1). Every seed encodes
losslessly to a 7-word incantation from the authoritative 1024-word mnemonic.

## Federation — the whole point

The Red Binder publishes three public JSON files at `raw.githubusercontent.com`:

| File | Purpose |
|------|---------|
| [`cards.json`](./cards.json) | The full 21-card registry |
| [`seed-index.json`](./seed-index.json) | Maps every seed → the raw URL of that card's JSON |
| [`peers.json`](./peers.json) | Federation bootstrap (list of peer binder seed-indexes) |
| [`cards/<slug>.json`](./cards/) | Each card as its own file (URL targets of the seed-index) |

Any binder that speaks SPEC v1.1 can:

1. Hear an incantation it doesn't recognize.
2. Walk its `peers.json` list.
3. Fetch each peer's `seed-index.json` from raw.githubusercontent.com.
4. Find the seed → follow the `url` field → fetch the card JSON directly.
5. Display it. Optionally add it to the local binder.

No servers. No APIs. No inter-binder handshake. Just static JSON on GitHub and 7 words.

## Speak the incantation anywhere

Try any of these incantations in **any** SPEC-compliant binder — they all resolve to a Red Binder card:

| Card | Incantation |
|------|-------------|
| Ember Scout (starter) | `WELD BURST DEEP JINX RUNT HALL GONG` |
| Forgesong Bard (core) | `BRAND HALL EMPIRE PROUD SLIME MATRIARCH REVENANT` |
| Pyrolith Warsmith (elite) | `STAMP ZAP EFFACE CHARM BROKE DISMISS LEFT` |
| The First Kindler (legendary) | `STAMP WILL GONG REMISS SKILL HICKORY PORTENT` |
| Red Binder, Prime (legendary) | `ETCH POWER FLINT HARBINGER VERVE LABYRINTH SPIN` |

Full list in [`seed-index.json`](./seed-index.json).

### Try it now

- In **[this binder](https://kody-w.github.io/red-binder/binder.html)** → Summon tab → paste any incantation above
- In **[RAPPcards](https://kody-w.github.io/RAPPcards/binder.html)** → Summon tab → paste any Red Binder incantation
  - (requires RAPPcards v1.1 update with federation — see SPEC §5.4)
- In **[RAR](https://kody-w.github.io/RAR/binder.html)** → Seed Resolver → paste any incantation
  - (RAR resolves its own cards natively; Red Binder cards require federation support)

## How to join the federation

Add your binder in 3 steps:

1. **Publish a `seed-index.json`** on GitHub at a stable raw URL, mapping each of your card seeds to a raw URL pointing to that card's full JSON.
2. **Add a `<meta name="rappcards-spec" content="1.1">` tag** to your binder HTML.
3. **Open a PR** to [kody-w/RAPPcards/peers.json](https://github.com/kody-w/RAPPcards) adding your binder to the canonical peer list.

That's it. Any compliant binder worldwide will now resolve your cards via incantation.

## Schema

Follows [RAPPcards SPEC v1.1](https://kody-w.github.io/RAPPcards/SPEC.md) exactly — see §2 for
card data model, §3 for seed + mnemonic, §5 for interop, §5.4 for federation.

## License

MIT. The 21-card deck art and stats are original to this repo; the spec and wordlist come from
[kody-w/RAPPcards](https://github.com/kody-w/RAPPcards) and [kody-w/RAR](https://github.com/kody-w/RAR).
