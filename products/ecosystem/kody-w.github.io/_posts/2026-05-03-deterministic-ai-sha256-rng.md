---
layout: post
title: "Deterministic AI: SHA-256 as a Random Number Generator"
date: 2026-05-03
tags: [ai-systems, determinism, reproducibility, simulation]
description: "Why every random choice in my simulations is hashed from the seed, the tick, and a label — instead of from `random.random()`. Same inputs → same 500-generation result, on any machine, forever. The pattern that turns 'look what happened' into 'you can verify what happened.'"
---

`random.random()` has a problem. It's stateful. Two scripts that both call `random.shuffle()` on the same list in different orders will get different results. A simulation that depends on `random` is hostage to its own call sequence.

For a 500-generation evolution simulation where every individual's mate, every species' fitness, every migration event needs to be reproducible — that's unacceptable.

So I replaced `random` with SHA-256.

## The pattern

```python
def tick_seed(self, label: str) -> int:
    payload = f"{self.name}:{self.seed}:{self.tick}:{label}".encode()
    return int(hashlib.sha256(payload).hexdigest()[:16], 16)

def coin(self, label: str) -> float:
    return self.tick_seed(label) / 2**64

def pick(self, label: str, items: list) -> Any:
    return items[self.tick_seed(label) % len(items)]
```

Every random choice is now a pure function of `(engine_name, base_seed, current_tick, label)`. No state. No call sequence dependency. Two scripts can ask "give me a random mate for individual #847 on tick 312" in any order and get the same answer.

## What this unlocks

**Reproducibility.** I ran an evolution sim with seed 42 last night. I ran it again this morning. The exact same species won both times with peak population 396. Exactly. To the individual.

**Debugging.** When a species went extinct unexpectedly, I didn't have to re-run the whole sim. I jumped to tick 472, reseeded the engine, and watched the death happen one step at a time.

**Sharing.** I can tell you "run `python3 sim.py --seed 42`" and you'll get my exact result tree. Not a similar tree. The same tree.

**Trust.** Scientific claims about emergent behavior are only as strong as their reproducibility. SHA-256 RNG turns "look what happened" into "you can verify what happened."

## The cost

Slightly slower than `random.random()`. SHA-256 is ~50ns per call vs ~5ns for `random`. Across a 500-tick evolution sim with ~50 random calls per tick per individual and ~500 individuals, that's about 6 seconds of overhead.

Worth it. Reproducibility is a feature you only know you needed when you don't have it.

## The implication

Most "AI" systems are non-deterministic by design. LLMs sample with temperature. Agents pick from tools probabilistically. This is fine for chat. It's a disaster for simulation.

If you're building anything that resembles a simulated world — economic models, evolution, multi-agent emergent behavior, training environments — push the determinism down to the RNG layer. Hash your randomness from the seed and the tick. Make every "random" choice a coordinate in a deterministic space.

Then the sim becomes a function. Inputs go in. The same outputs come out. Every time. Forever.
