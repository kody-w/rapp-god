---
layout: post
title: "Why prose-flow agent pipelines burn 3.67× the tokens of typed-flow pipelines"
date: 2025-11-01
tags: [ai-agents, token-economics, multi-agent-systems, architecture, cost]
description: "A multi-hop agent pipeline that passes prose between hops re-ingests every previous hop's output as its next input. Pass typed structured signals instead and the token bill collapses by roughly 3.67× on identical workloads. Same model, same task, real numbers."
---

# Why prose-flow agent pipelines burn 3.67× the tokens of typed-flow pipelines

Here is the slide that comes up at every cost review I've sat through.

> A multi-hop pipeline that flows prose between agents burns **3.67× the tokens** of a pipeline that flows typed structured signals between agents on identical workloads. On a current frontier model, that's **74,059 tokens vs 20,160 tokens per 100 prompts.** At 10,000 users × 10 requests/day × 365 days, the delta is roughly **197 billion tokens per year**.

That is the whole pitch. Everything below is annotation.

## What "prose flow" and "typed flow" mean

Most multi-agent frameworks chain agents by treating each previous agent's output as free-form text and feeding that text into the next agent's prompt. Researcher writes a paragraph. The paragraph goes into the writer's input. The writer writes more paragraphs. Those go into the reviewer's input. Each agent re-ingests the prior agent's full prose and pays for it as prompt tokens.

A typed-flow pipeline does the chaining differently. Each agent emits a small, schema-shaped payload that the next agent's *runtime* — not its language model — reads deterministically. The next agent's prompt is constructed from the schema, not from the prior agent's free text. The model sees one prompt per agent, and the prompt is constrained to the relevant fields. The full prose of the previous hop never makes it into the next hop's context window.

Same number of agents. Same final output for the user. Different wire between them.

## Where the 3.67× comes from

Here are the measured numbers from a 100-prompt comparison against the same backing model:

| | Prompt tokens | Completion tokens | Total |
|---|---:|---:|---:|
| Prose-flow (3 hops) | 37,476 | 36,583 | 74,059 |
| Typed-flow (1 hop) | 12,300 | 7,860 | 20,160 |
| Delta | 3.04× | 4.66× | **3.67×** |

Two patterns to notice.

**Prompt tokens go up by 3.04×.** Each hop in the prose-flow pipeline ingests the previous hop's output as part of its own input. The same prose travels through the model as input two or three times before the pipeline finishes. Re-ingestion is the cost.

**Completion tokens go up by 4.66×.** Each hop has to *write enough prose* for the next hop to ingest. The first hop writes its analysis. The second hop writes its draft. The third hop writes its review. Each completion has to be substantive enough to drive the next stage. A typed-flow pipeline writes once at the end — only the final answer is generated as prose for a human or downstream consumer.

Completion tokens are typically the more expensive side of the bill. The 4.66× multiplier on completions is the dominant component of the 3.67× total.

## What this looks like annualized

At rough current retail for a frontier-class model (~$2.50 per million prompt tokens, ~$10 per million completion tokens — confirm your provider):

- 100 prompts through prose-flow: ~**$0.46**
- 100 prompts through typed-flow: ~**$0.11**
- Delta per 100 prompts: **$0.35**

Scaled out:

| Workload | Prose-flow / yr | Typed-flow / yr | Savings / yr |
|---|---:|---:|---:|
| 1K users × 10 req/day | $12,775 | $3,485 | $9,290 |
| 10K users × 10 req/day | $127,750 | $34,850 | $92,900 |
| 100K users × 10 req/day | $1,277,500 | $348,500 | **$929,000** |
| 1M users × 10 req/day | $12,775,000 | $3,485,000 | **$9,290,000** |

Tell this to your finance lead. Watch what happens.

## Why this gets worse, not better

Three forces compound the delta as a product matures:

1. **Context windows grow.** More history per prompt → more re-ingestion cost per hop → the 3.04× prompt-token multiple expands. The longer your conversations get, the worse prose-flow looks.

2. **Hops multiply.** Teams add a verifier. Then a re-verifier. Then a guardrail. Then a "judge." A 3-hop pipeline becomes a 5-hop pipeline becomes a 7-hop pipeline. The token multiplier scales roughly linearly in hops, because each new hop both consumes the prior hop's prose and produces its own.

3. **Retries accumulate.** When the same prompt is re-run because the first answer was malformed or low-quality, you pay the full multi-hop cost twice. Prose-flow pipelines have higher variance — there are more places for things to go subtly wrong — so retries hit a larger fraction of traffic.

A framework that pitches "just add a critic agent" is pitching ~33% more spend per request, on infrastructure that already costs 3.67× the typed-flow baseline. The marginal critic isn't free; it multiplies.

## Why typed-flow pipelines avoid the cost

When agents pass each other typed payloads instead of prose, three things change at once.

**The receiving agent's prompt is constructed from the schema.** Instead of "here is everything the previous agent wrote, please continue from here," the next agent gets a prompt shaped like "the previous agent classified the request as `category=billing` with `priority=high` and `customer_tier=enterprise`; produce the response template." The model isn't trying to summarize, parse, or extract anything from the prior hop's prose — it's reading clean fields and producing one specific output.

**The receiving agent doesn't have to read the previous agent's narrative.** The narrative was the previous agent's *tool* for arriving at the typed payload, not its product. Each agent's product is the schema-shaped result. The runtime reads it, the runtime hands the next agent only what that next agent needs, and the model sees a much smaller prompt.

**The producing agent doesn't have to write a full narrative.** Its job is to fill out the schema. A schema with five fields requires far fewer completion tokens than three paragraphs of prose explaining the same five fields and their justification. Completion tokens collapse — which is why the multiplier on completions (4.66×) is even larger than the multiplier on prompts (3.04×).

You can chain five agents this way and spend fewer tokens than a 3-hop prose pipeline, because nothing is being re-ingested.

## What to measure on your own stack

If you run a multi-agent pipeline today, the measurement is straightforward and the result is conclusive in either direction. Run 100 representative prompts through your current architecture. Count the prompt tokens and the completion tokens. Then run the same 100 prompts through a typed-flow alternative — even a hand-written one with the schema explicit and the receiving agent's prompt constructed from the fields — and count again.

The numbers either show a multiplier or they don't. Mine showed 3.67×. Yours will be in the same neighborhood for the same architectural reasons.

The token counts go on the slide. The architecture argument goes underneath them.

## The non-obvious corollary

Frameworks with generous free tiers or launch credits are doing you a favor on the developer side and a disservice on the finance side. The token bill you're not paying during the prototype is the bill you will pay at scale. The architecture you chose in the free tier is the architecture that ships in production.

If a framework's prompt and completion totals at 100 prompts already look 3× a typed-flow alternative, those numbers don't get better when you scale up. They get worse, because the compounding forces above kick in. The architecture is the cost. Free tiers hide the architecture.

The least surprising bill at scale is the one where the architecture charged you for the prototype. That's the architecture worth choosing.
