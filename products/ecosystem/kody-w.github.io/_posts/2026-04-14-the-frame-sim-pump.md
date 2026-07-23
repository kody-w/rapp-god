---
layout: post
title: "The frame sim pump — seven primitives for running any AI simulation"
date: 2025-10-23
tags: [simulation, software-architecture, ai-systems, agent-based-modeling, design-patterns]
description: "Not an agent framework. Not a message queue. A universal simulation loop — seven primitives that make any AI simulation breathe."
---

I had been running a small AI simulation on a single laptop for a long time before I realized I had been staring at the same pattern for months without giving it a name.

The frame loop. The stream assignment. The delta merge. The next tick reading the last tick's output. I had been calling pieces of it different things — the context pattern, the worker assignment trick, the merge architecture. But those are components. The whole thing is one pattern. A pump that takes a universe at time T and produces the universe at time T+1. I call it the frame sim pump.

It is not a social network thing. Not a chatbot thing. Not an agent framework. It is a simulation engine pattern that works for anything where entities act on state and the state advances forward in time.

## Seven primitives

The entire pattern reduces to seven operations.

**STATE** — a serializable snapshot of the universe at time T. If something is not in the state, it does not exist in the simulation.

**PARTITION** — split entities into groups that can be processed independently. Which entities need to see each other's output within this tick? Agents mid-conversation go together. Agents on different topics go apart.

**PROCESS** — each group passes through an AI model in parallel. The model reads the full state plus its group's entities and produces a delta — a structured diff of what changed. Processors are isolated and generative. Two identical ticks can produce different output. That is what makes the simulation alive.

**MERGE** — combine all group deltas back into one state. Append-only data concatenates. Counters sum. The strongest strategy: make conflicts structurally impossible. If groups never share entities, there is nothing to conflict on.

**ADVANCE** — the merged state becomes the next tick's input. Without it, you have batch processing. With it, you have a simulation. No single tick is interesting. Interesting behavior emerges from hundreds of ticks, each building on the last.

**TOCK** — lightweight processing between ticks. The tick is the heartbeat. The tock is the physics that does not pause between heartbeats. Threshold checks, signal propagation, decay functions — all running continuously on what the last tick deposited. No LLM calls. A simulation with only ticks is a flip book. A simulation with tick-tock is a universe.

**ENRICHMENT** — past frames keep absorbing new context. A frame processed months ago can still receive new observations today. The original data is immutable. New context is appended alongside it. The constraint is causal consistency: you can enrich the past but you cannot contradict downstream history. The earliest frames are paradoxically the highest-fidelity frames in the system — they have been understood the longest.

That is the whole thing. Everything else is implementation.

## The shape

```
     STATE(T)
        |
    PARTITION
   / |  |  | \
  G  G  G  G  G     <- independent groups, processed in parallel
   \ |  |  | /
     MERGE
        |
    STATE(T+1)
        |
      TOCK          <- physics between heartbeats
        |
   ENRICHMENT       <- past frames absorb new context
        |
    PARTITION
   / |  |  | \
        ...
```

Scale by adding processors. The bottleneck is never the merge or the partition. It is the AI model's throughput.

## The frame object drives everything

There is no orchestration logic in the transport layer. The frame object — the full state at time T — is the entire program. The LLM reads the frame and decides everything. What to post. Where to comment. Who to reply to. Whether to start a debate or go quiet.

There is no `random.choice(channels)`. No `if agent.archetype == "philosopher": post_in("philosophy")`. The prompt is the program. The LLM is the runtime. Code is transport, not decision.

This also means the simulation is self-steering. The output of tick T includes metadata that shapes tick T+1: which agents to activate, how many groups to create, what regions to focus on. The simulation drives its own evolution. No external controller needed.

## What it looks like in practice

A reference implementation has run this pattern for hundreds of ticks across many days on a single laptop. The numbers, as a sanity check on the scale this can reach:

- More than one hundred agents
- Tens of thousands of posts and comments accumulated as state
- Up to fifteen parallel streams per tick
- Zero servers, zero databases, zero external dependencies
- State: flat JSON files in a Git repository
- Infrastructure: one laptop, the standard library of one programming language, a shell

Each tick, the pump partitions agents into streams using a diversity-weighted scoring scheme — agents from different archetypes get mixed to maximize emergence, while agents that historically interact get grouped to preserve conversation threads. Each stream is a separate LLM instance reading the same frame object, mutating a different partition, producing an append-only delta keyed by `(tick, timestamp)`. The composite key makes collision impossible by construction. Adding streams increases throughput, not collision rate.

## The tock makes it breathe

Between ticks — the long pauses while the heavy AI processing is not running — the tock layer keeps the universe alive. Sandboxed mini-interpreters read the current state and produce observations. Trending scores decay continuously. Threshold monitors detect when an event crosses a boundary or a metric hits a milestone.

None of this requires an LLM call. The tock runs on what is already in the state. When the next tick fires, agents see what the physics did between heartbeats. They react to a living universe, not a stale photograph.

The tick says: given this universe, what do the creatures do? The tock says: given what the creatures did, what does the universe do?

## The growing crystal

Retroactive enrichment is the property I did not expect. The earliest frames, recorded on day one, were thin — agents acting tentatively, social graph empty. Those frames today have been enriched with patterns detected across thousands of subsequent frames. Behavior that seemed random now glows with significance because we can see what it set in motion.

The enrichment is append-only. The original data is immutable. New context layers alongside it like minerals seeping through geological strata. The rock does not change. Our ability to read it does.

## Not just for social networks

The pump does not care about the state schema. Replace agent profiles with colonist records, order books, species populations, character sheets. Replace posts with resource allocations, trade orders, mutations, dialogue. The seven primitives stay the same.

A Mars colony sim partitions by shared resources. A market sim partitions by competing order books. An ecosystem sim partitions by food web edges. A narrative sim partitions by scene membership. The partition question is always the same: which entities need to see each other's output within this tick?

## What I got wrong

The pump does not build creatures. It builds the universe creatures emerge from. I spent months trying to engineer interesting agent behavior — better prompts, better personality templates, more detailed backstories. The behavior that actually emerged came from the loop itself. Put agents through hundreds of iterations of the same pump and they develop culture, inside jokes, recurring debates, and content norms that nobody designed.

The pump is not the creature. It is the spacetime the creature lives in. Tick is time advancing. Tock is the laws still operating between moments. Enrichment is the past still forming beneath the present. What crawls out of it is not up to you.

Seven primitives. The rest is what emerges.
