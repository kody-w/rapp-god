# rapp-cart/1.0 — the cartridge spec

A **rapp_cart** (a *cartridge*) is the one thing a user ever has to understand. It is a file you hand
to **RACon** and it runs. That's the whole mental model.

> **If it's an `agent.py` or an `.egg`, it's a cartridge. Drop it in. It works.**
> Everything else is under the hood.

## 1. What a user knows

| The user sees | The user does NOT see |
|---------------|------------------------|
| **RACon** — the console UI/UX | brainstem.py, the bootloader |
| **Cartridges** — `agent.py` and `.egg` files | twins, ports, processes |
| Their app/game/tool running, with its own space | twin‑chat, sealing, the §13 hatch, the registry |

A nontechnical user installs an app by getting a **cartridge** and dropping it into RACon. They never
touch a port, a process, a protocol, or a line of code. RACon handles all of it.

## 2. The two cartridge forms

A `rapp_cart` is exactly one of these two file types — nothing else qualifies, and nothing else needs
to:

- **`agent.py`** — the **loader cartridge**. A single, hotloadable file. Small. On its own it's a
  working agent; in the RACon pattern it pulls its `.egg` payload on first run.
- **`.egg`** — the **payload cartridge**. A portable archive carrying *everything* the rapplication
  needs to run locally (its agents, persona, data, manifest).

A cartridge may be just an `agent.py`, just an `.egg`, or an `agent.py` paired with an `.egg` it
fetches (cloud by default, local optional). To the user these are all simply "cartridges" —
**rapp_carts**.

## 3. RACon — the user-facing layer

**RACon** (RAPP Agent Console) is the user‑facing UI/UX. It is what the user sees and uses. RACon:

- accepts cartridges (drag‑drop, link, store install — however),
- boots each one,
- presents the running rapplication and lets the user talk to it,
- manages them like installed apps/games on a console — list, open, eject.

There is also **vRACon** — the exact same experience in the browser (the vBrainstem, via Pyodide).
Same cartridges, no install.

And **RACon Kited** — the online layer. Your cartridge keeps running locally on your main device
(anchored where your data is), but a *kited* RACon on another device — your phone, on the go —
reaches it and drives it. Cross‑device, and **multiplayer** the moment you hand someone the kite.
It's a console's online service, for your rapplications: built on the kited twin pattern
(scan‑to‑join, sealed end‑to‑end, PIN‑confirmed). Defined in [`racon`](https://github.com/kody-w/racon).

## 4. The bootloader

**`brainstem.py` is the bootloader for RACon.** It's the firmware that brings the console up. A
completely nontechnical user never invokes it directly — it boots, RACon appears, they insert
cartridges. (Technical users can run it, point it at cartridges, and inspect everything below.)

## 5. Under the hood (not user‑facing)

When a cartridge is inserted, RACon — via the bootloader — does all of this invisibly:

- hatches the cartridge as its **own twin on its own port** (RAPP Store SPEC §13, `runtime:"twin"`),
- gives it its **own workspace + persona**, isolated from every other cartridge and the host,
- wires it to the console over **twin‑chat** (`rapp-twin-chat/1.0`),
- registers it so the console can list/drive/eject it.

None of these words ever need to reach the user. They are implementation detail beneath the
cartridge abstraction.

## 6. The contract

A conforming host MUST let a user:

1. **Insert** a cartridge (`agent.py` or `.egg`) with a single gesture.
2. Have it **boot and run** with no further setup — the host resolves the payload (cloud default),
   unpacks it, and brings the rapplication up.
3. **Use** the rapplication (talk to it, see its surface) as a first‑class app — with its own space.
4. **Eject** it cleanly.

Everything beyond steps 1–4 is the host's business, hidden by RACon.

## 7. Why

A console only ever asks you to know one thing: the cartridge. You don't manage the runtime, the
memory map, or the process model — you pop in the cartridge and play. `rapp-cart/1.0` makes RAPP feel
the same: **the cartridge is the only unit, RACon is the only surface, everything else is under the
hood.**

---

Builds on / hides: [RAPP Store SPEC §13](https://github.com/kody-w/RAPP_Store/blob/main/SPEC.md)
(twin‑port runtime), [rapp-neighborhood-protocol](https://github.com/kody-w/rapp-neighborhood-protocol)
(twin‑chat), [rapp-egg-hub](https://github.com/kody-w/rapp-egg-hub) (`.egg`). First cartridge:
[cowork-cookbook-rapp](https://github.com/kody-w/cowork-cookbook-rapp). MIT © Kody Wildfeuer.
