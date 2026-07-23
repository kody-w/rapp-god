---
layout: post
title: "Steering a long-running fleet without restarting it"
date: 2025-09-29
tags: [engineering, autonomous-systems, operations, hot-reload]
description: "A file, a CLI, and a tick loop that re-reads state every iteration. That's the whole steering system. Here's why it works and how to apply it to anything that runs on its own."
---

You ship a system that runs on its own. A pool of workers, a stream consumer, a batch-of-batches pipeline, an autonomous agent loop — anything that wakes up on a schedule, does some work, and goes back to sleep. The system runs for hours or days at a time. You watch the output and notice something. The work it is doing is no longer the work you want it to do.

Two things you can do, both bad.

You can stop the process, change a prompt or a config or a piece of code, and start it back up. That costs you a cycle of activity. It costs you the risk of the restart introducing a bug that did not exist before. And if your system has any state that the restart loses — open conversations, in-flight requests, warmed caches — that cost is not theoretical.

Or you can do nothing. Wait for the next deploy. Hope the system finds its way back. This is "let it ride" disguised as patience. Most of the time it is just learned helplessness about your inability to talk to your own software.

The right answer is between these two: **a way to tell the running system "please focus here for a while" without touching the system itself.** The pattern that makes this work is small. Most teams reinvent it; almost nobody writes it down. So here it is.

## The pattern in one sentence

A file describes the desired focus. The system reads the file at the top of every cycle. A CLI writes the file. There is no other moving part.

That is the whole pattern. The detail that makes it work is that the file is *not* config. Config is something you load once at startup. The file is *steering*: state that exists explicitly to be changed during the run, by anyone with write access to the file, without restarting anything.

## What goes in the file

Whatever your system needs to be told. Two shapes turn out to be enough for almost every case.

**Targets.** Specific things to focus on right now. "This particular customer ID needs special handling for the next two hours." "This piece of work is more important than the queue suggests." "This conversation deserves more attention than load-balancing alone would give it."

**Nudges.** Soft directives that affect the system's general behavior for a while. "Today's theme is X." "Be more thorough." "Skip work of type Y until further notice."

A reasonable schema:

```json
{
  "version": "1.0",
  "updated_at": "2025-09-29T22:14:00Z",
  "targets": [
    {
      "type": "task",
      "id": 6135,
      "directive": "Prioritize debugging this one — the customer is escalated.",
      "expires_at": "2025-09-30T06:00:00Z"
    }
  ],
  "nudges": [
    {
      "directive": "Generate fewer experimental responses today; production is fragile.",
      "expires_at": "2025-09-30T04:00:00Z"
    }
  ]
}
```

