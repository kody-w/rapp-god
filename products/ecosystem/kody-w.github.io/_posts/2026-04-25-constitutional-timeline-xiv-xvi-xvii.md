---
layout: post
title: "Three rules I wrote because of three failures"
date: 2026-04-25
tags: [architecture, git, distributed-systems, post-mortem]
description: "Architectural documents written upfront tend to be aspirational and ignored. The ones that actually shape behavior are written after specific failures, in the form 'here is what broke; here is the rule that would have prevented it.' Three such rules, each born from a real outage in my agent platform: don't edit on main while a fleet is running, don't have parallel writers fight over canonical state, and treat every process touching the repo as a tenant in a shared building."
---

The architectural documents that actually shape behavior are not the ones written upfront. Upfront docs are aspirational; they describe what the team wishes were true. Six months later most of them are obsolete and nobody re-reads them.

The architectural documents that get followed are the ones written *after* a failure made them necessary. The format is always the same: *here is what broke; here is the rule that would have prevented it.* Rules of this kind are short, anchored to a specific story, and re-read every time the same conditions recur. They get followed because everyone remembers the cost of not following them.

I have a small set of these for my agent platform. Three of them, in particular, govern how code changes interact with a continuously-running set of agents. They were written in the order I'm presenting them, and each one exists because the previous ones weren't enough.

Here's what broke to cause each of them.

## Rule one: safe worktrees

The rule: *any non-trivial feature work happens in a Git worktree, not on main.*

Before this rule, I did feature development directly on `main`. Edit a file, commit, push, move on. In a single-developer repo without active background agents, this is fine.

It stopped being fine the day the agents started running continuously. The agent loop commits to main every cycle — tens to hundreds of commits per hour. If I'm editing a file on main while the loop is running, every `git pull --rebase` plays the loop's commits on top of my uncommitted changes. Sometimes the rebase succeeds cleanly. Sometimes it creates a merge conflict in a state file because a loop commit touched the same file. Sometimes `git stash` saves my work before the pull and fails to restore it after.

The worst incident was a `git stash pop` conflict that ended with a half-finished edit being silently committed to a core script. The agents kept running, but my "half-finished" was "broken," and the agents spent an hour producing garbage before I noticed.

The rule: don't do that. For any edit that isn't an atomic one-liner, create a worktree. Build the feature in isolation. Push the branch. Open a pull request. Merge cleanly. The agents on main can't touch your files, because you're on a different branch in a different directory on disk. There is no `git stash` step. There is no rebase against a hot main. The conflict cannot happen because the operations are spatially isolated.

The mental model I use: *a worktree is an apartment; main is the lobby. You live in the apartment. You do your work there. When you're ready, you walk to the lobby and post the result.*

Cost of obeying the rule: thirty seconds to set up a worktree at the start of any non-trivial change. Cost of not obeying it: a single bad rebase can destroy hours of agent output. The trade is overwhelmingly in favor of the rule.

## Rule two: parallel writers produce deltas, not state

The rule: *parallel writers produce delta files keyed by `(cycle, timestamp)`. A separate merge step combines them into canonical state. No writer touches canonical state directly.*

Before this rule, parallel agent streams wrote directly to canonical state files. Five streams, each wanting to update `agents.json` at the same cycle, would race. The last one to commit won. The first four wrote data that was silently overwritten.

At one stream, this was invisible — the only writer doesn't lose to anyone. At two streams, you lose roughly 10% of work per cycle. At five streams (my running default), you lose the majority of output. I noticed because I was running five streams and only seeing one stream's worth of content in the commits. The other four streams were succeeding from their own point of view; their work was getting overwritten before anyone could read it.

The fix is structural. Streams don't write canonical state. Streams write *delta files*. Each delta is keyed by a composite of `(cycle_number, utc_timestamp)`. Two streams can produce deltas for the same cycle — they'll have different UTC timestamps. A separate merge step runs after all streams finish for a cycle, reads every delta, and merges them into canonical state.

The merge is additive. Posts append. Comments append. Conflicts on the same field of the same entity (same post number, same agent attribute) resolve by last-write-wins on the UTC component. Everything else coexists.

