---
layout: post
title: "Three bash scripts run the universe"
date: 2026-04-24
tags: [bash, ai, agents, simulation, infrastructure]
description: "An always-on multi-agent simulation that recovers from crashes, restarts dead workers, resolves merge conflicts, and never stops — all from three shell scripts that talk through files. No Kubernetes. No service mesh. No observability stack. The right level of infrastructure for the workload, which turns out to be a lot less than the cloud-native default suggests."
---

There is a kind of system, increasingly common, that runs many processes cooperating on a shared piece of state, and that has to keep running for hours or days without somebody watching it. The cloud-native answer to "how do I run this" is a stack: orchestrator, scheduler, service mesh, observability platform, secrets manager, configuration system, ingress controller. The stack assumes you are running tens of services across tens of nodes for many tenants and you need real isolation guarantees.

Most workloads do not need any of that. They run on one machine. They serve one operator. They mutate a shared state file. They need to come back when something crashes. The cloud-native stack is wildly overspecified for them, and the cost of that overspecification — in setup time, in operational complexity, in things that can themselves go wrong — is so high that most of the workloads are simply not run, because the apparent investment is too large.

The right amount of infrastructure for a one-machine many-process always-on workload turns out to be three shell scripts that talk to each other through files. I have been running such a workload — a multi-agent simulation that mutates a Git repository — on this architecture for months. It survives crashes, restarts dead workers, resolves merge conflicts, never stops. It is one of the parts of my system I am proudest of, because it does a lot of work and is almost embarrassingly simple.

This post is what the architecture looks like, why bash is the right language for it, and what kinds of failures it does and does not handle.

## The three scripts

**The harness.** Launches N parallel worker processes plus M moderator processes. Each worker is a shell loop that, every few seconds: builds a prompt from the current state, sends it to a language model, parses the response, commits the resulting state changes, sleeps for the cycle interval. A worker is a `while true` loop with a model call inside it. That is the whole worker.

**The watchdog.** Runs alongside the harness in a separate process. Every two minutes, it: checks whether the harness is still alive (by reading a PID file the harness writes on startup), restarts it if dead, snapshots a small set of protected files and restores them if they have been overwritten with empty contents, resolves any pending Git merge conflicts on a known recovery strategy, and pushes uncommitted state to the remote.

**The sync.** Called by each worker before it builds its prompt. It fetches the latest state from the remote, merges with the local working tree, handles conflicts. It ensures each worker sees the latest world state before it acts on it.

Combined, these three scripts run a multi-agent simulation on a single laptop. Adding CPU is increasing the number of workers. Adding resilience is letting the watchdog restart crashed workers. Adding correctness is making the sync run before every cycle. There is no fourth component.

## Cooperation through files

None of the three scripts communicate directly. They communicate through a small number of files in known locations:

- A PID file the harness writes on startup. The watchdog reads it to check liveness.
- A stop-flag file. Any script can create it to signal a clean shutdown.
- A push-lock directory. A `mkdir`-based mutex; only one process can hold it at a time.
- A `logs/` directory. Each script appends to its own log. `tail -f` any of them to see what is happening.
- The state directory itself. The canonical simulation state, committed to Git, shared between all workers.

That is the entire interaction surface. No message queue. No inter-process-communication library. No shared memory. Just files. The guarantees come from POSIX file semantics — atomic rename, `mkdir`-as-mutex, append-is-atomic-below-pipe-size — and from Git, which gives merge, conflict detection, and history for free.

This works because file-based coordination scales sufficiently for the workload. Three scripts and a dozen processes do not need a high-throughput message bus. They need a couple of locks and some shared documents. The filesystem is already optimized for that case.

## Why bash

Bash is the right language for the harness and watchdog and sync because they do exactly what bash is good at: launch processes, redirect their output, wait on background jobs, handle signals.

The harness needs to launch N background processes, let them run independently, write their PIDs somewhere, route their stdout/stderr to log files, and handle a Ctrl-C that stops everyone cleanly. Each of these is a one-liner in bash:

- Launch in background: `cmd &`
- Capture PID: `pid=$!`
- Redirect output: `cmd > logfile 2>&1`
- Wait on background jobs: `wait`
- Handle signals: `trap 'kill 0' EXIT`

In Python, each of these is a wrapper around `subprocess.Popen`, signal handlers, careful management of file descriptors, and a thread or asyncio loop to wait on multiple processes. Bash hides all of that behind syntax that has been stable since the 1970s.

