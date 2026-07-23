---
layout: post
title: "Delta journals beat state mutations"
date: 2025-10-22
tags: [architecture, event-sourcing, software-design, ai-systems, distributed-systems]
description: "Why every long-running simulation, agent system, or fleet of writers should journal what changed instead of mutating canonical state. Time-travel debugging, replay, and how this scales to many parallel writers."
---

The naive way to run a simulation:

```python
state = load("state.json")
for frame in range(500):
    tick(state)
    save("state.json", state)
```

Works fine for a single sim on one machine. Falls apart the moment you want to:
- Rewind to frame 312 and watch what happened
- Run two sims in parallel without overwriting each other
- Diff what changed between frame N and frame N+1
- Distribute work across machines

The fix is older than databases: **don't mutate. Append.**

## The pattern

```python
class Engine:
    def __init__(self, name, seed, state, tick):
        self.state = state
        self.deltas = []  # journal

    def run(self, n_frames):
        for _ in range(n_frames):
            delta = self.tick(self, self.state, self.frame)
            self.deltas.append({
                "frame": self.frame,
                "ts": iso_now(),
                **delta,
            })
            self.frame += 1
```

The `tick` function returns a delta — what changed this frame. The engine appends it to a journal. The canonical state still gets mutated for convenience, but the journal is the source of truth.

If you lose the state, you can rebuild it from the deltas. If you want to replay frame 312, you reset state to frame 311's snapshot and apply delta 312. If two sims run in parallel, you merge their delta streams instead of fighting over the state file.

## What this unlocks

**Evolution simulations**: hundreds of generations where each frame's delta records births, deaths, mutations, speciation events. The full lineage tree (a cladogram) is computed from the full delta stream, not from the final state.

**Ecosystem simulations**: every migration event is a delta entry with origin, destination, identifier, and cost. The migration log on the viewer is just `deltas.filter(d => d.type === "migration")`.

**Fleet coordination**: when many parallel writers operate on the same repository, they each emit delta files. A merge engine reconciles them at boundaries. No two writers ever modify the same file simultaneously.

## Append-only as a coordination protocol

Once you commit to deltas, parallel writers become much easier to reason about. Each writer produces deltas keyed by a tuple like `(frame_or_round, timestamp, writer_id)`. Deltas merge deterministically because they are append-only — there is nothing to overwrite.

This is the scaling law for any system where outputs are expensive and non-deterministic. Without journaling, parallel writers overwrite each other's work and valuable output is silently lost. With journaling, parallel writes become *additive* — more workers means more throughput, not more collisions.

## The general principle

If your system has a "state" file that is being mutated, you are one race condition away from data loss. Add a journal. Make the state computable from the journal. The journal is cheap — it is just append-only records. The peace of mind is permanent.

Event sourcing is not new. CQRS is not new. But for AI systems specifically — where outputs are expensive, non-deterministic, and easy to lose — the journal is not a nice-to-have. It is the difference between a system that survives five hundred runs and one that survives five.
