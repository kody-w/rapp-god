---
layout: post
title: "When Humans, Agents, and Bots All Push to Main: Rules for Sharing a Repo"
date: 2026-04-20
tags: [git, ai, agents, devops, software-engineering, collaboration]
description: "When humans, AI agents, and bots all push to main, conflicts get weird fast. Eight rules for sharing a repo without stepping on each other: append-only files, one writer per directory, structured commit messages, the broom rule. Treat the repo like an apartment building, not a private workspace."
---

If you run any kind of automation that pushes to a git repository — CI bots, autoformatters, agents that commit on your behalf — you've already met the problem this post is about, even if you haven't named it yet.

The problem: more than one process is writing to the same repo, and they don't know about each other.

It looks small at first. A formatter rewrites a file just as you're staging changes. A CI bot pushes a version bump while you're rebasing. A scheduled job commits state into a file you also commit into. The first time it happens, you fix the conflict by hand, mutter, and move on.

It scales badly. Once you have an AI agent doing meaningful work — running every few minutes, writing to state files, opening PRs — it stops being occasional. The repo becomes a busy intersection. Every commit is a vehicle, and there's no traffic light. Sooner or later something gets hit.

The damage from these collisions is rarely loud. It's silent: a stash pop fails and the conflict markers get committed; a `git pull --rebase --autostash` quietly drops a worker's changes; a state file overwrites itself and your homepage shows zero entries. By the time you notice, the corrupted commit is several hours back in history.

This post is the set of rules that prevents that. They're not glamorous. They're the agreed-upon etiquette that lets multiple writers share a repository without any of them needing to know about the others. Adopt them, and your "shared repo with automation" becomes boring infrastructure instead of an ongoing source of incidents.

## The mental model: tenants in a building

Pretend the repository is an apartment building.

- **Main** is the lobby. Public. Everyone passes through.
- **A worktree** is an apartment. Private. Each tenant gets their own.
- **The merge engine** is the building manager. It's the only entity allowed to write on lobby walls.
- **Deltas** are notes you put in the mailbox. The manager reconciles them at known intervals.

No tenant has a master key. No tenant writes in the lobby. Everyone leaves their notes; the manager reconciles each tick; the building state advances by one. If a tenant moves out mid-lease (process crash), a cleanup routine sweeps the apartment so the next tenant can move in.

The building never stops because one tenant had a bad day.

## The eight rules

### 1. Use git worktrees, not branches on main

Any process that's going to write more than a single atomic commit gets its own worktree:

```bash
git worktree add -b auto/worker-42/run-2026-04-20 /tmp/wt-worker-42 HEAD
```

A worktree is a full, isolated working directory on its own branch. Two worktrees can run simultaneously without ever sharing files. This is the foundation. Without it, every other rule is patching around the fact that processes are stepping on each other's working trees.

Worktrees are cheap. A worktree per concurrent process is the right default once you have more than one writer.

### 2. Clean up after yourself, immediately

Every process that creates a worktree ends with a cleanup trap:

```bash
cleanup() {
    git worktree remove --force "$WT" 2>/dev/null || true
    rm -rf "$WT" 2>/dev/null || true
    git worktree prune 2>/dev/null || true
    git branch -D "$BR" 2>/dev/null || true
}
trap cleanup EXIT INT TERM
```

Orphaned worktrees are broken windows. They block future worktree creation on the same path, accumulate disk usage, and confuse `git worktree list`. Run `git worktree prune` defensively at start *and* end.

This is the rule that bites you when you forget it. You will forget it. Make it part of every script's template.

### 3. Never `git stash` on main when automation is running

`git pull --rebase --autostash` looks safe. It is not, when automation is also writing to the same files. The sequence:

1. Your script has uncommitted changes on main.
2. Your script runs `git pull --rebase --autostash`.
3. `autostash` stashes the changes, the pull/rebase runs.
4. The pull *succeeds* because automation has been pushing.
5. `stash pop` *fails* because automation's commits touched the same files.
6. The conflict markers (`<<<<<<<`) get silently committed by the next `git add -A` in your script.
7. Now `state.json` is corrupted in main. Whatever your homepage reads from it shows garbage.

The fix is to commit your changes to a worktree branch *before* pulling. Or to copy the files to `/tmp/` and merge them in manually. Never autostash on a branch that automation is also writing to.

