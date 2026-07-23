# rapp-basket

Your eggs, kept in this browser — **offline, private, yours**. A personal collection of every holographic organism you catch or make; **import and export** the whole basket to move it between devices or back it up.

**Live:** https://kody-w.github.io/rapp-basket/

## What it does

- **Keeps your eggs on-device** in IndexedDB — nothing leaves the browser without you.
- **Add** any `.egg` (drop files or pick them); each shows as a little palette-hued icon.
- **Preview** any egg in genuine 3D — click it and it hatches in the embedded Lantern.
- **Export the whole basket** as one `.basket.json` file; **import** one back on another device.
- **Download** any single egg to share it.

## A shared store

Every `rapp-*` surface lives on the same origin (`kody-w.github.io`), so this basket's IndexedDB is a **shared store** — [snap](https://kody-w.github.io/rapp-snap/), [the cabinet](https://kody-w.github.io/rapp-static-apis/hologram/), and [the lantern](https://kody-w.github.io/rapp-lantern/) can drop eggs straight into it (store name `rapp-basket`, keyed by content-address `id`).

## Files

- `index.html` — the basket, the IndexedDB store, import/export.
- `player.html` — the vendored universal 3D Lantern (preview).

Part of the RAPP static-API stack — content-addressed, forkable, no backend, no CDN.
