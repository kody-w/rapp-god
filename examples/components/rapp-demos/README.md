# rapp-demos

**Synced, scan‑to‑watch demos for rapid agent prototyping.** Open a demo on your laptop; it shows
an M365‑style surface and a control bar. Anyone who **scans the QR** (or opens the link) watches the
demo **move in real time on their own device** — read‑only — while *you* drive it **step by step**.
Built on the kited pattern: the link is **end‑to‑end sealed**, and the demo travels to the watcher
when they join.

**Live:** <https://kody-w.github.io/rapp-demos/>

## Why
A demo is just a scenario loaded into a **fixed template that looks like Microsoft 365** — only the
*text* changes. So prototyping a new agent experience = writing a small scenario file, dropping it
in, and driving it live for whoever's watching. No build, no deploy, no "share my screen."

## Use it
1. Open the player. Hit **Next ▶ / ◀ Prev** to walk the conversation one turn at a time.
2. Tap **📷 Share (QR)** → a watcher scans it (or opens the link). They now see exactly what you
   reveal, in sync, on their phone/tablet/another laptop. Close the tab and the session ends.
3. **⬆ Import** a scenario JSON to load any demo into the template; **⬇ Export** the current one.
   When you import, every watcher's view updates to the new demo automatically.

## A scenario is just text — `rapp-demo/1.0`
```json
{
  "schema": "rapp-demo/1.0",
  "appName": "Field Service Dispatch",
  "appIcon": "🚛",
  "script": [
    { "type": "user",  "content": "Dispatch emergency crews to the downtown outages." },
    { "type": "agent", "content": "Here's the optimized dispatch:",
      "agentData": { "title": "Emergency Dispatch", "status": "Complete",
        "details": { "Critical Outages": "3 locations · 2,847 customers", "Primary": "Crew A‑7 (15 min ETA)" } } }
  ]
}
```
Each entry is one turn: a `user` line or an `agent` reply (with an optional structured `agentData`
card). Generate one, import it, drive it. See [`scenarios/`](scenarios/) for two ready examples
(field service dispatch, predictive asset maintenance) — same template, different text.

## How it stays in sync (and private)
The host hosts a peer; watchers join over WebRTC. On join, the host sends the **whole scenario**;
then it sends only the **current step** as you click. Every message is sealed with
[rapp-sealed](https://github.com/kody-w/rapp-sealed) (AES‑256‑GCM, key from the link) — the broker
and the network never see the content. It's the [kited neighborhood](https://github.com/kody-w/rapp-neighborhood-protocol)
pattern, pointed at demos. Part of the RAPP ecosystem — see the [map](https://github.com/kody-w/rapp-map).

MIT © Kody Wildfeuer. The M365‑style template is a neutral facsimile for prototyping.
