---
title: Why I keep my binder in Obsidian
created: 2026-04-18
tags: [essay, meta]
---

# Why I keep my binder in Obsidian

A RAPPcards binder is a view over a federation. The federation doesn't care what view you use. Most binders are web apps with their own UI, their own database, their own search. Mine is an Obsidian vault.

I made this choice because I already think in Obsidian. I keep my notes here. I write essays here. I have years of accumulated context that backlinks and tags into a graph I trust. When I summon a card from the federation, I want the card to land in *my brain*, not in some other app.

The federation makes this trivially possible. Cards are content-addressed via a 7-word mnemonic, and the canonical form is just JSON. Whatever produces the JSON is fine. So my vault stores cards as markdown notes with frontmatter, and a build script generates the JSON sidecars at commit time. The federation sees a normal binder. I see a normal vault.

What I get from this:

- **Graph view** of my collection — which cards I've connected, which clusters I've built
- **Full-text search** across both card metadata and my notes about each card
- **Backlinks** between cards, between cards and essays, between essays and tags
- **Daily notes** that log when I summoned what and why
- **My own taxonomy** via tags (`#insight`, `#archived`, `#wishlist`) without anyone's permission
- **Real notes about each card**, not a comment field bolted onto a row

What [[Production Line Optimization Agent]] is, to me, is not a row in a database. It's a note I've written about a tool I've used, with backlinks to other notes about other tools, with tags that reflect my own thinking, in a vault that will outlive whatever specific federation app I'm using right now.

This is the Karpathy second-brain pattern applied to a federated card protocol. The binder is the brain. The brain is in Obsidian. The federation just works.

## Related

- [[../README|Vault home]]
- [[../cards/Production Line Optimization Agent]]
- [[../cards/Anvil Tester]]
- [[../cards/Supply Chain Forecaster]]
