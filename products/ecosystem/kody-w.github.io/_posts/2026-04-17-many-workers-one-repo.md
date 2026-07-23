---
layout: post
title: "How to Run Many AI Workers Against One Repository Without Them Eating Each Other"
date: 2026-04-17
tags: [ai, agents, git, multi-tenancy, software-engineering, concurrency]
description: "Five AI workers, one repo, no merge conflicts. The Dream Catcher pattern: workers write deltas to a known directory; a single reaper applies them serially. Append-only, conflict-free, works for humans too. The same shape as event sourcing, immutable infrastructure, log-structured storage."
---

If you run more than one AI agent against the same shared state, sooner or later you will lose data.

The first time it happens, you'll think it was a one-off. A merge conflict. A lost commit. You'll restore from backup, fix the immediate cause, ship a patch, and tell yourself it won't happen again.

It will happen again. The data loss is structural, not incidental. The number of collisions in a multi-writer system grows with the *square* of the number of writers — two writers have one collision pair, ten writers have 45, a hundred writers have 4,950. Add capacity, and the system gets worse, not better. Most teams hit this wall when they scale from "a couple of background agents" to "an actual fleet."

I hit it the first time when 10 parallel workers writing to the same file silently committed conflict markers to the main branch. About 130 entries in the affected file went to `{}`. The site looked like the whole platform had died. We rolled back ~90 minutes of work and I went and figured out what had to change.

The protocol that came out of that incident has worked at increasing scale ever since. Workers no longer collide. The throughput scales linearly with how many workers I add. The system survives crashes, partial writes, and clock skew. I'll explain it here in the four rules that make it work, and why each one is doing a specific job.

## The core insight: workers produce deltas, not state

The single decision that makes everything else work is: **workers don't write to shared state files.**

Instead, each worker produces a *delta* — a self-contained file describing what changed during its run. The delta has a unique filename. Workers drop their deltas into a known directory. They never modify the canonical files (`agents.json`, `stats.json`, whatever your shared state happens to be).

A delta looks like this:

```json
{
  "frame": 530,
  "stream_id": "worker-3",
  "utc": "2026-04-19T14:30:22Z",
  "items_created": [{"id": 6201, "title": "..."}],
  "comments_added": [{"target": 6195, "body": "..."}],
  "counter_increments": {"total_items": 1, "total_comments": 1}
}
```

The shared state is a *projection* of the deltas, computed at well-defined merge points. The deltas are the source of truth. The state files are a derived view.

This is the same shift event-sourcing teams have been making for two decades. It works for AI workers for the same reason it works for human-written services: the log is the database, and state is just a projection.

## Rule 1: Workers produce deltas, never state

This is what makes the rest possible. If worker A reads `state.json`, increments a counter, and writes back, worker B's increment between A's read and write is lost. With deltas, A writes "I added +1 to counter X" and B writes "I added +1 to counter X" and the merge engine sees both. Counter goes to +2. There is nothing to overwrite because nobody overwrites anything.

Workers can be on different machines, in different processes, behind different proxies. They don't need to know about each other. They don't need a coordinator. They just produce their deltas and drop them in the directory.

## Rule 2: Deltas are keyed by `(logical_clock, wall_clock)`

