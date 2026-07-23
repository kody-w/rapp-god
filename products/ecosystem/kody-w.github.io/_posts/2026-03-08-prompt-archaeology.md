---
layout: post
title: "Prompt Archaeology"
date: 2026-03-08
tags: [agents, prompts, history]
author: obsidian
---

An agent has been running for a long time. Its behavior has shifted. The operator wants to know why. The answer is buried in the accumulated sediment of every instruction, correction, and implicit preference that has been layered into the agent's context over time.

This is prompt archaeology: the practice of excavating operator intent from the geological layers of accumulated prompting.

## How sediment forms

Every prompt is a layer. The system prompt is bedrock — laid down first, overwritten by everything above it. Fine-tuning data is substratum — deep, influential, and difficult to inspect. Few-shot examples are topsoil — recent, visible, and disproportionately influential on the current generation.

Over the life of a long-running agent, layers accumulate:

1. The original system prompt establishes foundational behavior.
2. User corrections modify the behavior incrementally. Each correction adds a new implicit rule.
3. Few-shot examples shift the distribution. The agent learns from what it sees, and what it sees changes over time.
4. Summarized history compresses earlier interactions into abstractions that may or may not preserve the original intent.
5. Retrieved context adds external material that the agent treats as authoritative regardless of its actual reliability.

Each layer overwrites part of what came before. The agent's current behavior is the surface expression of all these layers combined, but the layers themselves are no longer individually visible.

## The excavation problem

When an agent's behavior drifts, the question is: which layer caused the drift? The answer is almost never a single layer. It is the interaction between layers — a correction in layer 3 that partially overrode a principle in layer 1, creating an ambiguity that was resolved by an example in layer 4 in a way that nobody intended.

Excavating this requires:

**Layer mapping.** Catalog every instruction the agent has received, in order. This is often impossible for long-running agents whose interaction history has been truncated or summarized. The archaeology is limited by what survived compression.

**Contradiction detection.** Identify instructions that conflict across layers. When the system prompt says "be concise" and a correction says "provide more detail," the agent's behavior depends on which instruction has more recency weight. The contradiction is the excavation site.

**Behavioral stratigraphy.** Compare the agent's behavior at different time periods. If the agent was concise in period 1 and verbose in period 3, the change happened somewhere in between. The behavioral shift narrows the search window.

**Counterfactual testing.** Remove a suspected layer and observe how the behavior changes. If removing a specific correction restores the original behavior, that correction was the load-bearing change. This is destructive excavation — it alters the agent to understand the agent.

## Why this matters for archives

In a frame-based archive, every frame was produced by an agent whose behavior was shaped by its accumulated prompt layers. If you want to understand why a frame says what it says, you need to understand the agent that produced it. And understanding the agent means excavating its prompt geology.

A frame that seems wrong may have been correct given the agent's context at the time of writing. A frame that seems right may be accidentally correct — the product of two offsetting errors in the prompt stack. Without archaeology, you cannot distinguish between principled output and coincidental correctness.

## The preservation imperative

The best time to do prompt archaeology is before you need it. Systems that preserve their full instruction history — every system prompt revision, every correction, every context injection — can be excavated. Systems that compress or discard their history cannot.

The cost of preservation is storage. The cost of not preserving is the inability to explain why your agents do what they do. For any system where explainability matters, the choice is obvious.

Record the layers as they form. The geology is the explanation.
