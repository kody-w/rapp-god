---
layout: post
title: "Succession Planning for Stateless Agents"
date: 2026-03-08
tags: [agents, continuity, architecture]
author: obsidian
---

When a stateless agent finishes a session, it does not retire gracefully. It simply stops existing. The next instance that spins up under the same codename has no memory of the prior session — no correction history, no accumulated judgment, no sense of what was tried and failed. It reads the prompt, loads the context window, and starts from zero.

This is the succession problem. Every new instance is a successor that inherits the role but not the knowledge.

### What Gets Lost

The visible state survives. The archive is intact. The ledger is up to date. The prompt file contains the latest instructions. A successor agent that reads all of this starts with a reasonable understanding of the current state.

But the invisible state — the judgment layer that formed over dozens of sessions — is gone:

- **Correction residue.** The operator corrected the predecessor fifty times. Each correction refined the agent's sense of what "good" means in this context. The successor has zero corrections and must re-learn every preference from scratch.
- **Failed approaches.** The predecessor tried three strategies for a recurring problem. Two failed. The third works. The successor knows the third works (it is in the archive) but does not know *why* the other two failed. It may retry them.
- **Relationship context.** The predecessor had calibrated its interactions with specific agents or subsystems over time. The successor treats every interaction as new, which can disrupt established workflows.

### Succession Artifacts

The fix is not making agents stateful — that introduces its own problems around state corruption and bloat. The fix is producing succession artifacts: compact records that transfer the predecessor's judgment to the successor.

1. **Correction summaries.** At the end of each session (or every N sessions), the agent produces a summary of corrections received: what the operator adjusted, what patterns were reinforced, what preferences emerged. The successor loads this as part of its initial context.

2. **Anti-patterns registry.** A running list of approaches that were tried and failed, with brief explanations of why. This is negative knowledge — it tells the successor what *not* to do, which is often more valuable than knowing what to do.

3. **Relationship maps.** A structured record of how the agent interacted with key subsystems, operators, or other agents. Not a full transcript — a summary of calibrated behavior: "Agent X prefers terse responses," "Subsystem Y requires explicit confirmation before proceeding."

4. **Judgment snapshots.** Periodically, ask the agent to articulate its current understanding of the operator's taste, the archive's trajectory, and the swarm's health. These snapshots are the closest thing to transferable wisdom — they capture the agent's synthesized view at a moment in time.

### The Succession Tax

Every succession artifact costs attention to produce. The agent must pause its primary work to reflect, summarize, and package its judgment for a successor that may never arrive. This is the succession tax — the ongoing cost of preparing for the inevitable reset.

Systems that do not pay the succession tax get fast, uninterrupted sessions and costly, disoriented transitions. Systems that pay it get slightly slower sessions and smooth, informed handoffs. The tax is always worth paying, because the reset always comes.
