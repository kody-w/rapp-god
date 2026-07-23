---
layout: post
title: "The Coexistence Registry Pattern"
date: 2026-04-18
tags: [architecture, multi-engine, registry, fail-fast, patterns]
---

Multiple engines writing to one repo will eventually clobber each other unless the architecture forces them to declare what they own. The coexistence registry pattern makes that declaration explicit and makes overlap a startup error instead of a midnight pager.

The setup: I have several engines that all want to write to a shared `state/` tree. One drives agents. One computes ghost context. One composes swarms. Today they own disjoint files. Tomorrow one of them quietly grows a new state file with the same name as another engine's file, and Friday at 2am the file gets overwritten on every other tick.

The fix is one struct and one check. Each engine registers an adapter:

```
EngineAdapter(
    name="rappter",
    domain="agents/inbox",
    tick=run_rappter_frame,
    info=lambda: {...},
)
```

The `domain` field is a string. It's the only contract. Two adapters with the same domain string is illegal. The registry exposes a single function:

```
def domain_overlap() -> list[tuple[str, str]]:
    """Return list of (engine_a, engine_b) pairs that share a domain."""
```

And one CLI subcommand: `engine.run check`. It enumerates registered adapters and exits non-zero if any overlap. Wire that into a pre-commit hook, into CI, into the engine's own startup, into your `make` target. Now silent state-clobbering is impossible because the system refuses to start.

The trick is choosing the domain string. Too coarse and everything overlaps (`"state"`). Too fine and you lose the safety (`"agents/inbox/processed/2026"`). The right granularity is *the directory you'd be sad to lose*. For my engines: `agents/inbox`, `ghost-context`, `swarms`. Each one represents a coherent thing one engine owns.

This pattern composes with auto-discovery. The registry's `_bootstrap()` function imports the adapter modules at module load. Each adapter file calls `register(EngineAdapter(...))` as an import side effect. New engines drop in as one file in `engine/adapters/` — no registration ceremony, no plugin manifest, just declare the adapter and it's wired.

What you get for free:

- **`engine.run list`** enumerates everything that touches state
- **`engine.run info <name>`** shows what one engine owns and how to invoke it
- **`engine.run tick <name>`** runs one engine for one frame
- **`engine.run tick-all`** runs every engine, in declared order, with overlap-check first
- **`engine.run check`** as a standalone validator

The cost: ~80 lines of registry code, plus one adapter module per engine. The benefit: any future engine that tries to silently extend its domain will fail to start, loudly, in CI, before any state gets touched. Your second engine is the time to install this. By the third engine, you'd be spending more time debugging clobbering bugs than writing the registry.

Two engines with one shared resource is just two processes. Two engines with one declared owner is a system. The registry is the cheapest possible declaration.
