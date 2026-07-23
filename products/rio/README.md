# 🌐 RIO — Rapplication Internet Online

An **early‑web‑style browser** for the RACon ecosystem — a rapplication you load into RACon to
**browse and use the kited ecosystem online**.

The kernel **brainstem** boots **RACon** (the console); you insert the **RIO `.egg` cartridge**; it
hatches into the RIO twin; and now you have a little browser — address bar, links, Back — for a new
web: the **kited web** of distributed agents.

## Use it

- **Standalone:** open **[RIO →](https://kody-w.github.io/rio/)** — type an address (`home`, `carts`,
  `map`, `registry`, `about`) or click a link.
- **In RACon:** insert the cartridge — paste `https://raw.githubusercontent.com/kody-w/rio/main/rio.egg`
  into RACon's *Insert an .egg cartridge*, then talk to the RIO twin: `go=carts`, `go=cart:cowork_cookbook`.

## What you browse

`rapp://home` (portal) · `rapp://carts` (the cartridge directory — what you can insert into RACon) ·
`rapp://cart:<id>` (preview a cartridge + its `.egg` URL) · `rapp://map` (the ecosystem) ·
`rapp://registry` (the live rapp‑god registry) · `rapp://about`.

## RIO completes the OSI stack

RIO is the **application layer (L7)** of the fully on‑device, GitHub‑account‑powered agent ecosystem:

```
L7  Application ... RIO (this browser) + rapplications
L5  Session ....... twin-chat (scan-to-join, the cross-device PIN)
L4  Transport ..... the sealed channel (AES-256-GCM over the wire)
L3  Network ....... the kited layer (the web of devices + twins)
L1  Host .......... your brainstem, on your device
```

The kited layer is the network — the web that connects every device and twin. **RIO is the browser
on it.** An early browser for a new web.

Part of the RAPP ecosystem — see the [map](https://github.com/kody-w/rapp-map) and
[VISION.md](https://github.com/kody-w/rapp-map/blob/main/VISION.md). MIT © Kody Wildfeuer. Not
affiliated with Microsoft.
