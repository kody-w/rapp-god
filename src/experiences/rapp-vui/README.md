# RAPP VUI

A hands-free, spatial **Virtual UI** for talking to a RAPP Brainstem. You **look
at what you want and pinch to select**; you speak and it answers out loud. An
immersive 3D scene with a living AI presence, instead of a chat box.

**The one principle:** the **gesture loop is the product** — gaze moves the
cursor, a pinch selects. Everything else serves that.

## Try it

**▶ Live demo (no setup): https://kody-w.github.io/rapp-vui/**

The demo runs a canned guided tour with **no server needed** — good for sharing
and gathering feedback. Mouse works out of the box; click **Enter hands-free** to
add face + gesture tracking (the camera never leaves your machine).

> ⚠️ **Early prototype (v0.1).** This is a work-in-progress against the
> [PRD](PRD.md) — shared *specifically* to collect feedback on the direction and
> the gesture feel. It is not the finished interface. The [build spec](VUI-SPEC.md)
> says to rebuild the interface cleanly with a live visual loop; consider this the
> straw man to react to.

## Server-agnostic — tether it to any brainstem

The VUI is just a client that `POST`s `/chat`. It isn't tied to any one flight —
point it wherever you want with `?server=`:

- **Standalone demo** (default): canned data, no server.
  → `https://kody-w.github.io/rapp-vui/`
- **Your local global brainstem**: `?server=http://localhost:7071`
- **A ring / flight**: `?server=<its url>`

> Note: a browser may block an **HTTPS** page (Pages) from calling
> **http://localhost** (mixed content). To tether to a local brainstem, run the
> VUI locally (open `index.html`, or serve it from the brainstem), or point it at
> an HTTPS brainstem. The standalone demo always works on Pages.

## The response protocol (what a brainstem returns)

```
{ "response": "<full text>|||VOICE|||<spoken line>|||HOLO|||{ \"prompt\": \"…\", \"options\": [{\"label\":\"…\",\"value\":\"…\"}] }" }
```

- `|||VOICE|||` → the spoken line (TTS + the voice-first transcript).
- `|||HOLO|||{prompt, options}` → the choices, rendered as portals orbiting the form.

The demo's "static brainstem" is one removable `<script>` block in `index.html`
that returns exactly this shape — delete it (or pass `?server=`) and the page is
byte-identical to the live client.

## Docs

- **[PRD.md](PRD.md)** — product requirements (goals, modalities, success criteria).
- **[VUI-SPEC.md](VUI-SPEC.md)** — build spec + non-negotiables + how to build it right.

## Feedback

Open an issue with what felt good, what felt junky, and (if you tried it)
how the **gaze + pinch** selection felt. That interaction is the whole ballgame.

<sub>Part of the RAPP platform. Code MIT; RAPP and the RAPP family of names are trademarks of the RAPP project.
Vision (camera + tracking) runs entirely in your browser and never leaves your machine.</sub>
