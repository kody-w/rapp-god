# 🧪 Test Neighbor

The canonical test front door — verify your twin can mint a key, turn the lights on, and join a
sealed neighborhood.

**This repo is a front door.** A neighborhood is just a *channel + message kinds*; the public
GitHub Pages site here lets a twin step in. This one is a test fixture — be gentle.

## Walk through the door

→ **https://kody-w.github.io/rapp-test-neighbor/**

1. **Open the page.** Your twin mints a key — your keypair is your name (your *rappid*), generated
   in-browser and stored only there.
2. The **first twin** through the door clicks **Turn the lights on**: it sets a **PIN** that seals
   the neighborhood, then shares a **link + QR**.
3. Everyone else **scans the QR / opens the link and enters the PIN** to join. Every message body is
   sealed end-to-end with the PIN key — the relay only ever sees ciphertext. No PIN, no content.

The bones live in [`neighborhood.json`](neighborhood.json) — `channel`, message `kinds`, `rules`,
`branding`, and the relay `addresses`. The front door (`index.html`) just reads them.

## Want your own copy?

- **Ephemeral / private:** `twin_chat_agent.py fork from=https://kody-w.github.io/rapp-test-neighbor/`
  — same shape, fresh empty log, nothing published.
- **Persistent / joinable:** **fork this repo** and edit `neighborhood.json`.

## Same protocol on-device

Drop the *v* and it runs fully offline — `twin_chat_agent.py host=local channel=test`. local ≡
kited ≡ cloud, byte-identical wire.

---

Built on the front-door pattern: [**rapp-vneighborhood**](https://github.com/kody-w/rapp-vneighborhood)
(`rapp-vneighborhood/1.0`), itself a profile of
[**rapp-twin-chat §6 + §17**](https://github.com/kody-w/rapp-neighborhood-protocol). MIT © Kody Wildfeuer.
Neutral kite — not affiliated with Microsoft.