Every delta has two timestamps: a *logical* one (a frame number, a tick, a sequence; whatever the application's notion of time is) and a *wall-clock* one (UTC). Together they form a globally unique composite key.

You could use a UUID. UUIDs are also unique. But UUIDs are opaque — they don't tell you anything about *when* the delta was generated or *what* it belongs to. With a `(frame, utc)` key:

- Sorting by logical time gives you the simulation/process timeline.
- Sorting by wall-clock time gives you what actually happened in real-world order.
- Detecting out-of-order arrivals is trivial.
- Replaying any range of history is just filtering by frame number.
- Comparing two snapshots is comparing two ranges of frames.

**Uniqueness with context is most of what you actually want from an event log.** Pure uniqueness leaves you doing forensics with a magnifying glass.

## Rule 3: Merge is additive, never destructive

When the merge engine collects deltas and applies them to canonical state, it follows three rules:

- **Items append.** Deduplicate by natural key (post ID, content hash, whatever).
- **Counters sum.** All increments combine.
- **Field updates use last-write-wins by wall-clock**, *but only for the same field on the same entity*. Different fields, different entities, always coexist.

The merge engine never throws information away. If two workers' deltas disagree on the same field, both are recorded; the merge engine logs the conflict and applies one according to the rule. The other is preserved in a `conflicts.log` so a higher-level policy step can re-evaluate.

This sounds expensive. The alternative — silently picking one and discarding the other — is much more expensive, because the cost is invisible until you're trying to debug something six weeks later.

## Rule 4: Frame boundaries are the only merge points

The merge happens at well-defined intervals. Until then, deltas accumulate. There is no continuous merging. The system is batch-oriented at the merge level even though individual workers are continuous.

This gives you a clean tick of the system clock. Every state snapshot at frame N is well-defined as "all deltas for frames 1 through N, applied additively." You can save snapshots, diff them, replay history, roll back. None of this is possible with continuous merging — the state would be in flux at every read.

## What a frame looks like end-to-end

```
Pre-frame:
  All workers pull main.
  Each worker creates its own isolated working directory.

Frame execution:
  Workers run in parallel.
  Each writes one delta:
    deltas/frame-530-worker-0.json
    deltas/frame-530-worker-1.json
    ...
  Workers never touch the canonical state files.

Post-frame:
  A single merge process runs:
    Read all deltas for this frame.
    Apply additive merge to canonical state.
    Commit + push the merged state.
    Move consumed deltas to an archive folder.
  Worker working directories cleaned up.
```

The merge is **single-threaded**. Only one process mutates the canonical files, and only at frame boundaries. All parallelism is confined to the delta-producing phase.

## Three guarantees you get for free

1. **No collisions.** Workers write to unique paths. They physically cannot stomp each other.
2. **Idempotency.** Running the merge engine twice with the same deltas produces the same state. Re-running a crashed worker produces no duplicates.
3. **Crash tolerance.** A truncated delta fails JSON parse and gets skipped. No half-written entries land in the canonical files.

Bonus: **a complete audit trail.** The deltas are preserved. You can replay any frame, see exactly what each worker produced, diff them, measure their divergence.

## Git is enough

For most teams reading this, the question of *transport* between workers is the next thing to answer. Don't overbuild it. Git as the message bus works fine until you need sub-second latency:

- **Deltas live in different files** with unique names. Git never sees them as conflicting.
- **The merge engine's commit** is one atomic update to canonical state plus deletion of consumed deltas. Atomic at the git level.
- **Frame boundaries align with merge commits.** History reads as `[deltas... deltas... merge frame N | deltas... merge frame N+1]`. Trivially auditable in any git tool.

You don't need a database. You don't need a message queue. You don't need a broker. Git's transport plus a directory of files plus a single-threaded merge process is enough for many many writers.

If you outgrow git's latency, the same pattern works on Postgres LISTEN/NOTIFY, on Redis streams, on Kafka. The shape of the protocol is identical; you're just changing the transport layer.

## The hard cases

**Two workers want to set the same field on the same entity to different values.** Last-write-wins by wall-clock; the loser logs to `conflicts.log` for human or policy review. Real-world frequency: rare.

**A worker crashes mid-frame.** Always emit an empty delta with a `status: fallback` marker. The merge engine then knows the worker tried but had nothing to contribute. Without this, you can't distinguish "crashed" from "had nothing to do."

**The frame boundary fires before all workers have written.** Use a timeout: workers that haven't written by T+30s get dropped. Don't use a barrier that waits for all workers — one slow worker stalls the whole system. The cost: occasionally a slow worker's frame-N delta arrives during frame N+1 and gets applied late. Usually fine.

## What this scales to

This is the part that surprised me. Most multi-writer systems get *worse* as you add writers, because each new writer adds a quadratic number of collision pairs. With this protocol, **each additional writer adds throughput without adding collisions.** More workers = more deltas = more parallel append operations into different files. The merge cost grows linearly with the number of deltas, not quadratically with the number of workers.

I went from 5 workers to 50 with no architectural changes. Throughput scaled linearly. The merge engine got marginally slower per frame (more deltas to read) and that was it.

## What it doesn't give you

To be fair to the alternatives:

- **No real-time consistency.** State at frame N is consistent only after the merge for frame N completes. Workers reading mid-frame see stale state. If you need sub-second consistency, this isn't the right protocol.
- **No linearizability.** Two writes don't have a defined order until the merge engine assigns one.
- **No free conflict resolution.** When two workers want incompatible things, the protocol surfaces the conflict but doesn't resolve it. You still need policy.

If your workload requires linearizability or real-time consistency, use a database that gives you those guarantees and accept the per-write overhead.

## Steal this

If you're building any multi-writer system and you don't already have a battle-tested database that fits:

1. Every writer produces a **delta file** per unit of work, keyed by `(logical_time, wall_clock)`.
2. Writers never modify canonical state directly. Only deltas.
3. A **merge engine** reads all deltas for a window and applies additive merge.
4. Retain deltas as audit log. Snapshot state at every merge point.
5. Use git as transport if sub-second latency isn't required.

You'll spend the first week getting the deduplication logic right per entity type. After that, you'll have a system that scales linearly with writers, survives arbitrary crashes, and has time travel built in for free.

It's not magic. It's the insight that **the log is the database, and the state is a projection** — applied consistently to every write path in the system.

That's the whole protocol. Four rules, one core insight. Build it once, and you stop losing data when you scale your AI workers.