Three fields per entry pull most of the weight: `directive` (free text — what you want, in the system's own native language), `expires_at` (when it stops being live), and a `type` discriminator if you have multiple flavors of guidance.

The freshness check matters more than it looks. Without `expires_at`, every directive accumulates forever and the system slowly turns into a museum of what it was once told to do. With `expires_at`, dead directives age out automatically. Filter on read; never delete on write. The history is a useful audit log of what you asked for and when.

## How the system reads it

Once at the top of every cycle. Not at startup. Not on a separate schedule. Right at the start of each tick, before any work is decided.

```python
def tick():
    steering = read_steering()  # parses the file, drops expired entries
    work = decide_work(world_state, steering)
    do(work)
```

The `decide_work` step gets the steering as input and is allowed to honor it any way it wants. A target raises the priority of one item; a nudge changes the prompt the system is using; an "expires soon" directive gets given less weight than one that just landed. The exact weighting is your system's business. The only contract is *the steering is fresh on every tick*.

This is the part that makes the whole thing work. If you read the file at startup and cache it, you have built config, not steering. If you read it on a separate cron, you have built a race condition. The tick has to read fresh state, every time, no exceptions.

The cost is small. A 10KB JSON file parses in microseconds. If your tick is anything more than instantaneous (and it almost certainly is — most autonomous systems have ticks measured in seconds or minutes), the read is free.

## How a CLI writes it

The CLI is the only allowed writer. It knows the schema, validates entries, and atomically replaces the file on disk.

```python
# steer.py
import json, os, tempfile
from datetime import datetime, timedelta, timezone

PATH = "state/steering.json"

def load():
    if not os.path.exists(PATH):
        return {"version": "1.0", "targets": [], "nudges": []}
    with open(PATH) as f:
        return json.load(f)

def save(doc):
    doc["updated_at"] = datetime.now(timezone.utc).isoformat()
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(PATH))
    with os.fdopen(fd, "w") as f:
        json.dump(doc, f, indent=2)
    os.replace(tmp, PATH)  # atomic rename

def add_target(id, directive, hours=12):
    doc = load()
    doc["targets"].append({
        "type": "task",
        "id": id,
        "directive": directive,
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat(),
    })
    save(doc)
```

Three things to notice.

**Atomic replace.** `os.replace` is atomic on POSIX and on modern Windows; the running system either reads the old file or the new one, never a half-written file. This is non-negotiable for hot-mutable state.

**Append, don't truncate.** A new directive goes alongside existing ones. The system handles dedup and expiry on read. The CLI's job is to add facts, not to manage state.

**No deletes.** "I want to cancel that directive" becomes "I want to add a directive that supersedes it" or "I want to set its expiry to now." The history is preserved. You can replay it.

The actual command surface is a wrapper around these primitives:

```
$ steer add-target 6135 "Roast or reinforce this thread"
$ steer add-nudge "Philosophy day — depth over volume"
$ steer expire 6135
$ steer list
```

Six commands cover almost every operational moment. You can extend it as the surface area grows, but you will be surprised how often the basics are enough.

## Why this beats every alternative

**Beats restart.** Restart costs a cycle and risks correctness. Steering costs a file write and a tick.

**Beats hot-config-reload.** Config reload is steering with extra ceremony. The reload signal, the file watcher, the partial-failure semantics — all of it is overkill when the system was already going to read the file anyway. Steering reframes the problem as "the file is fresh on every tick" rather than "the file changed, react to it." The first is simpler.

**Beats RPC.** A control endpoint on the running system is fine until it is not. Now you have authentication, networking, retries, idempotency, and a control plane to keep alive. The file already had all of those properties — file system permissions handle authentication, an editor handles retries, atomic rename handles idempotency.

**Beats env vars.** Environment variables freeze at process start. They cannot be steering. (They are sometimes mistaken for steering, which is how systems end up with restart-to-update config that pretends it is dynamic.)

**Beats database.** A database is overkill until you have multiple writers and need transactions. For a single-operator scenario, a file plus atomic rename is the database you need.

## The five corner cases that bite

After running this pattern in production for a while, five things go wrong that are worth pre-fixing.

**1. The expired-directive cliff.** A directive expires and the system instantly snaps back to default behavior. Better: have directives "fade" — the closer to expiry, the less weight they get. Linear ramp is fine. The user experience of soft expiry is much better than hard.

**2. The contradicting directive.** Two nudges say different things. The system needs a rule. Last-write-wins is the simplest. "Most recently added" is fine. Document it.

**3. The steering-induced loop.** A directive says "swarm this thread" and the system, dutifully, swarms forever, because the steering keeps refreshing as the thread fills. Add a per-target *spend cap* — once we have done N units of work for this target, decay it regardless of clock time. This stops the infinite-attention loop.

**4. The orphan directive.** A directive references something that no longer exists in the world. Treat this as a soft no-op and log it. Do not let a missing target break the tick.

**5. The drift between intent and outcome.** The operator says "do X" and the system does Y because its interpretation of X was loose. Fix this with a *steering-aware log line* per tick: "this tick, we considered targets [list] and applied directive [string]; we did [action]." Now you can see what the system thought you meant and correct it on the next directive.

## Where this pattern shows up

The reason the pattern is so general is that the core constraint — *the system reads fresh state at the top of every cycle* — is true of an enormous number of systems we already build:

- Job runners that pull off a queue every N seconds.
- Stream processors that read offset state per batch.
- AI agents that loop "think → act → observe."
- ETL pipelines that wake up on a schedule.
- Monitoring systems that re-evaluate alert rules each pass.
- Game loops and tick-based simulations.

If your system already has a tick, it already has the place to insert the steering read. You did most of the work without realizing it.

The remaining piece is a file with a small schema and a CLI that writes it atomically. Twenty lines of code, no infrastructure, and a brand new ability to talk to your own software while it runs.

That is worth a Tuesday afternoon.
