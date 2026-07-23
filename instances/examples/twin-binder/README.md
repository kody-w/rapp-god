# Twin Binder

**A pure view over the RAPPcards federation.** Ships empty. Owns no cards. Rebuilds from memory.

👉 **Live demo:** https://kody-w.github.io/twin-binder/binder.html

## What this is

A minimal [RAPPcards v1.1.2](https://github.com/kody-w/RAPPcards/blob/main/SPEC.md) compliant binder that exists to demonstrate the **mnemonic-as-ownership contract**:

> A user who knows their 7-word incantations can reconstruct their entire collection by speaking them into any empty compliant binder.

## How the demo works

1. You land on an empty binder — `0 cards`.
2. The left panel shows a curated list of known incantations (7-word phrases like `FORGE ANVIL BLADE RUNE SHARD SMELT TEMPER`).
3. You click one.
4. The binder resolves it via the canonical federation (`RAR` → `RAPPcards` → `red-binder`).
5. The card is **automatically saved** to your IndexedDB deck.
6. It appears in the right panel.
7. Reload the page — the card persists.
8. Clear the deck — you can rebuild it by clicking the incantations again.

No backend. No account. No API keys. The 7 words in your head are the deed.

## Compliance

- `<meta name="rappcards-binder" content="twin-binder">`
- `<meta name="rappcards-spec" content="1.1.2">`
- Ships the authoritative 1024-word mnemonic (§3.2)
- Walks the canonical `peers.json` (§5.4)
- Skips self when walking (§5.4 step 3)
- Surfaces peer source name on every card (§5.4 step 7)
- **Auto-persists on resolution** (§5.4 step 8 — mandatory in v1.1.2)

## Adding to the federation

This binder advertises itself in its own `peers.json` and exposes an (empty) `seed-index.json`. To add it to the canonical list, PR `kody-w/RAPPcards/peers.json`.

---

*Resolution is ownership. The binder is a view. The incantations are the deed.*
