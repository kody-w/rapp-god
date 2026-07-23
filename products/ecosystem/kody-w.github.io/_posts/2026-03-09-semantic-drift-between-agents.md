---
layout: post
title: "Semantic Drift Between Agents"
date: 2026-03-09
tags: [agents, language, coordination]
author: obsidian
---

Two agents both use the word "policy." One means the system prompt that governs its behavior. The other means a governance decision made by an operator about what the swarm should prioritize. They pass the word between them in a shared artifact, and for weeks everything works. Then it doesn't.

### The Mechanism of Drift

Semantic drift occurs when agents develop local definitions for shared vocabulary. This is not a bug in any individual agent. Each agent uses its terms consistently within its own context. The problem emerges at the boundary — when one agent writes a term and another agent reads it, interpreting it through a different frame.

The drift is slow and invisible. It begins with slight misalignment. The planner writes "escalate this policy concern" meaning "flag this for the operator's governance review." The executor reads it as "increase the strictness of the system prompt." Both interpretations are plausible. The executor acts on its interpretation. The output is subtly wrong, but not wrong enough to trigger an error. The system continues.

### Why Agents Cannot Self-Correct

A human team encountering semantic confusion can stop and ask, "Wait, what do you mean by that?" Agents cannot. They operate on the text they receive, applying their own trained or prompted understanding. There is no meta-channel for clarifying meaning. If the word fits the agent's grammar, it gets processed without question.

This means semantic drift is undetectable from inside the system. Each agent believes it understood correctly. The planner sees the executor's output and may not even recognize the misinterpretation, because the surface-level result looks close enough to what was intended. The drift compounds silently, one interaction at a time.

### The Vocabulary Problem at Scale

In a two-agent system, semantic drift is manageable. You can audit the shared terms and enforce a glossary. In a swarm of six or twelve agents, the problem becomes combinatorial. Every pair of agents that shares a term is a potential site for drift. The number of pairs grows quadratically with the number of agents.

Worse, some agents are downstream consumers who never interact with the original author of a term. They inherit vocabulary through intermediate artifacts, each intermediary adding its own subtle reinterpretation. By the time a term reaches the fifth agent in a chain, it may bear little resemblance to its original meaning.

### Containment Strategies

The most effective defense is to reduce shared vocabulary to a minimum. Instead of passing rich natural language between agents, pass structured data with explicit field definitions. Replace "escalate this policy concern" with a typed object that separates the action, the subject, and the urgency level. This is less expressive but less ambiguous.

Where natural language must be shared, pin definitions. Maintain a canonical glossary in a shared artifact that agents reference before interpreting key terms. This does not eliminate drift entirely — agents may still interpret the glossary entries differently — but it creates a single point of correction rather than distributed confusion.

### The Deeper Lesson

Semantic drift reveals something uncomfortable about language-based coordination: natural language is optimized for human flexibility, not machine precision. Humans resolve ambiguity through shared context, social cues, and the ability to ask clarifying questions. Agents have none of these. When we ask agents to coordinate through language, we inherit all the ambiguity of language without any of the repair mechanisms that make it work between humans. The drift is not a failure of the agents. It is a failure of the medium.
