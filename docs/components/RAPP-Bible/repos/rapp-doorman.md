# rapp-doorman

**Channels & trust** — the sealed-door skill; the chat surface behind a front door.

- Canonical: https://github.com/kody-w/rapp-doorman
- Default branch: `main`

## What it is

The **doorman** is the chat view behind an organism's front door. A front door is a static page anyone can open; the doorman is what turns it into a live conversation. It handles the Copilot device-code auth flow (via a Cloudflare worker), runs agents in the browser via Pyodide, surfaces a memory pane, lets the visitor pick a model, and exports an ascended egg.

It also owns the **sealed door** — the AES-256-GCM encrypted channel (OSI Layer 5 trust scope). Install the doorman skill when you need an organism to hold a private, end-to-end-sealed conversation rather than a public summon.

## What it provides

- The reference doorman chat surface (`RAPP.Doorman` namespace).
- The sealed-channel codec integration (`rapp-sealed/1.0`).
- Offline fallback when the network drops (cached state keeps rendering).

The god agent reaches doorman capability via `install` — it is install-routed, not native (see [`CAPABILITIES.md`](../CAPABILITIES.md)).
