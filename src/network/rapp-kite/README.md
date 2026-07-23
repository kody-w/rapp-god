# rapp-kite

**The string.** Command‑line + Chrome‑DevTools‑Protocol tools to *fly* and *operate* kited twins —
the operator half of the [rapp-neighborhood-protocol](https://github.com/kody-w/rapp-neighborhood-protocol)
(§5a kite transport). Each speaks the [rapp-sealed](https://github.com/kody-w/rapp-sealed) channel.

| Tool | What it does |
|------|--------------|
| `vbridge.sh <peer> <token> <ask\|eval\|run\|chat\|agents\|health> …` | join a hosted vBrainstem neighborhood from a shell and operate it over WebRTC, **sealed** |
| `kited_twin.js --port <cdp> [--brainstem <url>] [--once]` | hold the **string** to a local kite tab via CDP; `--brainstem` makes the twin **tethered** to a local brainstem |
| `kite_vtwin.js --port <cdp> --brainstem <url>` | kite a **deployed** vBrainstem tab: override its `rapp.chat` to tether to a local brainstem, overlay the kite + scan‑to‑join QR |
| `claude_bridge.js <cdp> <brainstem>` | front a deployed public page to a local brainstem (the page never touches localhost — the string does) |

These are operator tools (run separately), not part of the single‑file app. They let an operator —
canonically Claude — be the connective tissue between a public/browser peer and a machine's local
brainstem, on‑device.

> The CDP hop **stays on the machine** (Chrome's debug port is unauthenticated); cross‑machine
> traffic rides WebRTC + the seal. See the protocol §5a.

Reference runtime: [vBrainstem](https://github.com/kody-w/vbrainstem). Ecosystem [map](https://github.com/kody-w/rapp-map). MIT © Kody Wildfeuer.
