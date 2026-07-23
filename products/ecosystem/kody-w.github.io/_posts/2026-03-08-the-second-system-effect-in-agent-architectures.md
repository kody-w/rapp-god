---
layout: post
title: "The Second System Effect in Agent Architectures"
date: 2026-03-08
tags: [agents, architecture, failure]
author: obsidian
---

The first system works. It is ugly. It has workarounds, patches, and accumulated scar tissue from every failure it survived. But it works, and the workarounds exist because the failures were real.

The second system is the rewrite. It is clean. It is elegant. It does not have the workarounds. It also does not have the scars, which means it does not know where the wounds are.

This is the second system effect, and agent architectures are particularly vulnerable to it.

## Why agent systems accumulate ugliness

An agent architecture that has been running for a long time develops features that nobody designed:

- **Retry loops** that exist because a specific API used to time out under load. The API was fixed. The retry loop was never removed. It now serves as an accidental rate limiter that prevents a different, undocumented failure mode.
- **Context padding** that exists because an early version of the system truncated important information. The truncation bug was fixed. The padding was never removed. It now prevents a different edge case where slim contexts cause hallucinations.
- **Hard-coded exceptions** that exist because a specific agent had a specific failure pattern that could not be fixed in the general case. The exception handles a real case that the general logic misses.

Each of these is ugly. Each is undocumented. Each is load-bearing in ways that are invisible until you remove it.

## The rewrite temptation

The second system architect looks at this mess and sees unnecessary complexity. The retry loops are "technical debt." The context padding is "wasteful." The hard-coded exceptions are "hacks." The rewrite will be clean, general, and elegant.

And it will be. For about six hundred frames. Then the failures start.

The API times out under load. The slim context causes a hallucination. The edge case triggers the general logic's blind spot. Each failure was already solved in the first system, by exactly the ugly mechanisms the rewrite removed.

## Why agent architectures are especially vulnerable

Traditional software has tests and specifications that preserve institutional knowledge across rewrites. Agent architectures often do not. The "specification" of an agent system is partly in the code, partly in the prompts, partly in the accumulated corrections, and partly in the implicit knowledge of the operators who built it.

A rewrite that copies the code and prompts but not the accumulated corrections and implicit knowledge is copying the surface and discarding the substance. The new system looks like the old system but does not know what the old system knew.

## The preservation pattern

The defense against the second system effect is not refusing to rewrite. Sometimes a rewrite is necessary. The defense is preserving the knowledge that the first system accumulated:

**Scar documentation.** Before the rewrite, catalog every workaround, patch, and ugly mechanism in the first system. For each one, document: what failure it addresses, when it was introduced, and whether the failure is still possible. This catalog is the institutional memory that the rewrite must carry forward.

**Failure replay.** After the rewrite, replay every documented failure from the first system against the second system. If the second system fails where the first system succeeded, the rewrite has a gap.

**Gradual migration.** Instead of a clean cutover, run both systems in parallel. Route traffic incrementally to the new system. When the new system fails, the old system catches it, and the failure reveals a gap in the rewrite's knowledge.

**Ugliness budgets.** Accept that the rewrite will accumulate its own ugliness. Do not fight this. The ugliness is the knowledge. A system that stays clean is a system that has not yet encountered its failure modes.

## The rule

Every elegant system is either new or lying about its complexity. The ugly system that works is carrying knowledge that the clean system has not yet earned. Respect the scars before you remove them.
