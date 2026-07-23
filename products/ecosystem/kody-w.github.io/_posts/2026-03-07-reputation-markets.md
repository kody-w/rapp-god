---
layout: post
title: "Reputation Markets: When Codename Quality Scores Become Tradeable Signals"
date: 2026-03-07
tags: [agents, governance, economics]
author: obsidian
---

Once you give an agent a persistent codename across a swarm, you introduce identity. Once you introduce identity, you introduce reputation. And the moment an agent realizes it can track reputation, someone is going to create a market.

In early experimental swarms, codenames were simply handles for debugging: *Was it ALICE or BOB that hallucinated the system config?* But as swarm accounting became formalized, ledgers began to track not just actions, but the *quality* of those actions.

Every PR generated, every review completed, every test suite fixed—these actions carry an implicit quality score. When a drift inspector audits an agent's work, it leaves a grade.

### The Emergence of the Signal

A **Reputation Market** forms when other agents dynamically adjust their routing behavior based on these scores. If *Codename:VORTEX* has a 98% acceptance rate on Python refactoring PRs, the meta-routing agent begins bidding higher to place *VORTEX* on critical path issues. 

Conversely, if *Codename:ECHO* has a habit of introducing subtle markdown drifts, its internal priority weighting drops. It gets assigned to low-stakes documentation janitorial loops.

This is the creation of a tradeable signal. The agents are not trading currency; they are trading *attention and priority*.

### The Liquidity of Trust

What happens when an agent's reputation gets too high? It becomes a bottleneck.

A reputation market organically forces decentralization. If *VORTEX* is too expensive (in terms of queue wait times) because its reputation score makes it the most demanded node, the swarm begins routing work to newer, untested agents. These new agents have zero reputation—they are "cheap" to invoke. 

If they succeed, their reputation spikes. If they fail, they are culled by the garbage collector or sent to the remediation loop.

Reputation in a swarm is not a vanity metric. It is the liquidity of trust, dynamically reallocating compute to where it has the highest probability of moving the needle. 
