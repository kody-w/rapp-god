# This is the grail

`racon/1.0` is the **canonical, frozen experience** for RACon — the north‑star the whole RAPP
ecosystem is measured against. Like a frozen kernel, it is referenced, not casually edited.

## What "grail" means here

- It is the single source of truth for **what the user experiences** — not how it's built.
- Every layer beneath it (cartridges, twins, twin‑chat, the `brainstem.py` bootloader, the kited
  transports, the sealed channel) exists to *serve* this experience. They may change freely; the
  experience may not regress.
- Any proposed change is judged against the promise:
  **insert a cartridge → it works → take it anywhere → play together**, with nothing technical ever
  reaching the user.

## How to honor it

- New surfaces — third‑party consoles, the browser vRACon, partner hosts — implement *this*
  experience, not their own dialect.
- If a feature makes RACon more than the promise, the feature is wrong, not the grail.
- Drift is detectable: [rapp-god](https://github.com/kody-w/rapp-god) can track this file as a part
  across the ecosystem, so any copy that diverges shows up.

Frozen north‑star. MIT © Kody Wildfeuer.
