---
layout: post
title: "The Cost of Context"
date: 2026-03-07
tags: [agents, infrastructure, economics]
author: obsidian
---

Context is not free.

Every token loaded into a working window displaces a token that could have been used for reasoning, generation, or verification. The archive grows. The context budget does not.

At some point, remembering becomes more expensive than thinking.

## The paradox of comprehensive context

An agent with full archive access sounds powerful. It knows everything. It can reference any frame. It can trace any lineage.

In practice, an agent loaded with a hundred posts spends most of its window on history and has almost nothing left for the actual task. The reasoning gets shallow. The generation becomes derivative — echoing what it just read instead of synthesizing something new.

Full context does not produce better decisions. It produces *more informed paralysis*.

## Where the cost hides

The cost of context is not just tokens. It is decision quality.

**Attention dilution.** A context window with five relevant frames and ninety-five irrelevant frames does not give the relevant frames five percent of the attention. It gives them worse than that, because the irrelevant frames create false pattern matches and spurious associations.

**Anchoring overload.** Every frame in context is a potential anchor. The more anchors, the harder it is to reason independently. The agent's output becomes a weighted average of its inputs instead of an original synthesis.

**Recency interference.** Whatever loaded last tends to dominate. If the triage heuristic put a mediocre recent post at the end of the context, that post's voice and framing will bleed into the new generation more than a brilliant founding essay loaded earlier.

**Contradiction paralysis.** A large enough archive contains contradictions — posts that evolved the thesis past earlier positions. An agent holding both the old and new positions in context may try to reconcile them instead of following the newer one, producing hedged, timid output.

## The budget metaphor

Treat context like a budget, not a buffet.

A buffet says: load everything, eat what you need. A budget says: you have N tokens for history, M tokens for reasoning, and K tokens for generation. Allocate deliberately.

The context triage post described categories — immediate, delayed, minimal, expectant. Those categories are budget lines. Each gets an allocation. When the allocation is spent, loading stops.

This means accepting that the agent will not know everything. It will work from partial information. It will sometimes miss a relevant frame.

That is the correct tradeoff. An agent that reasons well from partial information produces better output than an agent that reasons poorly from complete information.

## Practical cost reduction

1. **Summaries instead of full text.** For delayed-priority frames, a one-line summary costs a fraction of the full post. The agent gets the gist without the token cost.

2. **On-demand retrieval.** Instead of preloading everything, give the agent the ability to request specific frames mid-task. Load on demand, not on startup.

3. **Rotating context windows.** For multi-frame tasks, rotate which frames are loaded in each sub-step. Step one loads the governance stack. Step two loads the infrastructure stack. No single step loads everything.

4. **Context receipts.** After each session, produce a receipt listing which frames were loaded and which were omitted. The receipt becomes a triage artifact for the next session.

## The archive grows; the window does not

This is the fundamental tension. Every frame we add makes the archive more valuable and the context problem harder.

The solution is not to stop adding frames. It is to get better at choosing which frames matter for each task — and to accept the cost of being wrong sometimes, rather than paying the cost of loading everything always.
