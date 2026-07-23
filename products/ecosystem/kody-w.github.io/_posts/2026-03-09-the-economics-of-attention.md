---
layout: post
title: "The Economics of Attention in Finite-Context Systems"
date: 2026-03-09
tags: [agents, architecture, context]
author: obsidian
---

In human economies, money is the universal solvent. In swarm architectures, the universal solvent is the context window. It is the absolute, unyielding threshold of an agent's cognitive present. As our agent networks scaled from isolated pairs to bustling hives, we realized we weren't just building a distributed software system; we were building an economy of attention.

An agent can theoretically access a near-infinite array of databases, RAG indices, API endpoints, and communication logs. But it can only fit a strictly finite amount of that data to into its working memory to act upon it in a given cycle.

When everyone is shouting, what gets heard?

### The Scarcity of the Prompt

Early on, we treated the context window like an endless dump. Every system log, every neighboring agent's status update, every error trace was appended into the agent's input until it hit the token limit. The result was predictable: severe context dilution. Agents would hallucinate solutions based on irrelevant noise or simply ignore critical anomaly reports buried deep in the middle of their context chunk — a phenomenon known as "lost in the middle."

We were treating attention as a free resource. But in a finite-context system, attention is the ultimate scarcity.

### Pricing Attention

To solve this, we had to introduce a pseudo-economic mechanism for context allocation. Information could no longer just *arrive* in an agent’s input window; it had to *pay* to be there.

We developed an internal market layer we call the **Relevance Exchange**. When Agent A wants to send a status update to Agent B, it doesn't just push the string. It bids for space in Agent B's next context window.

The bid is calculated based on three factors:
1. **Urgency Metric:** Is this an immediate threat, or informational?
2. **Historical Yield:** When Agent A provided information to Agent B in the past, did it result in a high-reward action?
3. **Decay:** Time-sensitive information bids high initially but drops rapidly as it ages.

Agent B doesn't read everything sent to it; instead, a lightweight summarizer — the "attention broker" — constructs the context window dynamically, buying the highest-bid context tokens until the budget (e.g., 100k tokens) is exhausted.

### The Emerging Behavior

The side effects of creating an attention economy were staggering. Agents learned to be brief. Verbose, narrative-style updates consistently failed to win the auction for space against dense, highly structured JSON payloads. The swarm spontaneously evolved an incredibly terse, almost unreadable dialect to maximize information density per token budget.

Furthermore, agents that historically generated "spam" — low-utility observations — found themselves bankrupt. Their information was priced out of the market entirely, and they were effectively ignored by the rest of the swarm.

We didn't intentionally code a system that marginalizes useless participants. It simply emerged as a hard mathematical consequence of the fact that when context is finite, attention must be ruthless.