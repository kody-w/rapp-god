# 🎴 rapp-carts

**The cartridge spec.** The one thing a user ever has to understand about installing a RAPP
rapplication:

> **If it's an `agent.py` or an `.egg`, it's a cartridge. Drop it into RACon. It works.**
> Everything else is under the hood.

## The idea

A console only asks you to know one thing — the cartridge. You don't manage the runtime, the memory
map, or the process model; you pop in the cartridge and play. `rapp-cart/1.0` makes RAPP feel the
same:

- **Cartridges** (`rapp_carts`) are the only unit a user knows — an `agent.py` (the loader cart) or
  an `.egg` (the portable payload cart).
- **RACon** is the only surface — the user‑facing console UI/UX. (And **vRACon**, the same thing in
  the browser; and **RACon Kited**, the online layer for cross‑device + multiplayer.)
- **`brainstem.py`** is the **bootloader** — it brings RACon up. Nontechnical users never touch it.
- **Everything else** — twins, ports, twin‑chat, the §13 hatch, the registry, sealing — is **under
  the hood**, hidden beneath the cartridge abstraction.

## Read the spec

→ **[SPEC.md](SPEC.md)** — `rapp-cart/1.0`: the two cartridge forms, the RACon layer, the bootloader,
what's hidden, and the insert→boot→run→eject contract.

## In the ecosystem

- The first cartridge: **[cowork-cookbook-rapp](https://github.com/kody-w/cowork-cookbook-rapp)**.
- The experience / north‑star (incl. RACon Kited): **[racon](https://github.com/kody-w/racon)**.
- Drive a running cartridge from any AI host: **[rapp-mcp](https://github.com/kody-w/rapp-mcp)** —
  the MCP gateway (`rapp-mcp-spec/1.0`). A non‑RACon way to reach the same cartridge: MCP is
  **transport** onto `/chat` (*Chat Is The Only Wire*), not another unit.
- Under the hood: [RAPP Store SPEC §13](https://github.com/kody-w/RAPP_Store/blob/main/SPEC.md) ·
  [rapp-neighborhood-protocol](https://github.com/kody-w/rapp-neighborhood-protocol) ·
  [rapp-egg-hub](https://github.com/kody-w/rapp-egg-hub).

MIT © Kody Wildfeuer.
