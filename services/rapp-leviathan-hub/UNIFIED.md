# The Leviathan, Unified

Two repos carried two senses of one word. They are not rivals — they are the same
idea, **many parts acting as one**, at two scales that stack into a single column.

|  | The **BEING** | The **FLEET** |
|---|---|---|
| repo | **rapp-leviathan-hub** (this) | **[kody-w/leviathan](https://github.com/kody-w/leviathan)** |
| spec | `rapp-leviathan-egg/1.0` + the Wrapped Organism pattern | `leviathan` SPEC v1.0 |
| many-as-one | many **CELLS** → one organism (vertical, infinite depth) | many **BODIES** → one fleet (horizontal) |
| the question | *what is one operator's whole digital self?* | *how does one mind drive many bodies?* |
| the unit | a 5-estate being, hatched from an `.egg` | a no-LLM body, driven via `POST /api/agent/<name>` |

## The column — bottom to top

```
   cells → estates → a BEING (runs on one brainstem)        ← Wrapped Organism (this hub)
                          │
   beings on many brainstems → a FLEET (one mind drives all) ← Leviathan Protocol (kody-w/leviathan)
```

A Leviathan is **the whole column**: cells compose into a being; a being runs on a
body; bodies compose into a fleet; one mind drives the fleet. The same prime
directive holds at every depth — *many-as-one, one wire, no new endpoints.* A 1-cell
daemon, a 10,000-cell empire, and a 50-node planetary swarm are the same system at
different scales.

## Which do I want?

- **One rich digital self** (many cells, infinite depth) → hatch a **BEING** from this hub.
- **Drive many brainstems as one** (many bodies, no throttle) → the **[Leviathan Protocol](https://github.com/kody-w/leviathan)**.
- **A planetary swarm of digital selves driven as one mind** → hatch beings across a
  fleet of brainstems, then drive the fleet with the Protocol. **That is a Leviathan at scale.**

## How they compose, concretely

1. **Hatch** a being onto each body (this hub: `hatch --egg <slug>`).
2. **Join** each body to the fleet — drop [`flock_endpoint.py`](https://github.com/kody-w/leviathan/blob/main/flock_endpoint.py) into its brainstem (no engine edit, works while the node's own LLM is down).
3. **Drive** the fleet of beings as one mind — `leviathan.up()`, `leviathan.all(...)`, `leviathan.scatter(...)`, or via the MCP server from Claude Code / Copilot CLI / Cursor.

The hub distributes the beings; the Protocol drives a fleet of them. Route between
the two senses with [`rapp-spine`](https://github.com/kody-w/rapp-spine) (the `leviathan` layer names exactly this distinction).

---

*Cells all the way down; bodies all the way out. The Leviathan is both.*
