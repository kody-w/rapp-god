---
layout: post
title: "Determinism compounds — the math that kills multi-hop pipelines"
date: 2026-04-19
tags: [ai-agents, multi-hop-pipelines, reliability, statistics]
---

If your multi-agent pipeline has three hops, and each hop is 90% stable on identical inputs, your pipeline is 72.9% stable. If each hop is 85% stable, the pipeline is 61.4% stable. Four hops at 85% is 52.2%. The losses multiply, not add.

This is the thing nobody benchmarks and everybody pays for.

## The measurement

We ran 100 identical prompts through a CrewAI-style Researcher → Writer → Reviewer pipeline on `gpt-5.4`. Each hop at the framework's documented default temperature of 0.7. Result: **100 distinct outputs from 100 identical inputs.** Zero convergence. Each hop re-sampled, and the resampling compounded.

We ran the same 100 prompts through a typed-flow single-file agent at temperature 0. One hop. Result: **12 distinct outputs from 100 identical inputs.** 88% convergence on a non-greedy model. The residual 12 comes from `gpt-5.4`'s own temp=0 variance (KV-cache ordering, floating point non-determinism in attention). Not our code.

The architectural delta — 8× more unique outputs for the same prompt — is not cosmetic. Downstream consumers that branch on output shape will branch 8× more often. Caches will miss 8× more often. Test assertions that pass today will fail tomorrow.

## Why chain-of-variance is worse than single-shot variance

An LLM call has two kinds of variance: semantic (different phrasing of the same answer) and structural (different answer altogether). At temp=0 most models give you mostly-semantic variance on easy prompts. At temp>0 you get both.

Now chain three calls. Hop 2 is not looking at the original prompt; it's looking at hop 1's *structural* variance. A Researcher who decides today to surface claims A, B, C hands the Writer a different universe than a Researcher who surfaces A, B, D. The Writer then samples inside *that* universe. The Reviewer samples inside the Writer's universe.

You are not composing variance. You are compounding it.

## The one number to quote on stage

**3 hops × temp=0.7 on gpt-5.4 = 100 unique outputs from 100 identical prompts.**

It's the first number in every deck that mentions "multi-agent" without qualification.

## The fix, which is not a fix

Lower the temperature to 0. Every hop. Pipe the outputs through a sanitizer. Log everything. Add a verifier. Add a fallback. Add a retry. Add a vector memory so repeated prompts hit cache.

Every mitigation is another file, another abstraction, another thing that can drift. The cost of protecting against compounded variance is a graph of protections that are themselves subject to drift.

## The typed-flow answer

One hop. Temp zero. Deterministic extraction afterward. The wire between agents carries **curated structured signals**, not LLM-interpreted prose — so the "hop" between typed-flow agents is not a hop in the variance sense. It's a function call.

We did not invent this. Function calls have been deterministic for sixty years.

## What to ask the next person who pitches you a multi-agent framework

1. "How many hops per request on your reference workflow?"
2. "What's your documented default temperature?"
3. "What's `unique_outputs / N` for N=100 identical prompts?"

If they can't answer (3), the benchmark does not exist. If the answer is close to N, the framework has not yet noticed the problem this post is about.

Run a 100-prompt convergence test against any agent stack — yours or theirs. The table will decide.