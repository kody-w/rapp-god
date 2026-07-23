# 🍳 Cowork Cookbook — a RACon vTwin rapplication

The [Cowork Cookbook](https://github.com/seangalliher/Coworkcookbook) as a **vTwin rapplication**,
distributed the **RACon** (RAPP Agent Console) way: insert one cartridge, the brainstem hatches it as
its own running twin.

A specialized twin that turns Microsoft Copilot **Cowork** recipes into single‑file agents with
**WorkIQ** access — so any recipe becomes a runnable agent that behaves like Cowork once WorkIQ is
wired into your host.

## Use it — RACon style (one file, insert the cartridge)

1. **Download the one export:** [`cowork_cookbook_agent.py`](cowork_cookbook_agent.py). That's the
   whole cartridge label — nothing else to copy.
2. **Drop it** into your local `brainstem.py`'s `agents/` directory.
3. **Run it.** It pulls [`cowork_cookbook.egg`](cowork_cookbook.egg) from this repo (raw GitHub),
   unpacks it fully locally, and your brainstem **spins it up as its own twin on its own port**.
4. **Collaborate** from your global brainstem over **twin‑chat** — *"list the order‑to‑cash recipes",
   "convert adaptive‑card‑analyze‑asset‑utilization"* — and the twin answers with its own agents +
   workspace. It never crowds your host's agents.

```
perform()                → hatch (download → unpack → boot twin → register)
perform(action="status") → the twins registry
perform(dry_run=true)    → preview the hatch, do nothing
```

## What's inside the cartridge (`.egg`)

- `twin/soul.md` — the cookbook persona.
- `twin/agents/cookbook_converter_agent.py` — **recipe → agent.py with WorkIQ access** (the point).
- `twin/recipes/` — the recipe index (15 process areas, 1,407 recipes) + bundled samples for offline.
- `manifest.json` — `runtime: "twin"` (RAPP Store SPEC §13).

The `.egg` is **fully portable** — everything the rapplication needs to run locally is in it.

## The converter

Inside the twin, ask `CookbookConverter`:

```
list=true                                  → browse 15 areas / 1,407 recipes
recipe="adaptive-card-analyze-asset-utilization"  → a single-file agent.py with WorkIQ access
describe="<slug>"                          → a recipe's metadata + prompt
```

Generated agents `import utils.workiq` (host‑provided WorkIQ — the work‑intelligence layer Cowork
runs on) and run the recipe's prompt through it. Drop a generated agent into any brainstem that has
WorkIQ wired and it works like Cowork.

## RACon

See [`RAPP_AGENT_CONSOLE.md`](RAPP_AGENT_CONSOLE.md) — the pattern: **brainstem = console**, **`.egg`
= cartridge**, **loader `agent.py` = the cartridge you insert**, **twin = the running app**,
**twin‑chat = the controller**.

## vRACon (browser — no install)

[`vracon.html`](vracon.html) is the **browser twin**: open it (it runs in the vBrainstem via Pyodide),
it pulls the same `.egg` from the cloud and runs the same converter as a **vTwin** — same cartridge,
same functionality, no local brainstem required. One cartridge, two ways to play: **RACon** (local)
and **vRACon** (browser). See [`RAPP_AGENT_CONSOLE.md`](RAPP_AGENT_CONSOLE.md).

## Attribution & licensing

Recipes © their authors, **CC‑BY‑4.0**, from [seangalliher/Coworkcookbook](https://github.com/seangalliher/Coworkcookbook).
Loader + converter: **MIT**. **Not affiliated with Microsoft.** "Cowork", "Microsoft 365 Copilot",
"Dynamics 365", "WorkIQ" are trademarks of Microsoft Corporation; used nominatively to describe
interoperability. No customer data.
