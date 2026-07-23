# obsidian-binder

**Your Obsidian vault, but it's also a [RAPPcards](https://github.com/kody-w/RAPPcards) binder.**

Karpathy-style second brain meets the federated card protocol. Each card is a markdown note in your vault. You write your own notes about the cards you've summoned. Obsidian gives you backlinks, tags, graph view, and full-text search over your collection. A build script keeps the federation files (`seed-index.json`, JSON card payloads) in sync so other binders can resolve from yours.

## The premise

A RAPPcards binder is just three things:
1. A `peers.json` advertising who you federate with
2. A `seed-index.json` listing the cards you own
3. JSON card payloads other binders can fetch

Nothing in the [SPEC](https://github.com/kody-w/RAPPcards/blob/main/SPEC.md) says cards have to be authored as JSON. So we don't. We author them as **markdown notes with YAML frontmatter** — Obsidian's native format — and a tiny build script generates the JSON sidecars at commit time.

The result: your binder is your vault. You read it in Obsidian. You search it in Obsidian. You add backlinks between cards. You write essays *about* cards. The card notes are your second brain. The federation just works.

## Vault structure

```
vault/
├── .obsidian/              ← Obsidian workspace config
├── cards/                  ← One markdown note per card
│   ├── Production Line Optimization Agent.md
│   ├── Supply Chain Forecaster.md
│   └── ...
├── essays/                 ← Your notes connecting cards
│   └── why-anvil-tester-changed-my-mind.md
├── binder.html             ← Open in browser to summon new cards
└── README.md               ← Your vault's home note
```

Open `vault/` in Obsidian. The cards/ folder is your collection. Use Obsidian's graph view to see how your cards connect. Use full-text search to find anything.

## Card frontmatter

Every card note has a frontmatter block that the build script reads:

```yaml
---
seed: "11447213470199194507"
incantation: "BRAND CUTLASS BREACH ANVIL COIL MUSK BESTOW"
name: "Production Line Optimization Agent"
agent_id: "rar-prod-opt-001"
source: "rar"
created: 2026-04-18
tags: [card, agent, productivity]
---

# Your notes here

Anything you want. The body is yours. Write about why you summoned this card,
how you've used the agent, what you've learned. Use [[Backlinks]] to connect
cards. Tag with #insights, #failed, #wishlist, whatever.
```

The frontmatter fields the federation needs:
- `seed` — the 64-bit integer seed (as a string)
- `incantation` — the 7-word phrase
- `name` — human-readable card name
- `agent_id` — the underlying agent identifier

Everything else in the frontmatter (`tags`, `created`, custom fields) is for *you*. The build script ignores it. Obsidian uses it.

The body is yours. Karpathy doesn't write structured JSON in his second brain. Neither do you.

## Build

```bash
python scripts/build.py
```

Reads `vault/cards/*.md`, generates:
- `seed-index.json` (at repo root, federation-ready)
- `cards/{seed}.json` (one per card, federation-ready)

Auto-runs on push via GitHub Actions. Your job is to write notes; the federation files take care of themselves.

## Summon a card

Open `vault/binder.html` in your browser. Paste an incantation. The federation walker fetches the card from whichever peer owns it, and writes a new markdown note to `vault/cards/` with the frontmatter pre-populated and an empty body for your notes.

Then you commit. The build script runs. Your binder now owns that card.

## Federation

This vault is a peer in the canonical [RAPPcards federation](https://raw.githubusercontent.com/kody-w/RAPPcards/main/peers.json). Other binders can resolve cards you own; you can resolve cards they own. See the [federation post](https://kodyw.com/2026/04/17/federated-cards-four-json-files.html) for how the walker works.

## Why this matters

A binder is a view over a federation. Most views are databases. This view is a *second brain*. Your cards aren't rows; they're notes. Your collection isn't a table; it's a graph. Your binder isn't a website; it's a vault.

You already know how to use Obsidian. Now you can use it as your interface to a federated card protocol. The mnemonic-as-ownership contract still holds — speak the seven words, get the card. But the place you read and think about your cards is the same place you do all your other thinking.

Ownership is a deed. The binder is a brain. Obsidian is the brain.

## Read more

- [RAPPcards SPEC](https://github.com/kody-w/RAPPcards/blob/main/SPEC.md) — the full protocol
- [Mnemonic-as-Ownership](https://kodyw.com/2026/04/17/mnemonic-as-ownership.html) — why the 7 words are the deed
- [A Federated Card Protocol in Four Static JSON Files](https://kodyw.com/2026/04/17/federated-cards-four-json-files.html) — how the walker works
- [Twin Binder](https://kody-w.github.io/twin-binder/) — the empty-binder rebuild demo
