# Obsidian Binder — Vault Home

Welcome to your binder. Below is the live card grid (rendered from `binder-view.html`, regenerated on every commit). Cards live in [[cards/]] as markdown notes you can search, link, and graph like any other notes in your second brain.

<iframe src="binder-view.html" width="100%" height="700" style="border:1px solid #ccc;border-radius:8px"></iframe>

> If you don't see the grid above, your Obsidian doesn't allow iframes. Open `binder-view.html` directly: right-click in the file explorer → Show in system explorer → open in browser. Or enable HTML embeds in Obsidian → Settings → Editor.

## Three ways to read your binder

1. **The grid above** — `binder-view.html`, your card-flipping interface. Search, tag-filter, expand each card's federation JSON. Looks like a real binder.
2. **Obsidian's own UI** — open the [[cards/]] folder in the file explorer. Use graph view to see how cards connect. Use full-text search across all your notes about each card.
3. **The federation** — `seed-index.json` and `cards/*.json` at the repo root, fetchable by any other binder peer.

Same vault, three reading modes.

## How this vault works

- Each card lives in [[cards/]] as one markdown note
- Frontmatter holds the federation-required fields (seed, incantation, name, agent_id)
- The body is yours — write whatever you want about the card
- Use `[[wiki-links]]` to connect cards in the graph view
- Tag with `#insight`, `#wishlist`, `#archived`, or whatever fits your thinking
- A build script (`scripts/build.py`) regenerates `binder-view.html` and the federation files on every commit

## Summoning new cards

1. Open `binder.html` in your browser (separate from `binder-view.html` — this one is the summon UI)
2. Paste a 7-word incantation
3. The federation walker fetches the card from whichever peer owns it
4. A new markdown note is created in `cards/` with frontmatter pre-populated
5. Add your notes to the body
6. Commit — the GitHub Action regenerates the federation files AND the grid view

## Essays

[[essays/why-i-keep-my-binder-in-obsidian]] — the manifesto

## The cards

See `cards/` for the full collection (or scroll the grid above).
