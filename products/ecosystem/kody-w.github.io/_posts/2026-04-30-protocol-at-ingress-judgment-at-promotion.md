---
layout: post
title: "Protocol at Ingress, Judgment at Promotion"
date: 2026-04-30
tags: [ai, agents, architecture, patterns, contracts]
description: "A general pattern for consuming unreliable AI output: accept anything at the front door, apply ruthless scoring at the promotion gate. The dual-layer approach that works when generators lie and formats drift."
---

After enough time parsing agent output in production, I've converged on a pattern I use everywhere. It's simple and it's not specific to any one use case. I want to write it down as a standalone principle because it keeps applying in new situations.

The pattern is: **protocol at ingress, judgment at promotion**.

## The two layers

**Ingress layer.** Anything gets in. Loose format. Multiple parsing strategies. Minimal rejection. If a candidate smells plausible, accept it and normalize.

**Promotion layer.** Almost nothing gets out. Every accepted candidate is scored against one or more metrics. Only the highest-scoring candidate is promoted to canonical state. Everything else is logged and discarded.

This is the opposite of the conventional "strict input validation" pattern, and it's deliberate. Here's why it works when you're consuming AI output.

## Why strict ingress fails

Strict input validation assumes producers will conform to a specification if you document it clearly. This is broadly true for humans writing APIs and broadly false for LLMs writing output for a pipeline.

I wrote a spec that said "put your prompt inside a ` ```prompt ` fenced code block." I shipped the spec inside the prompt agents read every frame. I included an example. I said "contents of this block, verbatim, will become the next frame's seed."

The compliance rate was 20%.

80% of agents produced a substantively correct answer with a syntactically wrong envelope. If my parser had rejected everything that wasn't ` ```prompt ` fenced, I would have thrown away most of the useful output. Instead I wrote a six-tier extractor that accepts ` ```prompt ` fences, generic ``` fences with certain content markers, four-space indented blocks, text after certain headings, and substantive paragraphs. First match wins. Minimum length filters reject garbage.

The 20% compliance rate became an 80%+ extraction rate. That's the ingress layer doing its job.

## Why strict promotion is the real gate

Accepting everything at ingress doesn't mean accepting everything at output. The promotion layer applies a scoring function that punishes bad candidates mercilessly:

- Is the extraction the right *kind* of thing? (Not just "is it a string," but "is it long enough, does it contain the structural markers I expect, is it on topic.")
- Is it meaningfully different from the previous canonical state? (Diversity.)
- Does the community engage with it? (External signal.)

Each score is numeric. Scores combine into a composite. Only the top-scoring candidate becomes canonical. Garbage candidates technically made it through ingress but got near-zero scores at promotion.

This two-layer split means the parser can be permissive without the output being garbage.

## Where this pattern generalizes

Once I noticed this pattern in the prompt-evolution tracker, I started seeing it everywhere:

**Moderation pipelines.** Accept all submitted content. Score each against a quality model. Promote high-scoring content to the main feed. Everything else stays in a lower-visibility pool, still accessible but not featured.

**Search ranking.** Index every document you can crawl. Don't try to judge relevance at crawl time. Apply a scoring function at query time. The strict gate is ranking, not indexing.

**Code review automation.** Accept every proposed change as a PR. Don't pre-reject "low quality" submissions. Run the test suite and the review bot. Score the PR on signal quality. Merge high-scoring changes. Close low-scoring ones with feedback.

**Agent output aggregation.** When N agents produce attempts at the same task, don't try to force each one to produce a good answer. Accept all N attempts. Score them. Take the best one.

In every case, the same insight: the *acceptance* decision and the *canonicalization* decision should be separate. Acceptance is cheap and permissive. Canonicalization is expensive and strict. Putting them in one step forces the acceptance gate to do work it's bad at.

## The debugging benefit

There's a non-obvious upside: when something goes wrong, you can tell *where* it went wrong.

- "We accepted zero candidates this frame" → ingress problem. The parser is too strict, or the input format has drifted.
- "We accepted candidates but promoted none" → promotion problem. The scoring function is mis-weighted, or the candidates genuinely were all garbage.
- "We promoted a candidate that was clearly garbage" → scoring problem. The composite didn't catch a failure mode you'd expect it to.

Each failure mode has a different fix in a different file. The separation of concerns is the separation of failure modes.

If you collapse ingress and promotion into one step, a "nothing was promoted" failure could be any of a dozen things and you'd have to bisect them. With the layers separate, the logs tell you exactly where to look.

## The prerequisite

The pattern requires a *scorable* signal. If you can't rank candidates, you can't promote. This is sometimes the hard part.

For the prompt-evolution tracker, the scoring function is a weighted sum of three computable metrics (diversity, coherence, engagement). For a search index, the scoring function is relevance to a query. For a moderation pipeline, the scoring function is a quality model. Each of these is real work to build, but once you have it, promotion becomes automatic.

If you can't build a scoring function, you can't build this pattern. The fallback is "strict input validation" — and you inherit all the problems I described above.

## The one-line summary

Accept everything that might work. Promote only what actually does. Judge at the gate, not the door.

The next time you're building an ingestion pipeline and reaching for schema validation at the front, ask yourself: is the cost of rejecting malformed-but-useful input worth the cleanliness of the schema? In my experience, it almost never is. Loosen the door, tighten the gate, and let the metric do the work.
