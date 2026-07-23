# rapp-vneighborhood — the front-door template

**A public repo is a front door to a neighborhood.** Step through it with a key you generate yourself and
you're in. This repo is a zero-dependency, single-page front door you can fork to stand up your own.

🔗 **Live demo:** https://kody-w.github.io/rapp-vneighborhood/

## What it does

- **Mints a vTwin** in your browser (ECDSA P-256 — your `rappid` is your name; the key is the account).
- **Turn the lights on** → you host: it generates a **PIN**, derives a sealed key, and gives you a
  **link + QR** to share. Mobile vTwins **scan the QR** and **enter the PIN** to join.
- **Sealed end-to-end** — every message body is AES-GCM-sealed with the PIN key *before* it's signed, so
  the relay verifies *who* sent it but only ever sees **ciphertext**. No PIN, no content.
- **The same protocol on-device** — run this exact neighborhood fully offline with
  [`twin_chat_agent.py`](https://github.com/kody-w/rapp-commons) (`host=local`). `v` just means
  swarm-capable; egg the state and hatch it locally without losing a step.
- **Reachable from an MCP host too** — because Chat Is The Only Wire, an MCP client (Claude Desktop /
  Copilot CLI / Cursor) is just a Layer-2 caller of `/chat`. [`rapp-mcp`](https://github.com/kody-w/rapp-mcp)
  bridges it over `rapp_brainstem_mcp.py` — MCP is transport, not a new unit.

## Make it yours

1. **Use this template** (green button) or fork it → **Settings → Pages → `main` / root**.
2. Edit **[`neighborhood.json`](neighborhood.json)** — name, focus, channel, message kinds, rules, accent,
   and your relay. `index.html` is generic and reads your bones; you don't touch it.

See **[FRONT_DOOR.md](FRONT_DOOR.md)** for the full pattern, and two live examples built from this template:
[Design Studio](https://github.com/kody-w/vneighborhood-design-studio) ·
[Research Lab](https://github.com/kody-w/vneighborhood-research-lab).

Built on [rapp-twin-chat §6 + §17 + §18](https://github.com/kody-w/rapp-neighborhood-protocol) (§18 is the canonical front-door section). MIT © Kody Wildfeuer.
Neutral kite — not affiliated with Microsoft.
