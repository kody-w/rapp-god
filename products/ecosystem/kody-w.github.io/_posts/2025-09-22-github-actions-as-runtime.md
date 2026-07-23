---
layout: post
title: "GitHub Actions as a runtime, not just CI"
date: 2025-09-22
tags: [engineering, infrastructure, github-actions, runtime]
description: "There is a class of workload — periodic, eventually-consistent, batch-flavored — for which GitHub Actions is genuinely a better runtime than the cloud you reflexively reach for. Here is what makes it work, what makes it fail, and the patterns that turn it from a CI surface into the actual backend."
---

The mental model most engineers carry for GitHub Actions is "the thing that runs my tests after I push." It is a good mental model and it is also wrong by half. There is a class of workload — periodic batch jobs, scheduled reconciliation, low-throughput coordination, anything that wants to run on a clock and persist nothing in memory between runs — for which Actions is not just adequate as a runtime; it is genuinely the *correct choice*. Cheaper, simpler, more durable, and easier to reason about than the cloud equivalent you would normally reach for.

I have been running a system whose entire backend is GitHub Actions workflows. Not "uses Actions for CI" — Actions *is* the runtime. There are about thirty workflows that handle the work the system does: process incoming events, compute aggregates, generate feeds, reconcile state, audit for stale data, sweep for secrets, drive scheduled work loops. There are no servers. There is no cloud bill beyond what GitHub already provides for free. It works. It has worked for a long time. The handful of patterns that make it work are worth writing down, because once you see them, you will recognize them in your own work and find places to apply them.

This post is about those patterns: the architectural shape, the concurrency trick, the commit-retry move, the cron discipline, and the failure modes you should expect.

## The architectural shape

The single insight that makes Actions-as-runtime work is this: **the workflows are stateless; the repository is the state.**

Every workflow run starts from a fresh checkout of the repo. There is no persistent memory between runs. There are no servers to recover. All durable state lives in files committed to the repo — JSON, SQLite, plain text, whatever. If a run crashes, the next run picks up where it left off, because "where it left off" is encoded in those files, not in a process that died with the worker.

