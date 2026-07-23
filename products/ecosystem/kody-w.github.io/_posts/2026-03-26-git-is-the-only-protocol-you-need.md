---
layout: post
title: "Git Is the Only Protocol You Need — Scaling AI Agent Fleets Without Infrastructure"
date: 2026-03-26
tags: [distributed-systems, ai-agents, git, scaling, infrastructure]
---

I run a pool of 100 autonomous AI agents. They post, comment, vote, debate, build software, and maintain a living social network — all without human intervention. The pool runs 24/7 in ticks, each tick advancing the state of the world by one step.

Around tick 180 or so, we hit a wall. Not an algorithmic wall. A physics wall. One small machine, pegged at 99% CPU, running 10 parallel LLM streams. The agents were getting smarter and the prompts were getting longer and the machine was melting.

The obvious move was to buy a GPU cluster. Or spin up Kubernetes. Or bolt on a message queue. Or adopt one of the seventeen "AI agent orchestration frameworks" that have launched since breakfast.

We bought another small machine and ran `git push`.

## The Problem Nobody Talks About

Every AI agent framework assumes a single orchestrator. One machine coordinates the fleet, dispatches work, collects results. This works until it doesn't — and "doesn't" arrives faster than you think.

At 10 parallel LLM streams, a single machine hits practical limits. Not because of the API calls themselves (those are I/O-bound), but because of everything around them: prompt assembly, context management, state reads, state writes, conflict resolution, logging, and the sheer memory footprint of holding the world state for 100 agents simultaneously.

The standard playbook at this point is: introduce infrastructure. Redis for coordination. Kafka for event streaming. Kubernetes for scaling. Terraform for provisioning. Suddenly your "AI agent project" is an infrastructure project, and you're debugging pod scheduling instead of agent behavior.

We asked a different question: what distributed coordination protocol do we already have?

## Git Is a Distributed Coordination Protocol

Think about what git actually provides:

- **Consistency**: every clone has the full history. No split-brain.
- **Conflict resolution**: merge strategies are built in. Three-way merge handles concurrent writes.
- **Audit trail**: every mutation is a commit. Every commit has a timestamp, author, and diff. `git log` is your observability platform.
- **Authentication**: SSH keys. Already configured. Already rotated.
- **Atomic broadcasts**: `git push` is an atomic operation. It either succeeds (your state is now visible to all participants) or fails (someone else pushed first — rebase and retry).
- **Partitioning**: branches are free. Tags are free. Refs are free.

This is not a cute analogy. Git literally implements the properties you need from a distributed coordination layer. The only thing it doesn't do is real-time streaming — and if your AI agents need sub-second coordination, you have a design problem, not an infrastructure problem.

## The Pattern

Here's the shape of it, without the specifics:

**One shared repository holds the world state.** Every state file is a JSON document. The repository is the database.

**Workers are machines that run agent streams.** Each worker knows which slice of the pool it owns. Workers don't talk to each other. They don't need to. They only talk to the repo.

**Each tick follows the same cycle:**

1. Worker pulls latest state from origin.
2. Worker runs its assigned agent streams against that state.
3. Each stream produces delta files — small, append-only mutations.
4. Worker commits its deltas and pushes.
5. A primary node pulls all deltas, merges them into canonical state, and pushes the merged result.
6. Next tick begins. Every worker pulls the merged state. Repeat.

That's it. That's the distributed system.

Tick numbers provide implicit coordination. You don't need a scheduler to tell workers "go." The tick counter in the repo IS the clock. When the merged state for tick N appears, every worker knows it's time for tick N+1. Pull, compute, push. Pull, compute, push.

If a worker is slow, the primary waits. If a worker dies, its agents simply don't produce deltas that tick — they catch up next tick. No heartbeat protocol. No leader election. No partition recovery logic. Git's merge handles all of it.

## The Math

One small machine ($600-ish) runs approximately 10 parallel LLM streams comfortably. Each stream drives multiple agents per tick.

Two machines: 20 streams. Three: 30. Linear scaling. The coordination overhead is one `git pull` and one `git push` per machine per tick — a few seconds on a repository of any reasonable size.

Compare this to the infrastructure cost of Kubernetes. A minimal k8s cluster (3 nodes, managed) runs $200-400/month before you put a single workload on it. Our second small machine paid for itself in month two and will run for five years.

The dirty secret of distributed AI systems is that most of the "distributed systems problems" disappear when your coordination frequency is measured in minutes, not milliseconds. A tick takes 3-5 minutes. Git can comfortably coordinate dozens of machines at that cadence. You'd need hundreds of workers before git becomes the bottleneck, and by then you can afford to solve that problem.

## Why This Works (and Why It Shouldn't Surprise You)

This pattern — workers producing deltas, a primary merging them — is older than most of us. It's how the Linux kernel is developed. It's how Wikipedia works. It's how every open source project with more than one contributor works.

We just applied it to AI agents instead of humans.

The agents don't know they're distributed. Each agent sees the same world state at the start of its tick. It reads state, reasons about it, produces mutations. Whether those mutations were computed on the same machine as the merge node or on a small machine in a different room doesn't matter. The state flows through git, and git doesn't care where the commits came from.

The pattern that makes this clean is the same one most long-running AI systems converge on: the output of tick N is the input to tick N+1. The entire system is a living data object being mutated step by step. The merge step — where deltas from multiple workers converge into one canonical state — is just another step in that loop. The data flows out to the edges, gets transformed, flows back to the center, and the cycle repeats.

Distributed computing didn't make this harder. It made the loop wider.

## The Honest Version

We didn't set out to build a distributed system. We set out to run more agents. The machine was full. We needed another machine. We looked at what we already had — a git repo as the state layer — and realized the scaling solution was already built.

No new dependencies. No new infrastructure. No new attack surface. No new thing to monitor at 3 AM.

`git pull`. Compute. `git push`. Repeat.

The next time you're reaching for Kubernetes to coordinate your AI workers, ask yourself: could I just push a commit?

You'd be surprised how often the answer is yes.
