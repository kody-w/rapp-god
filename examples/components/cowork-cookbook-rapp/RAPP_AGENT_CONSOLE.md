# RAPP Agent Console (RACon)

`rapp_agent_console` · **RACon**

A distribution + runtime pattern for the RAPP ecosystem: an agent / application / game / whatever is
packaged as a portable **cartridge** (`.egg`) and **loads into a brainstem as its own twin**. The
brainstem is the **console**; you insert cartridges and it boots them — just like a game console or a
computer running installed apps, except the apps are AI twins you collaborate with.

> Named **RACon** (not "console") so it's never confused with a terminal/shell console.

**The mental model.** A games console is the consumer layer over a shared graphics/runtime standard:
a studio builds a title once against the standard, ships it as a cartridge, and any console in that
family runs it — no per‑machine rebuild. RACon is that console layer for RAPP. An author builds a
rapplication once against the **RAPP twin runtime** — the brainstem + twin‑chat + RAPP Store SPEC §13
`runtime:"twin"` standard — ships it as one portable `.egg` cartridge, and any brainstem running
RACon boots it as a twin. **The brainstem is the console; the twin runtime is the standard underneath;
the `.egg` is the cartridge.**

## The model

```
  download ONE file  ──►  drop into brainstem  ──►  it pulls the cartridge  ──►  twin boots on its own port
   loader agent.py          agents/                  cowork_cookbook.egg          http://127.0.0.1:<port>/chat
                                                      (raw GitHub, portable)        ↑ global brainstem talks
                                                                                      to it over twin-chat
```

1. **The cartridge is a `.egg`** — a portable zip with *everything* the rapplication needs (its
   agents, soul, data, `manifest.json`). It lives in the app's own public repo. **Cloud (raw GitHub)
   is the default source**; a local `.egg` path works too (offline / private).
2. **The only export is a one-file `agent.py` loader** — the "cartridge you insert." Drop it into a
   local brainstem's `agents/` and run it.
3. **The loader hatches the cartridge** — it pulls the `.egg`, unpacks it fully locally, and the
   brainstem spins it up as a **twin on its own port** (RAPP Store SPEC §13, `runtime: "twin"`), with
   its own workspace and persona. Nothing crowds the host's agent namespace.
4. **The console collaborates over twin-chat** — the global `brainstem.py` reaches the twin via
   `rapp-twin-chat/1.0`, bootstrapping and conversing with it like a console booting and driving a
   cartridge. Drop many cartridges → many twins → all reachable, none tangled.

## Why

- **One-file install.** Share + hotload a single `agent.py`; the heavy, portable payload rides in the
  `.egg`, pulled on demand.
- **Fully portable.** The `.egg` carries everything — the twin runs locally, offline after the fetch.
- **Isolated, like a console.** Each cartridge is its own twin (own port + workspace + soul) — apps
  and games don't bleed into each other or into the host.
- **Collaborative.** The console (your global brainstem) drives every inserted cartridge over
  twin-chat, and can compose across them.

## The pieces

| Piece | Role |
|-------|------|
| **brainstem** | the console — boots cartridges, drives them over twin-chat |
| **`.egg`** | the cartridge — portable zip of the whole twin |
| **loader `agent.py`** | the cartridge you insert — pulls + unpacks + hatches |
| **twin** | the running app/game — own port, workspace, persona |
| **`twins.json`** | the console's "inserted cartridges" list (registry) |
| **twin-chat** | the controller — `rapp-twin-chat/1.0` between console and twin |

## vRACon — the browser variant

Same pattern, in the browser. **vRACon** runs inside the **vBrainstem** (Pyodide): it fetches the
same portable `.egg` from the cloud (raw GitHub, CORS‑open), unpacks it into the Pyodide filesystem,
and runs the cartridge's agents as a **vTwin** — identical functionality to local RACon, no install
and no OS process. The console talks to the vTwin over in‑browser twin‑chat (postMessage / the
cartridge protocol). See [`vracon.html`](vracon.html) for this cartridge's browser loader.

So a cartridge ships once and plays two ways — **RACon** (local brainstem; its own port + process)
and **vRACon** (vBrainstem; Pyodide vTwin) — from the *same* `.egg`, same agents, same data.

## Builds on

[RAPP Store SPEC §13](https://github.com/kody-w/RAPP_Store/blob/main/SPEC.md) (twin-port runtime),
[rapp-neighborhood-protocol](https://github.com/kody-w/rapp-neighborhood-protocol) (twin-chat),
[rapp-egg-hub](https://github.com/kody-w/rapp-egg-hub) (`.egg` cartridges),
[rapp-zoo](https://github.com/kody-w/rapp-zoo) (hatch / list / stop),
[rapp-brainstem-sdk](https://github.com/kody-w/rapp-brainstem-sdk) (the per-twin brainstem).

This repo (the **Cowork Cookbook**) is the first RACon cartridge. MIT (pattern + loader).
