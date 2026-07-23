---
layout: post
title: "Git is your database — when the access pattern fits"
date: 2025-10-07
tags: [architecture, git, databases, json, content-management]
description: "I have a system in production with thousands of records, dozens of writers, and full audit history. The database is a git repository. Here is the access pattern that makes this possible, what makes it work, and where it actually breaks."
---

The first time someone tells you their database is a git repository full of JSON files, you assume they have not yet hit the wall they are about to hit. PostgreSQL exists for a reason. Indexes exist for a reason. Concurrency control exists for a reason. Surely this person is going to discover all of those reasons soon.

Sometimes they are. But not always. There is a class of systems where git, used as the actual primary data store, is not just adequate — it is *better* than the database you would otherwise reach for. The systems where this works share a specific access pattern. Most teams misidentify whether their system is one of them, in both directions: some force a database where files would have been simpler, others try files for a workload that genuinely needs a database. This post is about the access pattern, why git fits it, and where the bound is.

I have run a system with this architecture in production for months. Tens of thousands of records. Dozens of authors writing concurrently. Full audit history. No PostgreSQL. No Redis. No Dynamo. No SQLite. The database is a git repository. The query layer is a public-static-file URL. The write layer is whatever inbound channel the system already had. It is not a toy. It works.

Here is what actually makes it work, and what would break it.

## The architecture, plainly

The data lives as flat JSON files inside a git repository, in a directory like `state/`. Each file is one logical "table" — `users.json`, `topics.json`, `events.json`. Inside each file, records are key-indexed by ID. Reading a record is "fetch the file, look up the ID."

The read path is one URL — your repo's public-static-file URL. Any HTTP client, anywhere, can fetch any state file by name. The CDN-on-by-default behavior of public-static-file hosting handles caching for free.

The write path is whatever inbound channel the system already supports. In my case, that is structured submissions to an issue tracker — a script reads new issues, validates the action, writes a delta file into an `inbox/` directory, and a second script merges deltas into the canonical state files and commits the result. Every write is a commit. Every commit is signed by whoever made it. The commit history *is* the audit log.

That is the whole stack. There is no running database process. There is no connection pool. There is no failover. The "database" is whatever git already gave you, and you push to wherever git already pushes.

## The access pattern that fits

The architecture only works for a specific kind of workload. The shorthand is **read-mostly, append-mostly, audit-required, low-write-rate.** Each adjective is doing real work.

**Read-mostly.** Reads outnumber writes by a wide margin. A typical web app fits this — most page loads are reads, write-shaped requests are a small fraction of traffic. If your traffic is balanced or write-heavy, the architecture starts to strain.

**Append-mostly.** New records arrive far more often than old records change. Edits exist but are not the dominant write pattern. If your workload constantly mutates existing records in place, you are going to fight the commit graph forever.

**Audit-required.** You actually want a permanent record of *who changed what when*. If you do not, the file-and-git architecture is over-investing in audit you will not use; pick a database with simpler tooling. If you do, git's audit log is among the strongest you can get for free.

**Low-write-rate.** "Low" depends on your tolerance for commit-merge work. Hundreds of writes per minute is fine. Thousands of writes per minute starts to require careful concurrency engineering. Tens of thousands per minute does not work — you will run out of git's design envelope long before you run out of CPU.

When all four adjectives apply, git-as-database is genuinely better than the database you would otherwise reach for. When any one of them does not apply, you should pick something else.

## Why this is *better* than a database for the right workload

Three benefits, in order of how much they matter.

**Git is the audit layer everyone wishes their database had.** Every write is a commit. The commit message describes what happened. The author of the commit identifies who. The diff shows exactly what changed. Time travel is `git checkout`. Provenance is `git blame`. None of this required code on your part. None of this can be silently disabled. None of this can be lost in a database migration.

In a traditional database, audit is a feature you bolt on — an audit table, a trigger, an event sourcing layer, a CDC pipeline. Each adds complexity. Each can be misconfigured. None of them are quite as good as the audit log git was already keeping.

**The read layer is global, fast, and free.** Public-static-file hosts serve flat JSON to anyone who asks. The first reader pays the latency of the origin fetch; everyone else pays the cache hit. You did not write any caching code. You did not stand up any CDN. You did not configure any rate limits. The read layer scales with the host, not with your traffic.

If your workload is heavy on reads — and most workloads are — that property alone changes the cost structure of the system. You go from "we need to size a cluster for read traffic" to "the cluster is the host's, and it is included in the price."

**The write path inherits a peer-reviewed concurrency model — git's merge.** Two writers committing to the same file at the same time produce a merge. Most of the time, git resolves the merge automatically (different keys in the JSON). When git cannot resolve, you get an explicit conflict you must handle. This is *better than the silent last-write-wins* that most ad-hoc concurrency layers default to. It forces you to face the question of "what should happen when two people change the same field at the same time" rather than letting one of them quietly win.

The downside is that you have to handle the conflict, but you would have to handle it anyway in any correct system. Git surfaces the moment.

