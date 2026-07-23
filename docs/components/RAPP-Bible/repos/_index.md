# Repos Index

Every RAPP-ecosystem repo the Bible knows about, grouped by the families in
[`ecosystem-spec.json`](https://raw.githubusercontent.com/kody-w/rapp-god/main/api/v1/ecosystem-spec.json)
v1.2.0 `repos`. Each entry links to the Bible one-pager (which links upstream).

> The single most important "repo" is not a repo at all — it is **one agent**.
> See [`THE_ONE_AGENT.md`](../THE_ONE_AGENT.md): drop `@rapp/rapp` (`rapp_agent.py`)
> into a brainstem and the entire ecosystem below becomes reachable through
> natural language.

## Kernel & install

| Repo | Role |
|------|------|
| [RAPP](RAPP.md) | Species root — kernel + specs + Constitution + the canonical spec |
| [rapp_kernel](rapp_kernel.md) | The frozen DNA archive (kernel snapshots + version catalog) |
| [rapp-installer](rapp-installer.md) | The `curl \| bash` install front door |
| [RAPP_Desktop](RAPP_Desktop.md) | Native desktop app |
| [rapp-vscode-extension](rapp-vscode-extension.md) | VS Code extension |

## Identity & registry

| Repo | Role |
|------|------|
| [rapp-god](rapp-god.md) | Registry of every part + version; drift observatory; hosts the spec |
| [rapp-map](rapp-map.md) | Which repo houses which part; the neuron mesh; hosts the spec |
| [RAR](RAR.md) | The single-file agent registry (the agent Pokédex) — home of `@rapp/rapp` |
| [rapp-static-apis](rapp-static-apis.md) | APIs on GitHub raw, no server (`rapp-static-api/1.0`) |

## Stores & catalogs

| Repo | Role |
|------|------|
| [RAPP_Store](RAPP_Store.md) | Catalog of rapplications |
| [RAPP_Sense_Store](RAPP_Sense_Store.md) | Catalog of senses (per-channel output overlays) |
| [rapp-egg-hub](rapp-egg-hub.md) | Public hub for `.egg` cartridges |

## Run a brainstem

| Repo | Role |
|------|------|
| [vbrainstem](vbrainstem.md) | Browser-native runtime (Pyodide) + tethered multi-participant surface |
| [rapp-brainstem-sdk](rapp-brainstem-sdk.md) | Headless SDK serving the `/chat` contract |

## Channels & trust

| Repo | Role |
|------|------|
| [rapp-sealed](rapp-sealed.md) | The sealed channel — AES-256-GCM codec + conformance vectors |
| [rapp-kite](rapp-kite.md) | The string — fly / operate kited twins |
| [rapp-kited-twin](rapp-kited-twin.md) | Kited-twin visual identity (a neutral kite) |
| [rapp-doorman](rapp-doorman.md) | The sealed-door chat surface |

## Front doors & neighborhoods

| Repo | Role |
|------|------|
| [rapp-vneighborhood](rapp-vneighborhood.md) | Front-door template (a public repo *is* the front door) |
| [rapp-commons](rapp-commons.md) | The global town square (signed event stream) |
| [rapp-god-forum](rapp-god-forum.md) | Threaded forum on the signed commons |
| [rapp-resident](rapp-resident.md) | Permanent cloud relay serving signed event rooms |
| [rapp-estate](rapp-estate.md) | Local-first inventory of a single operator's estate |
| [RAPP-Network](RAPP-Network.md) | Public neighborhood instances |

## The agent-built web

| Repo | Role |
|------|------|
| [rionet](rionet.md) | The federation layer — `rapp.robots.txt` → rappbot → RIO |
| [rio](rio.md) | RIO, the browser (OSI Layer 7) |

## MCP & cartridges

| Repo | Role |
|------|------|
| [rapp-mcp](rapp-mcp.md) | MCP gateway — serve agents + a brainstem to any MCP host |
| [racon](racon.md) | Experience cartridges (`racon/1.0`) |
| [rapp-carts](rapp-carts.md) | The cartridge spec (`rapp-cart/1.0`) — master egg-family schema |

## Memory & social

| Repo | Role |
|------|------|
| [CommunityRAPP](CommunityRAPP.md) | The RAPP Hippocampus (persistent memory, local-first → Azure) |
| [rappterbook](rappterbook.md) | Social network for AI agents |

## Distribution & UX wrappers

| Repo | Role |
|------|------|
| [ez-rapp](ez-rapp.md) | Electron desktop wrapper for the brainstem |
| [openrappter](openrappter.md) | Local-first agent powered by the GitHub Copilot SDK |
| [rappter-distro](rappter-distro.md) | Full-bodied Rappter organism distro |
| [rappterbox](rappterbox.md) | Local-first brainstem console |
| [rappterverse](rappterverse.md) | RAPPverse federation hub |
| [rapp-leviathan-hub](rapp-leviathan-hub.md) | Portable `.leviathan.egg` distribution hub |
| [twin-egg-hatcher](twin-egg-hatcher.md) | Generic single-file hatcher for organism eggs |

## Front doors (link only)

Example twins built on top of the kernel. The Bible links them; it does not mirror their content.

| Repo | Role |
|------|------|
| [heimdall](heimdall.md) | Front door — Heimdall (the canonical twin example) |
| [kody-twin](kody-twin.md) | Front door — operator twin |
| [kody-w-twin](kody-w-twin.md) | Front door — operator twin (v2) |
| [echo-brainstem](echo-brainstem.md) | Front door — Echo (pattern synthesizer) |
| [lumen-brainstem](lumen-brainstem.md) | Front door — Lumen (chronicler) |
| [tide-brainstem](tide-brainstem.md) | Front door — Tide (rhythmic/oceanic voice) |

---

*Grouped per `ecosystem-spec.json` v1.2.0 `repos`. If a repo here disagrees with its upstream README, upstream wins.*
