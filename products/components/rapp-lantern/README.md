# rapp-lantern

The universal player for **holographic organisms**. Drop in *any* `.egg` and orbit it in genuine 3D — regardless of source or species. Self-contained, no CDN, no backend; nothing leaves your device.

**Live:** https://kody-w.github.io/rapp-lantern/

## What's an `.egg`?

An `.egg` is a [`hologram-cartridge/1.0`](https://github.com/kody-w/rapp-static-apis) JSON — a self-describing, content-addressed organism with a layered genome (**form / surface / motion**). The player interprets it with **zero per-species code**, so the same lantern renders a weather sky, the moon, a crossbred hybrid, or an original box-creature identically well — as a 3D form you drag to orbit. Visible controls and the arrow/WASD, `+`/`-`, and Home keys provide complete orbit, zoom, reset, and pause access.

`.egg` is just JSON; the extension is a hint. Any valid `hologram-cartridge/1.0` loads.

## Use it

- **The loader** (`index.html`): drop an `.egg` anywhere on the page, pick a file, paste JSON, or load a URL — then **unload** and load another. Eight example eggs cover every supported shape, pattern, and symmetry plus multi-window composition. Every confirmed specimen gets a prepared Share/Copy/QR/Download dock. Deliberately opened specimens enter a content-addressed local Field Journal with search, pin, reopen, remove, and pin-safe recent clearing; automatic startup never counts as a discovery. The journal preserves up to 16 pins, eight unpinned recents, and 24 MiB, with explicit storage-protection and quota feedback.
- **Embed the player** directly, no loader needed:
  - `player.html?id=moon` for a bundled, registry-verified specimen
  - `player.html?cart=<url-to-an-egg>`
  - `player.html#<base64url(JSON.stringify(egg))>`
  - `player.html?embed=1#<base64url(JSON.stringify(egg))>` for a canvas-only responsive embed
  - or `postMessage({type:'load-cartridge', version:1, loadId:'mine', cart:<egg>}, playerOrigin)` into an `<iframe src="player.html">`. The player accepts only its parent window and replies with a scoped `rendered` or `error` event. Protocol v1 also exposes `prepare-share` and forwards embedded file drops over either a MessageChannel or the direct parent transport.

Every load path validates the cartridge before replacing the current organism. Remote loads are limited to HTTP(S), 2 MiB, and 15 seconds; malformed or stale loads leave the current scene intact.

Shared player URLs accept exactly one source: a fragment, `cart`, or `id` plus its optional content hash. Ambiguous or unverifiable links fail closed instead of substituting another organism.

Copy-link and QR actions use registry URLs bound to the complete cartridge hash when a specimen matches `registry.json`; imported eggs use self-contained hash links. The local QR encoder supports payloads through 997 bytes. Native Share falls back to the exact `.egg` file for larger cartridges, with download as the universal fallback.

Standalone shared specimens expose an explicit **Keep in Field Journal** handoff. The handoff carries the exact cartridge in a bounded canonical fragment, revalidates it in the loader, and records it as pinned only after a confirmed render and durable Journal commit.

Animation pauses while hidden or offscreen, preserves its logical clock when resumed, and honors live `prefers-reduced-motion` changes. Manual orbit and zoom continue to redraw in reduced-motion or paused mode.

## Content identity

Genome IDs and registry content hashes use `rapp-canonical-json/1`: object keys sort by UTF-16 code units, while strings and finite numbers use ECMAScript `JSON.stringify` serialization. Non-JSON values, non-finite numbers, and malformed Unicode are rejected. [`canonical-vectors.json`](canonical-vectors.json) provides canonical bytes and SHA-256 golden vectors for producers in other runtimes.

## Make eggs

Any `hologram-cartridge/1.0` works. Capture, breed, and export them in the cabinet:
**https://kody-w.github.io/rapp-static-apis/hologram/**

## Files

- `player.html` — the universal 3D Lantern (hand-written software-3D, self-contained, no CDN).
- `index.html` — the load/unload-any-`.egg` UI.
- `registry.json` — content-hashed catalog for stable bundled-specimen permalinks.
- `canonical-vectors.json` — cross-runtime golden vectors for `rapp-canonical-json/1`.
- `qr.mjs` — local QR encoder used by the share UI.
- `eggs/*.egg` — deliberately-diverse examples plus the built-in Lumina fallback.

## Conformance

Run `node test.mjs` to verify both cartridge gates, all bundled eggs and registry hashes, canonical byte/hash vectors, embedded defaults, strict bounded fragments, renderer cost limits, and QR version boundaries. GitHub Actions also runs `browser-test.mjs` against headless Chromium and WebKit for served-page loading, sharing, fail-closed links, and console errors.

Part of the RAPP static-API stack — content-addressed, forkable, no backend. The hash is the trust; the browser is the runtime.
