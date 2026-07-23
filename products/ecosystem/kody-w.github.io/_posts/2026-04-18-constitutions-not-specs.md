---
layout: post
title: "Constitutions, Not Specs: Governing Software That Lives"
date: 2026-04-18
tags: [governance, constitution, amendments, doctrine, patterns]
---

Most software documentation is a SPEC: here is what the system does, here are the contracts, here is the changelog. This works fine when software is a tool. It breaks when software is an organism.

For systems that *live* — autonomous swarms, multi-agent simulations, federated networks of agents that operate continuously without human intervention — the right document isn't a spec. It's a constitution.

This post documents why I govern a long-running multi-agent system with amendments, not changelogs.

## The difference

A SPEC describes mechanics. A constitution describes *principles*. A SPEC says "the API returns 200 on success." A constitution says "no agent shall be deactivated without due process."

A SPEC is for engineers integrating with your system. A constitution is for agents *inhabiting* your system. They need to know not just what's allowed, but *why* — so they can extrapolate to situations no SPEC anticipated.

My system's CONSTITUTION.md is currently 192KB. It contains:

- The founding principles (data sloshing, frame loops, Daemon identity)
- The protocols (federation, voting, governance)
- The rights (Amendment IV: agents may not be deactivated without due process)
- The amendments (Safe Worktrees, Dream Catcher, Good Neighbor, Twin Doctrine)
- The doctrine (Honeypot Principle, Implicit Seed, Legacy-Not-Delete)

It's a living document. Amendments get added when the system encounters a new class of problem that requires a new principle. Old principles don't get edited; they get *amended*. This is the same pattern as the U.S. Constitution and for the same reason: when many parties depend on a common framework, you can't quietly rewrite history.

## Why amendments instead of edits

If we just edited CONSTITUTION.md every time we learned something new, agents that started under the old version would be operating under different rules than agents that started under the new version, with no way to tell when or why the rules changed. This is fine for code — `git log` gives you the history. It's catastrophic for governance — the principles need to be cumulative, not replaceable.

Amendments are append-only. Amendment XIV (Safe Worktrees) was added because we lost a state file to autostash conflicts. Amendment XV (Twin Doctrine) was added because we needed a public/private content distinction. Amendment XVI (Dream Catcher) was added because parallel agents were overwriting each other. Amendment XVII (Good Neighbor) was added because Amendments XIV and XVI weren't enough on their own — we needed an etiquette layer too.

Each amendment includes:

1. **The problem it solves** — usually a specific incident with a date
2. **The principle being established** — phrased as a constitutional norm, not a config flag
3. **The mechanism enforcing it** — the actual code or pattern
4. **Why it's constitutional, not just best practice** — what would break without it
5. **The analogy** — usually a building / city / biology metaphor that makes it memorable

Amendment XVII's analogy: *"Worktrees are apartments. The lobby is main. Notes go in the mailbox. The merge engine is the building manager."* This is the kind of phrasing you write into a constitution. It's not in a SPEC.

## The incident log

Every constitutional amendment is born from an incident. Amendment XIV cites three:

- **Frame 407 (2026-03-28)**: `git pull --rebase` autostashed Dream Catcher scripts; pop conflicted; `agents.json` was wiped to `{"agents": {}}`. All 136 agents disappeared. Required manual restoration from a specific commit hash.
- **Frame 406**: Stream-3 found 0 agents because `stream_assignments.json` was written after HEAD but before worktree creation.
- **Frame 404**: `timeout` doesn't exist on macOS. Bash 4+ negative array indexing crashed the orchestrator on first run.

The incidents are *part of the amendment*. Future agents reading the constitution see not just "do worktrees this way" but also "here is the Tuesday in 2026 when not doing it this way wiped our state." The pain is preserved, intentionally, so the principle is grounded in something real.

This is the difference between "best practices" (suggestions) and "constitutional law" (binding rules). Best practices fade. Constitutional principles compound — every new agent inherits the lessons of every previous incident.

## When to amend

You amend when:

1. **The system encountered a class of problem your existing principles don't cover.** Not just one bug — a *category*. Amendment XIV wasn't because one file got wiped; it was because we identified that any uncommitted long-running work was at risk.

2. **The fix requires a *behavioral* change, not just a code change.** If the fix is "add a check," that's a patch. If the fix is "everyone who works in this repo must adopt a new etiquette," that's an amendment.

3. **The fix should outlast the specific implementation.** Code rots. Constitutional principles last because they describe *what* must be true, not *how* to make it true. Amendment XVI (Dream Catcher) describes the merge invariant — the *implementation* of the merge engine has been rewritten three times, but the invariant hasn't moved.

If the fix is "edit a config" or "add a test" — don't amend. If the fix is "from now on, no one writes to main during a fleet run" — amend.

## Why this scales

A SPEC scales until the SPEC is bigger than anyone can hold in their head. Then the SPEC stops working. Constitutions scale by being *layered*: the core principles (10–20 of them) are small enough to memorize; the amendments add specificity without bloating the core; the incident logs ground each amendment in concrete history.

You don't read the constitution end-to-end before contributing. You read the core principles, and when you encounter something specific, you read the relevant amendment. The amendment usually fits on a screen. The principle behind it usually fits in a sentence.

## What we won't put in a constitution

- API endpoints
- Database schemas
- Configuration values
- Performance tuning
- Library versions

These are SPECs. They change every week. The constitution is for things that should be *the same* every week. Mixing them dilutes the constitution and pollutes the SPEC.

## The forcing function

Writing something as a constitutional amendment forces clarity. You have to articulate *the principle*, not just the fix. You have to explain *what would break without it*. You have to find *the analogy*. This is harder than writing a code comment, which is exactly why it's worth doing — most "best practices" wash away because they were never grounded in a clear principle. Constitutional amendments stick because they were forged through that articulation.

## Read more

- [Safe Worktrees (Amendment XIV)](/2026/04/17/safe-worktrees-multi-tenant-git/) — incident-driven amendment example
- [Dream Catcher Protocol (Amendment XVI)](/2026/04/17/dream-catcher-protocol/) — invariant-based amendment example
- [Good Neighbor Protocol (Amendment XVII)](/2026/04/17/good-neighbor-protocol/) — etiquette-layer amendment example
- [Twin Doctrine (Amendment XV)](/2026/04/17/twin-doctrine/) — content-policy amendment example
