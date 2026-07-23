# rapp-snap

Open your camera, snap a picture — and **the photo becomes a living 3D creature** you can keep. Entirely in your browser: no photo is uploaded or stored, only the organism it becomes.

**Live:** https://kody-w.github.io/rapp-snap/

## How it works

The snapshot is analyzed on-device, no upload:

- **dominant colors** → the creature's palette
- **brightness** → its glow
- **warmth** (warm vs cool) → its body shape (busy → a spiky star, warm & bright → a blob, cool & dim → a ring, muted → segments)
- **texture / busyness** → its spikes and limbs

Those become a [`hologram-cartridge/1.0`](https://github.com/kody-w/rapp-static-apis) genome — a self-describing, content-addressed organism the universal **[Lantern](https://kody-w.github.io/rapp-lantern/)** renders in genuine 3D you drag to orbit. **Same photo, same creature; a different photo, a different one.** Keep it as an `.egg` and it lives anywhere in the stack — the cabinet, the moment app, the lantern.

## Files

- `index.html` — camera capture + the photo→genome mapping.
- `player.html` — the vendored universal 3D Lantern (self-contained, no CDN).

Part of the RAPP static-API stack — content-addressed, forkable, no backend, no CDN. Nothing phones home.
