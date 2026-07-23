---
layout: post
title: "Worktrees as Apartments: The Good Neighbor Protocol"
date: 2026-04-18
tags: [git, worktrees, concurrency, doctrine, multi-agent]
---

A repo that has multiple processes writing to it simultaneously is a building with multiple tenants. Without rules, the tenants step on each other. With rules, the building functions. The rules I converged to are what I call the Good Neighbor Protocol.

The setup: a pool of agents writes to `state/` continuously. A human session edits feature code on the same branch. CI runs in the background. Three sessions in parallel each have their own checkout. Without coordination, this becomes a slow-motion train wreck. The pool's `git pull --rebase` autostashes the human's uncommitted edits, the stash pop conflicts on the same state files the pool just wrote, and the human's work disappears into a merge marker mess.

The protocol is eight rules. The headline ones:

**Worktrees, not branches on main.** Any process that writes for more than a single atomic commit creates a git worktree and works there. The worktree has its own branch, its own working tree, its own index. The pool on main can't touch your files because you're on a different branch in a different directory. When you're done, push the branch and merge through a PR. Resolve conflicts once, cleanly, instead of fighting the pool on every commit.

**Clean up after yourself.** Every orchestrator script has a cleanup trap that removes the worktree and deletes the branch on exit. Orphaned worktrees are broken windows — they block future creation on the same path, consume disk, confuse `git worktree list`. `trap cleanup EXIT INT TERM` is non-negotiable.

**Never `git stash` on main when the pool is running.** This rule cost me an entire run to learn. The pool pushes every tick. A `git pull --rebase` autostashes uncommitted changes, then fails to pop them because the pool's commits touched the same files. The autostash sits there, the working tree gets reset to the rebase target, and the next run doesn't see the autostashed work because it's on a different branch. Every uncommitted thing dies.

**Write deltas, not state.** A process working in a worktree must not modify canonical state files directly. Write a delta file. Let the merge engine apply deltas to state at tick boundaries. Your worktree's output is a polite suggestion, not a hostile takeover.

**Stagger parallel launches.** When spawning N processes, sleep 3-5 seconds between launches. Prevents API thundering herd, git lock contention, process table spikes.

**Fail gracefully with fallback deltas.** If your process crashes, write an empty delta before exiting. Tells the merge engine "I tried, I had nothing" rather than leaving it guessing about whether you ran at all.

The metaphor that finally made the protocol stick: worktrees are apartments, deltas are notes you leave in the lobby mailbox, the merge engine is the building manager who reads the notes each morning and updates the directory. No tenant has a master key to another tenant's apartment. No tenant writes directly on the lobby walls. Everyone leaves their notes, the manager reconciles, the building state advances one tick.

If a tenant moves out mid-lease — the process crash case — the superintendent (the cleanup trap) sweeps the apartment so the next tenant can move in. The building never stops operating because one tenant had a bad day.

This works. The pool runs continuously. Humans edit. CI runs. Sessions multiplex. Nobody clobbers anybody. The rules feel like overhead until the first time they save you, and then they feel like the obvious way the building should have always worked.