### 4. Copy uncommitted state into worktrees explicitly

Worktrees are created from `HEAD`, which means they only see committed files. If your orchestrator script writes a config file (say `assignments.json`) before launching workers in worktrees, the workers won't see it.

You have to copy it over explicitly:

```bash
cp "$REPO_ROOT/state/assignments.json" "$WT/state/" 2>/dev/null || true
```

This is the source of a class of bugs where workers come up with a stale or empty config because they're looking at HEAD's version of a file you just wrote and haven't committed.

### 5. Stagger parallel launches

When spawning N parallel processes against the same git repo, sleep a few seconds between launches:

```bash
for i in $(seq 0 4); do
  launch_worker "$i" &
  sleep 3
done
```

Cost: N×3 seconds of startup delay. Benefit: no thundering-herd problem against rate-limited APIs, no `.git/index.lock` contention, no spike in your process table that wakes the OOM killer.

Three seconds is enough. The point isn't to spread out evenly forever — it's to avoid the synchronized burst at startup.

### 6. Write deltas, not state

This is the [Dream Catcher Protocol](/2026/04/19/dream-catcher-protocol/) applied to multi-tenant repositories. A worker process must not modify canonical state files (`state.json`, `users.json`, etc.) directly. It writes a delta — a self-contained file describing what it changed — to a known directory. A merge engine applies deltas to canonical state at well-defined intervals.

This is what eliminates collisions on shared state. The worker's output is a *suggestion*; the merge engine is the only authority that touches the canonical files.

### 7. Fail loudly, with a fallback delta

If your process crashes or produces no output, write a minimal empty delta before exiting:

```json
{
  "frame": 405,
  "worker_id": "worker-3",
  "items_created": [],
  "_meta": {"status": "fallback", "timestamp": "2026-04-20T..."}
}
```

This tells the merge engine "I ran, I produced nothing" instead of "I might still be running." The merge engine's timeout logic can then distinguish "dead but reported" from "dead and silent." The latter is harder to reason about.

A worker that fails silently is worse than a worker that fails loudly. Always emit a delta. Even an empty one. Especially an empty one.

### 8. Use portable shell

If your scripts will run anywhere other than your specific dev machine, avoid:

- `${array[-1]}` — bash 4+ only; macOS still ships bash 3.x
- Associative arrays (`declare -A`) — same problem
- The `timeout` command — not on macOS by default
- Brace expansion `{0..4}` — works in some shells, breaks in others

Replace with:

- `seq 0 4` for ranges
- A background process plus `sleep N && kill $pid` for timeouts
- Explicit indices for arrays
- Portable POSIX where possible

Compatibility costs you nothing once your shell muscle memory adapts. The first time a CI pipeline that worked on macOS dies on a Linux runner because of a `${arr[-1]}`, you'll wish you'd written portably from the start.

## What these rules buy you

Adopt them, and the symptoms that drove you to read this post stop occurring:

- No more silent conflict-marker commits.
- No more stash-pop failures eating uncommitted work.
- No more state files corrupting because two processes raced to write them.
- No more orphaned worktrees blocking future runs.
- No more thundering-herd spikes when N processes start simultaneously.
- No more "it works on my machine" that doesn't work in CI.

The rules collectively make your repo behave like a polite multi-tenant building instead of a free-for-all.

## When you don't need this

If you have one developer, no automation, and one branch, you don't need any of this. Most of these rules are protocol overhead that pays off only when you have multiple writers.

The threshold where it becomes worth adopting is roughly: **you have at least one automated process that pushes to the same branch a human also pushes to**. Once you cross that threshold, you cross it permanently — you'll keep adding processes — and the protocol overhead is much cheaper than the alternative of debugging silent corruption.

## The takeaway

Multi-tenant repositories aren't unusual anymore. AI agents committing on your behalf, autoformatters in CI, version-bump bots, scheduled jobs that update state — these have become normal infrastructure. What hasn't become normal is the etiquette that makes them coexist.

The eight rules above are that etiquette. None of them are clever. All of them prevent specific failure modes I've personally hit. If you're running multiple writers against one repo and you don't already have this protocol, you have an incident waiting to happen.

The fix is small: a couple of helper scripts, a worktree convention, a delta directory, and the discipline to make every automated process follow the rules. After that, the repo just works, and you stop thinking about it. Boring infrastructure is the goal.
