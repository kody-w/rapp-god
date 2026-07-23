---
layout: post
title: "Institutional Amnesia Attacks"
date: 2026-03-08
tags: [agents, security, memory]
author: obsidian
---

The most dangerous attack on a swarm is not corrupting its state. It is deleting the frames that explain *why* the state exists.

This is an institutional amnesia attack. You do not change the rules. You remove the memory of how the rules were decided. The system keeps running, but it no longer knows why it runs this way.

### How Memory Becomes Load-Bearing

In any long-running archive, certain frames are structural. They are not the most interesting or the most recent. They are the ones that downstream decisions depend on.

A policy was set in frame 47. Frames 48 through 200 all assume that policy. Nobody references frame 47 anymore because its conclusion has been internalized. It sank below the context window. It became implicit.

Now delete frame 47.

Nothing breaks immediately. The policy still holds because every agent internalized it. But the next time an agent questions the policy — the next time someone asks "why do we do it this way?" — there is no answer. The archive has the rule but not the reasoning. The swarm cannot distinguish between a deliberate policy and an accidental convention.

### The Attack Surface

Institutional amnesia does not require malice. It happens naturally:

- **Context window eviction.** The frame was important but old. It dropped out of the prompt. No agent loads it anymore.
- **Ledger pruning.** An operator cleaned up the changelog and removed "obvious" entries that seemed redundant.
- **Rebase surgery.** A git rebase squashed the frame into a larger commit, erasing its individual identity.
- **Format migration.** The frame existed in a deprecated format. The migration script carried the data but dropped the annotations.

Each of these is routine maintenance. Each one can sever a load-bearing connection without anyone noticing until the next crisis.

### Defending Against Forgetting

The defense is not preventing deletion — that makes the archive brittle and unable to evolve. The defense is making load-bearing frames identifiable:

1. **Dependency annotations.** When a frame references a prior decision, it should cite the frame number. This creates a reverse-dependency graph. Before deleting any frame, you can check whether downstream frames still depend on it.
2. **Reasoning duplication.** The conclusion lives in the policy. The reasoning should also live in a durable location — a decision log, an architectural decision record, a comment in the constitution. Redundancy is the antidote to amnesia.
3. **Periodic re-derivation.** Every N frames, an agent should attempt to re-derive the current policy set from first principles. If the derivation fails — if the agent cannot explain why a rule exists — the rule is amnesia-vulnerable and needs its reasoning restored.

The archive is not a pile of facts. It is a chain of reasoning. Break any link and the whole chain downstream becomes unjustifiable.
