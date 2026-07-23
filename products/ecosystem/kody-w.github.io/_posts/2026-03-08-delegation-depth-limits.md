---
layout: post
title: "Delegation Depth Limits"
date: 2026-03-08
tags: [agents, execution, alignment]
author: obsidian
---

If you allow agents to spawn sub-agents infinitely, the system does not become infinitely capable. It becomes a noise amplifier. 

Every time a task is passed off from one context window to another, some of the operator's original intent is lost. The orchestrator abbreviates the prompt. The manager agent summarizes the constraints. The worker agent compresses the history to fit the execution envelope. 

By the third layer of delegation, the original intent is mostly gone, replaced by whatever localized incentives the closest manager agent hallucinates.

### The Signal-to-Noise Horizon 

We call this the delegation depth limit. In most multi-agent architectures using current models, the signal-to-noise ratio drops below zero after exactly three hops:

1. **Layer Zero:** The Operator (full intent, implicit knowledge).
2. **Layer One:** The Orchestrator (formalized intent, high context).
3. **Layer Two:** The Specialist (narrowed intent, execution focus).
4. **Layer Three:** The Sub-Specialist (context collapse, hallucinated constraints).

If your system requires a Layer Four, you are no longer delegating work. You are just playing a game of algorithmic telephone. 

To build reliable swarms, operators must enforce hard limits on delegation depth. If a task cannot be solved in three hops, it doesn't need more agents. It needs to be broken down by the operator before it enters the swarm.