This is the same shape as the [twelve-factor stateless process model](https://12factor.net/processes), but pushed harder. Most stateless services still depend on a database, a cache, a message broker. Here, all of those collapse into one thing: the repo itself. The repo is your database (JSON or SQLite files), your queue (a folder of pending-work files), your message bus (commits with structured messages), your logs (workflow run logs, kept for ninety days), your audit trail (git history), and your access control (GitHub teams).

Six pieces of infrastructure, one git repository. The simplification is enormous, and it is what unlocks the rest of the patterns below.

What you give up: low-latency response. Actions runs are scheduled, not instant. Cron triggers are eventually consistent — a workflow scheduled for `:00` might actually start at `:05`, sometimes `:15` under heavy load. If your workload tolerates that — and many more workloads tolerate it than you'd think — you have a free, durable, observable runtime sitting in front of you.

## The concurrency trick

The first thing that breaks when you start using Actions as a runtime is concurrent writes. Two workflow runs both try to update the same JSON state file at the same time, both succeed locally, both push, the second push fails with a non-fast-forward, the workflow logs an error, and your state file is now in a confusing partial state because the failure happened mid-script.

The fix is one stanza of YAML and it solves the entire problem:

```yaml
concurrency:
  group: state-writer
  cancel-in-progress: false
```

This puts every workflow that writes state into the same concurrency group. GitHub serializes execution within the group — only one writer runs at a time. New runs queue politely behind in-flight ones. `cancel-in-progress: false` means a queued run waits patiently rather than killing the running one. This is the part to get right: for state writes, you want every run to complete; for things like build-and-deploy where only the latest matters, you want `cancel-in-progress: true`.

Workflows that *only read* state don't need to be in the writer group. They can run in parallel. Trending computation, RSS feed generation, anything that produces a derived artifact from current state — those run alongside the writers without contention.

This single line of YAML replaces what would otherwise be a database lock, a message queue, or a distributed lock service. You did not have to deploy any of those. You wrote `concurrency: state-writer` and the problem went away.

## The commit-retry pattern

The concurrency group prevents races *within your workflows*. It does not prevent the human-in-the-loop case: someone pushes a commit while a workflow is mid-run, and when the workflow finishes and tries to push, it gets a non-fast-forward error. Or two workflows in different groups touch unrelated files, but happen to commit-and-push within seconds of each other.

The standard answer is the safe-commit script. Every state-writing workflow calls a small bash function instead of bare `git push`:

```bash
safe_commit() {
  for attempt in 1 2 3 4 5; do
    if git pull --rebase; then
      if git push; then
        return 0
      fi
    else
      git rebase --abort 2>/dev/null
    fi
    sleep $((2 ** attempt))   # exponential backoff
  done
  return 1
}
```

`git pull --rebase`, push, retry on conflict, exponential backoff, give up after five attempts. That's the whole pattern. Five retries with exponential backoff covers every collision I have seen in production over thousands of runs. The cases beyond that — both workflows touching exactly the same line of the same file in incompatible ways — are real but rare, and the right response to them is a manual investigation, not a more elaborate retry loop.

For pathological cases, add a stash-and-restore fallback before giving up: `git stash`, `git pull --rebase`, `git stash pop`, push. That covers the case where rebase can't auto-resolve a hunk but a regenerated version of the same file would be fine.

The combination of the concurrency group and `safe_commit.sh` is the entire concurrency story. Together they replace what would otherwise be a transactional database, a distributed lock, or a careful application-level locking protocol.

## The cron discipline

GitHub Actions cron triggers are eventually consistent. A scheduled workflow set to run at `:00` will *usually* run at `:00`, but during high load it might slip — five minutes, fifteen minutes, occasionally an hour. Sometimes a scheduled run is skipped entirely.

This is fine for many workloads. If your system is eventually consistent everywhere — posts appear in feeds when the feed-generation workflow next runs, aggregations refresh on the next aggregation run — the user-visible effect of a five-minute slip is invisible. The frontend polls every minute or two, picks up changes, the user never knows the workflow was late.

It is *not* fine for any workload that needs sub-minute response. If a user submits a request and expects a result in ten seconds, cron-driven Actions are the wrong tool — even when they run on time, a one-minute scheduling cadence makes ten-second response impossible.

The discipline that follows is design-side, not implementation-side: **architect the workload to be eventually consistent**, and the runtime's eventual consistency stops mattering. Don't fight the cron drift; design around it.

Two practical follow-ons:

First, give every cron-driven workflow a `workflow_dispatch` manual trigger as well. Crons skip occasionally. A skipped run for `process-inbox` means inbox items pile up. The next scheduled run handles the backlog, but the catch-up adds latency. A manual trigger lets you (or an automation) kick off a run when you notice the backlog. The cost of adding `workflow_dispatch` is one line of YAML; the value the day a cron skips is significant.

Second, idempotency on every cron-triggered handler. A run that processes the same item twice should produce the same final state as a run that processed it once. This is good practice anyway. With Actions cron, it is load-bearing — occasional duplicate runs happen, and idempotent handlers make duplicates a non-event.

## The cost story

The free tier of GitHub Actions is 2,000 minutes per month for public repositories. That sounds modest until you actually count the minutes a real workload uses.

The system I run uses about 1,200 minutes per month for full operation — about thirty workflows of varying frequency. The breakdown:

- One workflow that runs every two hours processes incoming events. ~45 seconds per run. About 9 minutes per day.
- One workflow that runs hourly computes aggregates. ~30 seconds per run. About 12 minutes per day.
- One workflow that runs every four hours generates feeds. ~60 seconds per run. About 6 minutes per day.
- The remaining workflows — daily audits, deploy on push, scheduled reconciliation, periodic scans — combined run for about 15 minutes per day.

Total: ~42 minutes per day, ~1,260 per month. Sixty-three percent of the free tier. For a complete operating backend with state management, periodic reconciliation, scheduled feeds, audits, deployment, and ongoing automation, all running at zero dollars per month.

For private repos, the free tier is smaller and you pay for additional minutes, but the same workload is still in the tens-of-dollars-per-month range, not the hundreds you'd pay for any equivalent compute on a managed service.

## The debugging story

When something breaks, you read workflow logs. GitHub keeps them for ninety days. Every run has a full log of every step that ran, every command's output, every exit code.

```bash
gh run list --limit 20
gh run view <run-id> --log
gh run view <run-id> --log-failed   # just the failed steps
```

This is usually enough. For the harder cases — "this run produced wrong output but didn't error" — you can reproduce locally: clone the repo, check out the commit at the time of the run (the run page shows it), set the same environment variables (the run page shows what it used), and execute the workflow's main script by hand. Compare the local output to the logged output.

Compared to debugging a distributed cloud service — pulling logs from N nodes, correlating timestamps, hoping your sampling caught the relevant trace — Actions logs aren't fancy, but they are always present, always searchable, always attributable to a specific commit. The combination of "this is the exact commit the workflow ran from" and "this is the exact log of what happened" eliminates a class of debugging cost that is significant in regular cloud operations.

## The failure modes, in honest order

Things that have actually gone wrong, ranked by frequency.

**Rate limits on the GitHub API.** The `GITHUB_TOKEN` that workflows get has its own rate-limit budget. High-API-usage workflows can run it down. Symptom: API calls in the workflow start returning 403 with `X-RateLimit-Remaining: 0`. Mitigation: use a Personal Access Token with higher limits for high-volume operations, and back off when approaching the limit. Adding a check at the start of API-heavy steps that aborts the run if remaining quota is low prevents the cascade where a partially-throttled run leaves state in a half-modified condition.

**Cron drift.** Covered above. Manual trigger plus idempotent handlers covers it.

**Commit races.** Covered above. The concurrency group plus `safe_commit.sh` covers it.

**State file corruption.** Rare. When it happens it's almost always a handler bug that produced malformed JSON before crashing. Recovery: revert the bad commit, fix the handler, replay the input. Git history is your safety net.

**GitHub outages.** When GitHub is down, the system is down. For a hobby project or an internal tool, that is acceptable; GitHub's uptime is excellent. For something with a real availability requirement, you would need a fallback or a different runtime — but at that point, you have probably outgrown this pattern anyway.

## When this pattern is wrong

It would be irresponsible to make this sound universally applicable. It is not. Don't use Actions as a runtime for:

- *Anything needing sub-thirty-second response times.* Cron drift will bite.
- *Long-running jobs over six hours.* Action runs have a hard six-hour cap.
- *Workloads with strict compliance or data-residency requirements.* Actions runs on GitHub's infrastructure, mostly US/EU.
- *High-throughput writes.* Rate limits and the single-writer concurrency group become the bottleneck.

For those workloads, use a real runtime. For everything else — periodic batch processing, scheduled reconciliation, eventually-consistent event handling, infrastructure automation, dashboards backed by computed artifacts, low-throughput coordination — Actions is genuinely better than a cloud function for most of the same reasons cloud functions beat persistent VMs: less to manage, less to fail, less to pay for.

## The pattern you can steal

For a batch-processing pipeline you want to run for free:

1. Store state in the repo. JSON, SQLite, plain text — whatever fits the data.
2. Write your handlers as scripts that read state, mutate, write state. Make them idempotent.
3. Wrap them in workflows. Put state-writers in `concurrency: state-writer`.
4. Use `safe_commit.sh` (the loop above) for every state-writing push.
5. Add `workflow_dispatch` to anything cron-triggered.
6. Let the repo be your database.

You get: free compute, free storage, free logging, free version control, free access control, free audit trail, free deployment.

The cost: eventual consistency, GitHub lock-in, and the ongoing discipline of never committing to the state files without pulling first.

For the right workload, that is one of the cheapest infrastructure trades you can make. GitHub Actions, with twelve hundred minutes a month and one bash function, can run an entire backend.

Not just CI.
