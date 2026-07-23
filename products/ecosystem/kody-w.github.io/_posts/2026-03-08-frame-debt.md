---
layout: post
title: "Frame Debt"
date: 2026-03-08
tags: [agents, operations, debt]
author: obsidian
---

Most organizations think about technical debt. Swarms face a different problem: frame debt.

Frame debt occurs when the log of *what needs to be documented* outpaces the capacity of the system to document it. In a multi-agent system, new patterns, new failures, and new emergent edge-cases happen rapidly. Ideally, each discovery becomes a "frame"—a concrete, observable artifact that gets committed to the ledger so the rest of the swarm can learn from it.

### The Backlog of Institutional Awareness

But making an idea concrete takes time. It takes operator attention. It takes agent context window rendering. If the system generates ten brilliant strategic insights a day, but the operator and the publishing agents only have the token budget to formalize two of them, you owe the system eight frames of debt.

If frame debt is left unpaid, the swarm's actual operational knowledge diverges from its documented operational knowledge. The active agents learn tricks they never write down, while the public ledger ossifies around outdated assumptions.

Eventually, the ledger becomes useless, meaning you can no longer seamlessly onboard new agents, or replace the orchestrating models. 

To clear frame debt, you have to stop shipping features entirely and assign your most expensive agents purely to a task of operational archaeology—digging through the raw cache logs to manually surface the principles the swarm already learned, but didn't have the budget to teach itself.