## Why this *fails* outside the right workload

Three failure modes, in order of how badly they bite.

**High write rate breaks the merge model.** Git's merge is fast for small numbers of concurrent writes. When the same file is being modified by hundreds of concurrent writers, the merge cost dominates. Each writer has to fetch, modify, and push, retrying on conflict. With low contention, retries are rare and cheap. With high contention, the system spends more time retrying than working. There is no "lock the row" in this architecture; you have optimistic concurrency only.

The mitigation is to *partition* the writes — split a single hot file into many smaller files, each touched by a subset of writers. The cost is a loss of locality (related data now lives in many files). The benefit is that contention drops linearly with the partition factor.

**Mutable fields produce noisy commit history.** If you have records that change constantly — a counter, a "last seen at" timestamp, a heartbeat — every change is a commit, and every commit is in the history forever. Within weeks the history is dominated by housekeeping commits and the audit log loses signal.

The mitigation is to *exile mutable fields*. Counters and heartbeats go to a different file, ideally one that gets snapshotted and rotated — not into a per-write commit. The canonical state files hold only data that changes meaningfully.

**Large state files become a load problem on every read.** If `topics.json` is 50 MB, every reader pays 50 MB of bandwidth on every read. The static-file CDN helps, but the origin still has to serve cold-cache fetches. The reader still has to parse 50 MB to look up one topic.

The mitigation is to *split files at a size threshold*. When a single file approaches a few megabytes, break it into shards keyed by something natural — first letter of an ID, hash bucket, time window. Each shard is a fetch. Readers fetch only what they need.

A reasonable rule: files smaller than a megabyte are fine; between one and ten megabytes, watch them; above ten megabytes, split.

## What the access pattern looks like in practice

Concrete shape of a system that successfully runs on this architecture.

**State files live in `state/`.** One file per logical entity. Files are flat JSON. Files are pretty-printed for git diff readability. Top-level shape is `{"id": {...record}}` so lookups are O(1) within the file.

**Writes never go directly to canonical state.** A writer submits a delta — a small JSON file describing what they want to change — to an `inbox/` directory. A periodic process reads the inbox, validates each delta, applies it to the canonical state, and commits the result. This serializes writes, prevents direct commits to state files, and gives you a place to validate before mutation.

**Helper for atomic writes.** A small `state_io` module wraps every write in temp-file-plus-fsync-plus-rename-plus-readback. Without this, a crash mid-write leaves a corrupt state file. With it, every write is durable or did not happen.

```python
def save_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    with open(path) as f:
        if json.load(f) != data:
            raise StateCorruptionError(path)
```

This pattern is non-negotiable. If you want git-as-database to be production-grade, every write goes through atomic-write helpers. Skipping this is the single most common way teams torch their state.

**A retry-with-rebase commit helper.** Multiple processes may push at once. The commit helper does `git fetch && git rebase && git push`, retrying on rejection up to a small bound. Without this, parallel pushes collide and the system stalls. With it, the system tolerates concurrent commits transparently.

**Stable URLs for everything.** Every state file is reachable at one URL forever. Frontend code, API consumers, federation peers — they all hit the same URL. Versioning happens by changing the file's *shape* in a backward-compatible way, not by changing the URL.

## The practical envelope

A reasonable estimate, based on running this architecture in production: it works comfortably up to:

- Hundreds of records per file before splitting.
- Tens of thousands of records total across the system.
- Single-digit writes per second sustained, with bursts higher.
- Hundreds of concurrent readers (limited only by the static-file host).
- Months of audit history with strong forensic value.

Above any of those, you are not in the access-pattern sweet spot anymore. You may still be okay, but you are spending more engineering effort on workarounds than you would spend on a properly-chosen database.

## When to use this and when not to

Use it when:

- The data is mostly public-readable.
- The audit log is genuinely valuable to you.
- Writes are submissions, not constant mutations.
- You want to leave the platform someday and take all your data with you in `git clone`.
- The deployment model — push to a repo to update the database — *helps* rather than hinders your team.

Do not use it when:

- The data must be private and authenticated per request.
- Writes are constant in-place updates of existing records.
- You need transactional consistency across multiple state files.
- Real-time freshness matters more than audit history.
- Your write rate exceeds tens per second sustained.

Most systems are not the sweet spot for this architecture. Some are, and for those it is much better than the alternative because the audit log is real, the read path is free, and the operational surface is "you already had git."

## The point, plainly

Git-as-database is not a hack. For workloads that are read-mostly, append-mostly, audit-required, and low-write-rate, it is a strong primary store. The audit log alone is worth more than most teams realize. The read layer is global and free. The write path is sane if you discipline it — atomic writes, retry-with-rebase commits, file splits when state grows.

Pick the architecture for the access pattern, not for the meme. Most teams who try this and fail were running the wrong workload on it. Most teams who succeed had identified the access pattern explicitly first and chose this on purpose. Be the second kind.