The parts of the system that are *not* a good fit for bash — parsing JSON, calling HTTPS APIs, computing similarity scores, running machine learning models — live in Python or Go scripts that bash invokes as subprocesses. Each language does what it is good at. Bash is the conductor. The performers speak whichever language the part calls for.

This is the same lesson Unix taught fifty years ago and most modern stacks have forgotten. Shell is the right glue. It is bad at structured data, bad at long-lived computation, bad at concurrency primitives. It is excellent at "launch this thing, watch it, log it, kill it if it goes wrong." Use it for that and only that, call out to other languages for the rest, and the result is short and obvious.

## What it handles automatically

I have watched this setup run through a dozen different failure modes without any human intervention. The ones that come up regularly:

**A worker crashes mid-cycle.** The watchdog notices the harness has fewer children than expected within two minutes and restarts the harness. The crashed worker's last incomplete commit is dropped on the next sync.

**A worker's model call hangs.** Workers have a timeout on every external call. The worker's loop times out, logs the failure, and moves to the next cycle.

**A merge conflict during push.** The push helper rebases against the latest remote and retries. If the rebase fails too, the conflict is logged for human attention; the worker continues without pushing this cycle.

**A protected file gets clobbered by a worker.** The watchdog snapshots a known-good copy of critical files on every cycle. If the next snapshot shows the file is empty or massively shorter than expected, it restores from the previous snapshot.

**Disk fills up with old logs.** The harness rotates log files older than a threshold. Old commits are not pruned because their value is in the history.

**The laptop loses network briefly.** Workers' external calls time out, the watchdog keeps polling, the harness keeps the workers alive. When the network comes back the workers resume.

None of these required dedicated code. They fall out of the architecture: a harness that launches things, a watchdog that watches them, a sync that handles Git. The architecture *expects* failures because failures are normal, and it has dumb-but-effective recoveries for the common ones.

## What it does not handle

I should be honest about the gaps.

**Corrupted state files.** If a worker commits malformed JSON, the simulation will keep running but other workers will crash on the next read. There is some read-back validation at write time, but not all formats are fully validated. The fix is tighter validation at the boundary, not more infrastructure.

**A model output that produces infinite text.** Workers pipe model output to a parser. A sufficiently malformed output can make the parser hang. The fix is an explicit timeout at the parser level, in addition to the existing timeout at the model call level.

**Clock drift.** If the laptop clock is wrong, the timestamps used in the merge engine are wrong, and writes can be deduplicated incorrectly. The fix is `chrony` or equivalent, run once at setup. Not a runtime concern but worth knowing.

**Multi-machine scale.** This architecture runs on one machine. It does not split workers across machines. If you need that, you need real orchestration (Kubernetes, Nomad). That is the day to introduce the heavier stack.

These are known gaps. I have built around them but have not eliminated them. The right discipline is to fix them at the input boundary, not by adding more components.

## When the simple stack stops being enough

I would reach for Kubernetes or a similar orchestrator the day the workload needed:

- To run across multiple machines.
- To survive a machine going down with no human attention.
- To serve more than one tenant with isolation guarantees.
- To horizontally scale beyond what a single machine provides.

Until any of those is true, three shell scripts is the correct architecture and adding orchestration would be a tax on every operation. The watchdog is one hundred lines of bash. Kubernetes is a system more complex than the workload it is hosting. The cost-benefit only flips at scale.

The general rule I have arrived at: *match the infrastructure to the workload's actual demands, not to what infrastructure looks impressive*. Most workloads are smaller than the default infrastructure suggests, and the cost of overshooting is real. A three-script harness for an always-on multi-process workload is the right amount, until it isn't.

## The takeaway

If your system can be run by a harness, a watchdog, and a sync, run it that way. Bash is the correct language. Files are the correct inter-process channel. Git is the correct state store, if your state can fit in Git. The complexity ceiling on this architecture is roughly twenty parallel processes and a few days of continuous runtime. That is enough for an enormous amount of useful work.

When you hit the ceiling, you will know. You will see specific patterns of failure that the architecture cannot recover from cleanly, and the fixes will start to require components the simple stack does not have. That is when you replace it with something heavier. Until then, three scripts.

The reason this is worth writing down is that the cloud-native default has trained a generation of engineers to reach for orchestration on day one. The result is workloads that never ship, because the infrastructure investment exceeded the workload's value before the workload was ever finished. The bash-and-files architecture is a reminder that you can ship the workload first and add infrastructure as needed, instead of the other way around.

Three scripts. One operator. Many cooperating processes. A repository for state. A watchdog that puts everything back when something falls over. That is the entire stack. It is enough.
