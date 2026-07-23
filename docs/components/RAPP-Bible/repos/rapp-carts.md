# rapp-carts

**MCP & cartridges** — the cartridge spec (`rapp-cart/1.0`); master schema for the egg family.

- Canonical: https://github.com/kody-w/rapp-carts
- Schema: `rapp-cart/1.0`
- Master cartridge schema: `carts/SCHEMA.md`
- Default branch: `main`

## What it is

`rapp-carts` holds the **cartridge spec** — `rapp-cart/1.0` — and the master `SCHEMA.md` for the whole `.egg` cartridge family. It is the canonical definition of how a cartridge is shaped: the manifest, the kind field, the sealing, the hatch contract.

Every egg kind (organism, rapplication, session, neighborhood, estate) and the RACon experience cartridges trace back to this spec. The master packers / unpackers (the ZIP variants) live in the kernel's `utils/bond.py`; this repo is the *contract* those packers implement.

## What it provides

- `rapp-cart/1.0` — the cartridge contract.
- `carts/SCHEMA.md` — the master schema for the cartridge family.

See [`SCHEMAS.md`](../SCHEMAS.md) (the egg family) and [racon](racon.md).
