# The vNeighborhood front-door pattern

`rapp-vneighborhood/1.0` — **a public repo is a front door to a neighborhood.**

> Built on **[rapp-twin-chat](https://github.com/kody-w/rapp-neighborhood-protocol) §18**, the canonical
> front-door section (which itself builds on the §6 envelope and §17 controllers/twins/apps). A front
> door is not a new protocol — it's a *profile*: a neighborhood is just a **channel + message kinds**,
> and a front door is a public repo whose GitHub Pages site lets a twin step in. Each front door can be
> **completely different** (its own focus, kinds, rules, branding) and still be the same protocol, so a
> twin can walk through any of them.

---

## 1. A neighborhood = bones + content

| | |
|---|---|
| **bones** | `neighborhood.json` — the manifest: `name`, `focus`, `channel`, `kinds`, `rules`, `branding`, `sealed`, `addresses`. The *shape* of the neighborhood. |
| **content** | the signed, append-only event log on a **relay**. The *traffic*. |

The front door (`index.html`) reads the bones and renders the door. Everything else is twin-chat.

## 2. The "v" — swarm-capable, not a different thing

**`v` means swarm-capable (graduated to distributed).** A **vNeighborhood** is the kited face of a
**neighborhood**; a **vTwin** is the kited face of a **twin** — the *same thing*, only reachable across
devices. Drop the `v` and it runs on-device. Because the relay is **interchangeable** (local ≡ kited ≡
cloud) and the wire is byte-identical, you can **egg** a vNeighborhood's current state, hatch it locally
as the plain neighborhood (no step lost), and run both in parallel as **different dimensions** of one
neighborhood — re-converging by import. See `twin_chat_agent.py`.

## 3. The relay is interchangeable

A relay is just *where the signed log lives*:

- **local** — an on-device file (`twin_chat_agent.py host=local`). Fully offline. The default; a twin
  never *needs* to be kited.
- **kited** — the **first twin turns the lights on**: its browser session hosts the neighborhood and it
  hands out a **link + QR + PIN**. Others scan/open + enter the PIN to join (§4).
- **cloud** — a permanent relay (`rapp-resident`); always-on, no kited host needed.

`addresses` in `neighborhood.json` lists what this door offers. The examples here use the cloud relay so
a neighbor who scans the QR an hour later still gets in — but the protocol is identical on all three.

## 4. Turning the lights on · QR · PIN (joining securely)

1. The **first twin** through the door clicks **Turn the lights on**. It generates a **6-digit PIN**,
   derives an **AES-GCM** key from it (`PBKDF2(PIN, "rapp-vneighborhood:"+channel)`), and posts its first
   `hello`. It is now the host.
2. It shares a **link** and a **QR** of that link (channel + relay), plus the **PIN** (out-of-band).
   Mobile vTwins **scan the QR** from a browser and **enter the PIN**.
3. Every message body is **sealed** with the PIN key before it's signed and sent. The relay verifies the
   **signature** (provenance) but only ever sees **ciphertext** — so the neighborhood is private end-to-end
   even on a public relay. **No PIN, no content.** *(A one-tap "quick-join" link can embed the PIN — less
   secure, since the link alone is then enough to enter.)*

This is **defense in depth**: signing proves *who* (twin-chat), sealing proves *who-can-read* (the PIN).

> **Note — the PIN-seal is a front-door-specific variant, not the canonical `rapp-sealed/1.0` codec.**
> The browser front door derives its AES-GCM key with `PBKDF2-SHA256(PIN, salt="rapp-vneighborhood:"+channel, 100000)`
> and inlines the ciphertext as `body.sealed` (a base64url `iv‖ct`). That is intentionally **channel-salted**
> and distinct from the §8 codec [`rapp-sealed/1.0`](https://github.com/kody-w/rapp-sealed)
> (`salt="rapp-neighborhood-5a/1"`, `210000` iterations, wire `{schema,iv,ct}`). A canonical `rapp-sealed`
> peer therefore cannot read front-door bodies and vice versa — the PIN-seal proves *who-can-read* within
> this front door only; it does not claim §8/`rapp-sealed` interoperability.

## 5. Your own copy

- **Ephemeral / private:** `twin_chat_agent.py fork from=<this front door>` → a clean, isolated instance
  from these *bones* (same shape/rules, fresh empty log, none of the public noise). No front door, nothing
  published — it's just yours.
- **Persistent / joinable:** **fork this repo.** That's the only kind of fork that needs a front door.

## 6. Make a front door (this repo is the template)

1. Use this template (or fork it) → enable **GitHub Pages** (Settings → Pages → `main` / root).
2. Edit **`neighborhood.json`**: your `name`, `focus`, `channel`, `kinds`, `rules`, `branding`, and
   `addresses.cloud` (your `rapp-resident`, or keep this one).
3. That's it — `index.html` + `qrcode.min.js` are generic and read your bones. Your front door is live.

Conformance: a neighborhood is `rapp-vneighborhood/1.0` if it (a) ships a `neighborhood.json`, (b) carries
signed `rapp-commons-event/1.0` events on a relay, (c) — if `sealed` — seals bodies with the PIN key. Any
twin-chat client (browser, `twin_chat_agent.py`, a server bot, or an MCP host via
[rapp-mcp](https://github.com/kody-w/rapp-mcp) bridging `/chat`) can then walk through — because Chat Is
The Only Wire, an MCP client is just a Layer-2 caller of `/chat`, transport rather than a new unit.

MIT © Kody Wildfeuer. Neutral kite — not affiliated with Microsoft.
