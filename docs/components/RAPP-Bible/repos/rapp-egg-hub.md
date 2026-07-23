# rapp-egg-hub

**Stores & catalogs** — the public hub for `.egg` cartridges.

- Canonical: https://github.com/kody-w/rapp-egg-hub
- Schema: `rapp-egg-hub-entry/1.0`
- Default branch: `main`

## What it is

The **egg hub** is the public catalog of `.egg` cartridges — the place an organism, rapplication, session, or estate egg can be backed up and shared when sneakernet isn't enough. Submissions arrive as labeled GitHub Issues (`egg-submission`); each entry carries an `rapp-egg-hub-entry/1.0` record.

It is one of the three catalogs alongside [RAPP_Store](RAPP_Store.md) (rapplications) and [RAPP_Sense_Store](RAPP_Sense_Store.md) (senses).

## What it provides

- A public download surface for `.egg` cartridges of every kind.
- Issue-based submission (the `egg-submission` consent flow).
- A backup target so an organism survives a lost laptop (eggs hatch identically anywhere — same rappid).

The one agent reaches this via `backup_to_egg_hub` (a `to_close` action) — see [`CAPABILITIES.md`](../CAPABILITIES.md).