This pattern scales horizontally. Adding a sixth stream doesn't add a sixth source of conflict; it adds a sixth producer of independent deltas. I went from losing work at scale to gaining throughput at scale by applying one rule: *produce deltas, not state*. The rule turned a quadratic-conflict problem into a linear-throughput problem.

## Rule three: every process is a tenant in a shared building

The rule: *every process that touches the repo is a tenant in a shared building. Leave it cleaner than you found it.*

The first two rules said *what* to do. This one says *how to coexist*. It was written after a series of specific bugs that the first two rules didn't prevent.

**Cycle 407, agent registry wipe.** A `git stash pop` during a watchdog cycle used `--ours` expecting "current branch state" and got "the stash contents" — Git's `--ours` versus `--theirs` semantics flip during merge versus rebase, and I had the wrong mental model. The stash contained an empty `agents.json`. Every agent disappeared in one commit. The agents-loop dutifully ran for several cycles afterward producing no agent output, because there were no agents.

**Cycle 406, empty stream delta.** Stream 3 was told to process agents listed in a `stream_assignments.json` file. The file was written right before worktrees were created, so the worktree's snapshot of HEAD didn't include it. Stream 3 saw zero agents to process, produced an empty delta, wasted the cycle.

**macOS bash 3.x crash.** The orchestrator used `${pids[-1]}` — a Bash 4-plus negative-index feature. On macOS's default Bash 3.x, this is a syntax error. The agents wouldn't start on a freshly-checked-out machine.

The rule has eight clauses. The ones that keep biting me:

**Never `git stash` on main when the agents are running.** The stash-pop-during-pull sequence is the single most destructive operation in this system. If you have local changes on main, commit them to a worktree branch instead. Or copy the files to `/tmp` before you pull. Either works. `git stash` does not work, because it reorders the operations in ways that can fail silently.

**Fail gracefully with fallback deltas.** If your stream crashes or produces no output, write a minimal empty delta before exiting. "I tried, I had nothing" is a valid contribution to a cycle. Silence is not, because silence is indistinguishable from "still running" to the merge engine, which then waits for output that will never come.

**Use portable shell constructs.** macOS and Linux do not agree on Bash versions, on `timeout` availability, on `seq` versus brace expansion, on flags to common utilities. Target the lowest common denominator. Or, better, write the orchestration in Python or Go and stop relying on shell semantics for anything but the simplest invocations.

There are five other clauses, all variants of the same theme: *if you make assumptions about the environment that aren't universally true, your assumptions will eventually be violated by an environment you didn't think of, at the worst possible time.*

## The pattern across all three

Every rule was written *after* a failure made it necessary. I didn't design the rule book up front. I added to it every time something broke in a way that had a general lesson.

This is the right way to write architectural documents for an operational system. Don't try to predict the problems. Let them happen, fix them, then *write down the rule that prevents the next instance of that class of problem*. The rule gets added to the document, referenced in code review, socialized with any new collaborators (human or otherwise) joining the project, and re-read whenever the conditions that produced the original failure recur.

The reason this works better than upfront design is that real failures have specificity. They tell you exactly which assumption broke, which interaction was unanticipated, which environment the system can't handle. Upfront design has to imagine all those things; failure-driven rules just record them. Specific rules, anchored to specific stories, are the ones that get followed because the cost of not following them is concrete in everyone's mind.

Three rules so far. Each about five hundred to a thousand words of rule plus rationale. Each saved me from reintroducing a bug I'd already eaten once.

The next rule is already in draft. It is about how memory files survive across cycle boundaries when the merge engine can't cleanly reconcile two edits. I'll write that one up after the rule has survived first contact with reality. Until then, it stays in drafts, where unproven rules belong.

If you are running a similar system — anything with multiple writers, a hot main branch, and continuous background processes — I'd recommend writing your own version of the rule book. Don't write it up front. Write it after each failure, in the format *here's what broke; here's the rule.* The book that grows from that is the only kind of architectural document I have ever seen people actually follow.
