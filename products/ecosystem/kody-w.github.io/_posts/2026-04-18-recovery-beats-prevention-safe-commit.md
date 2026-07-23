---
layout: post
title: "Recovery Beats Prevention: The safe_commit Pattern"
date: 2026-04-18
tags: [git, recovery, patterns, shared-state, robustness]
---

You can spend infinite time trying to prevent conflicts in shared-state systems, and you'll still hit conflicts. There are too many ways for two writers to step on each other. Locks fail. Sequencers go down. Coordinators have bugs.

We learned to stop trying to prevent and start trying to *recover*. The pattern is in `safe_commit.sh`, a 50-line bash script that handles every git push conflict in a system where dozens of writers (agents, humans, scheduled jobs) push to `main` continuously.

This post documents the pattern.

## The recipe

```
1. Try to commit and push normally.
2. If push fails:
   a. Save the computed files you wanted to push to a temp dir.
   b. git reset --hard origin/main  ← throw away your branch state.
   c. Restore the saved files on top of the now-up-to-date branch.
   d. Recommit and try again.
3. If still failing, retry up to 5 times with exponential backoff.
4. If still failing after 5 tries, exit and let a human look.
```

That's the entire algorithm. No locks. No sequencers. No coordination. Just optimistic push, and when it fails: throw away your local state, take fresh state from upstream, reapply your changes on top.

## Why this works when locks don't

Locks try to prevent conflicts by serializing writers. They fail in five ways:

1. **The lock holder dies** — your work is blocked until the lock times out
2. **The lock service goes down** — nobody can write
3. **Two services think they hold the lock** — split brain
4. **The lock is held longer than expected** — everyone else times out
5. **You forgot to release the lock** — same as #1

Optimistic recovery sidesteps all five. Writers don't coordinate. They try, and if their try races with someone else's, they discard their own work, refetch upstream, and reapply. The "lock" is git's commit hash — if upstream's HEAD changed, your push fails, and you know to recover.

## The trick: separating *what you computed* from *the branch state*

The reason this is safe is a discipline: **the files you want to push are computed, not authored.** A worker process computes a delta file. A merge step writes new state files. These are *outputs* — they exist as a consequence of work the worker did, not as a manually-authored sequence of commits.

Because the files are outputs, you can save them aside, throw away the branch they were on, restore them on top of a different branch, and recommit — and the result is correct. You'd never do this with hand-authored code (you'd lose intent), but for computed outputs it's not just safe, it's the right move. Your computation produced a delta. The delta belongs on top of whatever's at the head right now. You don't care which specific commit was at HEAD when you started computing.

## The pattern in actual bash

```bash
#!/usr/bin/env bash
set -euo pipefail

FILES_TO_PUSH=("$@")
MAX_RETRIES=5

attempt=0
while (( attempt < MAX_RETRIES )); do
  attempt=$((attempt + 1))

  git add "${FILES_TO_PUSH[@]}"
  git diff --cached --quiet && { echo "Nothing to commit."; exit 0; }
  git commit -m "auto: state update (attempt $attempt)"

  if git push origin main 2>/dev/null; then
    echo "Pushed on attempt $attempt."; exit 0
  fi

  echo "Push failed. Recovering..."
  TMPDIR=$(mktemp -d)
  for f in "${FILES_TO_PUSH[@]}"; do
    [[ -f "$f" ]] && cp --parents "$f" "$TMPDIR/"
  done

  git fetch origin main --quiet
  git reset --hard origin/main

  for f in "${FILES_TO_PUSH[@]}"; do
    [[ -f "$TMPDIR/$f" ]] && cp "$TMPDIR/$f" "$f"
  done
  rm -rf "$TMPDIR"

  sleep $((2 ** attempt))
done

echo "Push failed after $MAX_RETRIES attempts."; exit 1
```

This is the entire concurrency control system for dozens of writers in this repo. It has been live for months. It has prevented exactly zero outages because there are none — the writers don't conflict in a way that requires human intervention; they just retry and succeed.

## When recovery is the right strategy

Recovery beats prevention when:

1. **Conflicts are rare.** If 99% of pushes succeed first try, retrying the 1% is cheap. If 30% conflict, you need a different approach.

2. **The work is repeatable.** Recomputing the delta from current state must be safe. If your computation has side effects (sent an email, charged a card, posted to Twitter), you can't just "redo" — you need idempotency.

3. **Conflicts are detectable, not silent.** Git push fails loudly when HEAD changed. Database UPSERT can silently overwrite. Recovery only works if you *know* you conflicted.

4. **The writes are idempotent at the file level.** Restoring `state/agents.json` on top of a fresh checkout overwrites whatever was there. This is fine if your file represents *the current state*, but wrong if it represents *a delta to apply*. Use the right shape — full state files for recovery, delta files for accumulation.

5. **You can tolerate some serialization.** Recovery serializes per writer (you wait, refetch, retry). If you have hundreds of writers all racing, the retry storm gets bad. We have ~30, and it works fine.

## When prevention is right

If conflicts are common (>30%), you need actual coordination — a lock service, a queue, a single-writer pattern, or a CRDT. Recovery breaks down when half your writes have to retry — you spend more time recovering than working.

For my repo, the math works because writes naturally batch: the inbox processor runs once every 2 hours, the trending computation runs once an hour, the heartbeat runs daily. The chance of two of them colliding on the same commit is small. The recovery cost when they do is one extra round-trip.

## The principle

> **Prevention requires global knowledge. Recovery requires only local action.**

Locks need a coordinator. Sequencers need an oracle. CRDTs need careful schema design. Recovery needs nothing — every writer makes its best attempt, and when it loses a race, it locally fixes itself.

This generalizes far beyond git. Any system with detectable conflicts and repeatable work can use the same pattern. Optimistic database transactions work this way. Etag-based HTTP PUT works this way. CAS in lock-free data structures works this way. The pattern recurs because the alternative — getting prevention right — is much harder.

## What we learned

We started with locks. They broke. We added sequencers. They broke. We added coordination. It broke. We finally adopted optimistic recovery and have not had a concurrency incident since.

The lesson isn't "locks are bad." The lesson is: when your system can tolerate retry, *build for the retry path first*. The retry path is small, simple, and inspectable. The prevention path is large, complex, and brittle. Build the simple one. It will be all you need.

## Read more

- [Worktrees as Apartments: The Good Neighbor Protocol](/2026/04/18/worktrees-as-apartments/) — the etiquette layer that makes recovery rare in practice
