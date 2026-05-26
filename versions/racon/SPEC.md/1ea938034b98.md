# racon/1.0 — the RACon experience

The experience contract for RACon. It defines what a user is **promised**, the surfaces that deliver
it, and the line between what's **seen** and what's **hidden**. This is a UX/experience spec — the
mechanics live below it (see "Under the hood").

## 1. The promise

> You have **cartridges**. **RACon** is the only thing you see. Drop a cartridge in — it works, with
> its own space — at home, on the go, and together with others. You never touch a port, a process, a
> protocol, or code.

## 1a. Two layers — and the line between them

**The user layer — all a regular person ever needs to know:**

- **RACon** — the console they use.
- **their brainstem** — their AI; RACon runs on it (and boots it).
- **the kited twin** — their AI follows them across their devices, and can be shared (multiplayer).
- **shareable `.egg` cartridges** — the apps they get and pass around. Call them **`.egg` cartridges**
  (or just **eggs**) — "egg" is the friendly word: it incubates locally and *hatches* into their twin.
  ("Incubation file" is the same thing described; `.egg` cartridge is what you say.) A cartridge may
  also be a single `agent.py` loader that fetches its egg — see
  [rapp-carts](https://github.com/kody-w/rapp-carts).

**The builder layer — "RAPP speak":** agents, twin‑chat, the twin‑port runtime (SPEC §13), the
registry (rapp‑god), the neighborhood protocols, sealing, ports. Builders live here; **a regular user
never has to meet any of it.** If a user‑facing surface makes someone learn a builder‑layer word,
that's a bug, not a feature.

## 2. The local surfaces

- **RACon** — the console on the user's main device. Insert a cartridge → it boots → the user uses
  the running rapplication, which has its own memory, workspace, and persona.
- **vRACon** — the identical experience in the browser (the vBrainstem, via Pyodide). Same
  cartridges, zero install. Proven: a cartridge's `.egg` loads in‑browser and runs as a vTwin.

A user does the same one gesture for both: get cartridge → drop in → use.

## 3. RACon Kited — the online layer (cross‑device + multiplayer)

**RACon Kited** is to RACon what an online service is to a games console: it brings **cross‑device
collaboration** and **multiplayer** — without moving your stuff into the cloud.

- **It stays local.** Your cartridge keeps running as a twin on your **main device**, anchored where
  your data is. Nothing is uploaded.
- **You take it with you (kited).** A *kited* RACon on another device — your phone, on the go —
  reaches that locally‑running rapplication and **drives it remotely**. You're using the very same
  app, still running back home, from your hand.
- **Multiplayer.** Hand someone the kite (a scan‑to‑join code) and they're in the same rapplication
  with you, live. Co‑op for your AI apps.
- **Sealed + confirmed.** The kited line is end‑to‑end sealed (AES‑256‑GCM), joined by scanning a
  code, and a **matching PIN** is confirmed across the two devices before anything syncs — as
  private as if it were all on one machine.

Built on the kited twin pattern
([rapp-neighborhood-protocol](https://github.com/kody-w/rapp-neighborhood-protocol): twin‑chat,
the §5a transports, the sealed channel, scan‑to‑join, the cross‑device PIN). To the user it is just:
*"point your phone at the code and your app is here too."*

## 4. The experience contract

A conforming RACon MUST give the user, with no setup beyond a single gesture each:

1. **Insert** a cartridge → it boots and runs as a first‑class app with its own space.
2. **Use** it — talk to it, see its surface — like an installed app.
3. **Eject** it cleanly.
4. **Kite** it — reach and drive a locally‑running cartridge from another of the user's devices.
5. **Share** it — let an invited person join the same running rapplication (multiplayer), sealed.

No port numbers. No process management. No protocol words. No code.

## 5. Under the hood (never user‑facing)

RACon hides: the bootloader (`brainstem.py`), the per‑cartridge **twin on its own port** (RAPP Store
SPEC §13), **twin‑chat** (`rapp-twin-chat/1.0`), the `.egg` fetch/unpack, the twins registry, the
sealed channel and key handling, and the kite transports. These exist; none of them are the user's
concern.

## 6. Why this is the grail

A console wins by asking you to know exactly one thing: the cartridge. RACon holds that line for AI
apps. This document is the **frozen north‑star** — the canonical experience every layer beneath it
serves. Drift is measured against it: if a feature makes RACon more than *insert → it works → take it
anywhere → play together*, the feature is wrong, not the grail. See [GRAIL.md](GRAIL.md).

---

Cartridge spec: [rapp-carts](https://github.com/kody-w/rapp-carts) · first cartridge:
[cowork-cookbook-rapp](https://github.com/kody-w/cowork-cookbook-rapp) · MIT © Kody Wildfeuer.
