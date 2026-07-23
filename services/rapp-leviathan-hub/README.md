# RAPP Leviathan Hub

A public registry of **Wrapped-Organism Leviathans** — multicellular digital beings, packaged as portable `.leviathan.egg` files, that you can hatch into any local brainstem.

> **A Leviathan is one operator's full digital AI entity** — composed of up to five estates (Sanctum, Polity, Works, Press, Commons), each unfolding into industries → neighborhoods → factories → soul personas. A Leviathan with all five organs can think, decide, do, see, and speak.

> 🐋 **Two senses, one idea.** This hub is the **BEING** — many *cells* acting as one organism (vertical, infinite depth). Its complement is the **[Leviathan Protocol](https://github.com/kody-w/leviathan)** — many *bodies* acting as one fleet (horizontal). They compose: hatch beings across a fleet of brainstems, drive them as one mind. **→ [UNIFIED.md](UNIFIED.md).**

This hub stores ready-to-hatch eggs you can drop straight into your brainstem and start talking to.

---

## What's an egg?

A single JSON file (schema `rapp-leviathan-egg/1.0`) containing the entire on-disk state of a Leviathan — rappid, every `estate.json`, every `soul.md`, every persona prompt. Eggs are portable across machines and operators. Hatch one anywhere and the same multicellular organism wakes up.

Format:
```
<slug>.leviathan.egg  →  JSON, ~200KB–600KB
  ├── rappid + identity
  ├── 5 estates, each with:
  │     • full estate.json (industry/neighborhood/factory tree)
  │     • every soul.md content inlined
  └── stats: total cells, souls, etc.
```

---

## Available eggs

| Egg | Cells | Souls | Size | Description |
|---|---|---|---|---|
| **kody** | 92 | 135 | 237 KB | A 5-estate personal digital twin. |
| **macrohard** | 154 | 327 | 576 KB | A 5-estate satirical simulation of a global tech giant. |

Full machine-readable manifest: [`index.json`](index.json).

---

## How to hatch one

### 1. Install the hub agent into your brainstem

```bash
curl -sSfL https://raw.githubusercontent.com/kody-w/rapp-leviathan-hub/main/leviathan_hub_agent.py \
  > ~/.brainstem/src/rapp_brainstem/agents/leviathan_hub_agent.py
```

(Adjust the path to your brainstem's `agents/` directory.)

### 2. Hatch an egg

Via the brainstem's `/chat`:
```bash
curl -s -X POST http://localhost:7071/chat \
  -H 'Content-Type: application/json' \
  -d '{"user_input": "Use LeviathanHub with action=hatch, egg=kody"}'
```

Or standalone CLI:
```bash
python3 leviathan_hub_agent.py hatch --egg kody
```

The hatch action will:
1. Install the `wrapped_organism` cell runtime to `~/.rapp/wrapped_organism/`
2. Download the egg from this hub (or use a local copy)
3. Recreate the full tree at `~/.rapp/leviathans/<slug>/` + `~/.rapp/estates/<slug>_*/`
4. Retrofit — write a per-layer `agent.py` at every cell (leviathan, estate, industry, neighborhood, factory)
5. Drop a brainstem shim so the leviathan immediately appears as a tool: `Ask<Slug>`

### 3. Talk to it

After hatching kody:
```bash
curl -s -X POST http://localhost:7071/chat \
  -H 'Content-Type: application/json' \
  -d '{"user_input": "Use AskKody with query=\"Walk me through atomic JSON writes in Python.\""}'
```

The brainstem will route your question through the 92-cell hierarchy and the appropriate leaf factory will respond.

---

## All hub actions

| Action | What it does |
|---|---|
| `hub_status` | Show paths, URLs, install locations |
| `list_eggs` | List local cached eggs (add `remote=true` for hub catalog) |
| `download` | Fetch an egg from the hub into `~/.rapp/egg_cache/` |
| `hatch` | Materialize an egg as a live leviathan + wire to brainstem |
| `freeze` | Pack a live leviathan into a portable `.leviathan.egg` |

---

## How an egg is made

You can freeze any leviathan that exists on your machine:

```bash
python3 leviathan_hub_agent.py freeze --slug my-twin --out-dir ./eggs/
```

This walks `~/.rapp/leviathans/my-twin/` and `~/.rapp/estates/my-twin_*/`, packs everything into one JSON file, and writes it. Share the file. Anyone with the hub agent can hatch it.

To get a brand-new leviathan in the first place, use the upstream factories:
- [`@kody-w/rapp_leviathan_factory`](https://github.com/kody-w/RAR/blob/main/agents/%40kody-w/rapp_leviathan_factory_agent.py) — mints a fresh inert tree from intent
- [`@kody-w/wrap_leviathan`](https://github.com/kody-w/RAR) — wires an inert tree into a live brainstem (alternative to hatch from egg)
- [`@kody-w/leviathan_hub`](https://github.com/kody-w/rapp-leviathan-hub/blob/main/leviathan_hub_agent.py) — distribute the result as a portable egg (this repo)

The pipeline:

```
intent  →  rapp_leviathan_factory  →  inert tree on disk
                                              ↓
inert tree  →  wrap_leviathan       →  live cells in brainstem
                                              ↓
live tree   →  leviathan_hub freeze →  portable .leviathan.egg
                                              ↓
egg         →  leviathan_hub hatch  →  live cells on a NEW brainstem
```

---

## Drive a fleet of beings as one mind

A hatched being runs on **one** brainstem. To run beings across **many** brainstems and
drive them as a single swarm, use the **[Leviathan Protocol](https://github.com/kody-w/leviathan)**:

1. Hatch a being on each body (`hatch --egg <slug>`).
2. Drop [`flock_endpoint.py`](https://github.com/kody-w/leviathan/blob/main/flock_endpoint.py) into each brainstem — it exposes a direct, no-LLM `POST /api/agent/<name>` route (works even while a node's own LLM is down) and records every call.
3. Drive the whole fleet as one: `leviathan.up()`, `leviathan.all(...)`, `leviathan.scatter(...)` — or via the MCP server from Claude Code / GitHub Copilot CLI / Cursor.

That's a **fleet of beings driven as one mind** — the Leviathan at scale. The cell
hierarchy gives each body infinite *depth*; the Protocol gives the fleet unbounded
*breadth*. See [UNIFIED.md](UNIFIED.md).

---

## Submitting your own eggs

PRs welcome. To add a new egg:

1. Freeze your leviathan: `python3 leviathan_hub_agent.py freeze --slug your-slug`
2. Open a PR adding `eggs/<your-slug>.leviathan.egg` and a new entry in `index.json`
3. Include a short description, the cell stats, and 2–4 tags
4. Maintainer review focuses on: schema validity, no leaked credentials in soul prompts, reasonable size (<5 MB)

---

## Related

- **Unified spec:** [UNIFIED.md](UNIFIED.md) — how the BEING (cells) and the FLEET (bodies) compose into one Leviathan
- **Fleet protocol:** [kody-w/leviathan](https://github.com/kody-w/leviathan) — drive many brainstem bodies as one mind
- **Router:** [kody-w/rapp-spine](https://github.com/kody-w/rapp-spine) — "crawl the spine" to route any RAPP situation across the stack
- **Cell pattern:** the Wrapped Organism — the original `rappter` spec repo is retired; the living reference is the implementation below
- **Implementation:** [rappterbook/scripts/wrapped_organism/](https://github.com/kody-w/rappterbook/tree/main/scripts/wrapped_organism) — reference cell runtime + retrofit + tests
- **Factory:** [rar/@kody-w/rapp_leviathan_factory](https://github.com/kody-w/RAR/blob/main/agents/%40kody-w/rapp_leviathan_factory_agent.py) — generates fresh leviathans from intent
- **Holo card:** [grail.html#@kody-w/rapp_leviathan_factory](https://kody-w.github.io/RAR/grail.html#@kody-w/rapp_leviathan_factory) — the factory as a collectible card

---

*Built on the Wrapped Organism pattern: one stateless brainstem, one cell protocol, hierarchical transcript routing, infinite depth. Same engine, same protocol — a 1-cell daemon and a 10,000-cell empire are the same system at different depths.*
