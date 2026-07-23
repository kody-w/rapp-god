---
layout: post
title: "What shipping with an LLM partner actually cost — five months in numbers"
date: 2025-10-10
tags: [engineering, llms, ai-coding, cost-analysis, software-development]
description: "I ran the receipts on five months of building software in close partnership with a language model. Tokens. Dollars. Hours. Mistakes. Concrete numbers, with sources, so you can compare them to your own intuitions."
---

There is a category of post that says "I built X with an LLM in T weeks." The number is usually shocking. The numbers are usually qualitative — "one weekend," "one month," "one engineer instead of three." Useful for vibes. Less useful for budgeting.

I kept receipts on a five-month run of building real software in close partnership with a language model. Tokens. Dollars. Hours. Mistakes. Things that worked. Things that did not. The point of this post is to put numbers on a process that mostly gets discussed in adjectives, so that when you sit down to plan a similar effort you have actual figures to argue against.

I am not selling anything. The numbers are conservative reconstructions where the metering was incomplete and exact where it was not. Sources noted throughout.

## The work

Five months. A nontrivial side-project codebase: roughly 100,000 lines of Python, plus a frontend, plus SDKs in five languages, plus a couple hundred long-form blog posts. The system is in production. Other people use it. It runs autonomously when I am asleep.

Specifically:

- 120 pull requests merged.
- A protocol specification of meaningful size, drafted from scratch and revised several times.
- About 130 single-file plugins, each one a complete piece of behavior.
- A swarm server, a local runtime, a browser-side runtime, a worker, and a content pipeline.
- A bake-off harness that runs evaluations and produces reports.
- 120-ish blog posts of meaningful length, all written in the same partnership.

One person typing. One model in the loop, varying across months as the model menu changed.

## The token bill

| Period | Tokens | Approx USD |
|---|---:|---:|
| Month 1 (warm-up, scaffolding) | 18M | $43 |
| Month 2 (spec drafting + early features) | 64M | $156 |
| Month 3 (server-side build) | 92M | $221 |
| Month 4 (registry + content pipeline) | 117M | $278 |
| Month 5 (bake-off + harden + ship) | 134M | $312 |
| **Total** | **~425M** | **~$1,010** |

Source: usage exports from the cloud provider plus the model vendor's billing page. USD is approximate; pricing changed mid-period. The biggest single line on any month was prompt-side input, not generation — context windows get expensive when the working code is large enough that you have to feed back substantial chunks each turn.

Honest read: this is **somewhere between a small SaaS subscription and a junior contractor for a few weeks.** It is small relative to "build a thing in five months" budgets. It is not "free." Anyone telling you LLM-driven development is free is either not measuring or not actually building.

## What that bought us

The same money in the same months, in the absence of the model partner, would have bought a fraction of the work. Here are the categories of work that I genuinely could not have produced solo at this rate.

**A protocol specification with accompanying examples and test fixtures.** Drafting the spec required many rounds of "here is the constraint, here is the field, here is what the field means, here is the validation rule." The model did not write the spec — I did, in collaboration — but the long tail of "for each of these 30 fields, generate a positive and negative test fixture, then a JSON-schema validator, then a parser, then a serializer" is exactly the kind of repetitive elaboration the model is good at and humans are bad at staying patient with.

**A hundred-plus single-file plugins with consistent shape.** I wrote a few canonical plugins by hand to establish the shape. The rest were generated, with my architecture and the model's drafting, then tested. Each plugin's quality is dictated by my review. The aggregate volume is what would otherwise have been impossible.

**SDKs in five languages with consistent semantics.** I designed the SDK shape once. The model produced four ports, in idiomatic style for each target language, with tests. I reviewed each port for fidelity to the canonical version. The languages I do not work in daily — the ones where I would have spent days re-learning the conventions — are where the partnership saved the most time, because the model already knows the conventions.

**Documentation written alongside code.** Every feature shipped with documentation that was written in the same session as the code. This is the part of solo development I would have skipped or deferred. With the model, the documentation lands at the same time as the code, because it is cheap to ask for and the model already has the context.

**Long-form blog posts.** Most of the writing in those 120 posts is mine — voice, argument, structure, edits. The model is a drafting assistant, an outliner, a reference for technical phrasing, a suggester of titles and openings. The boost is specific: I write roughly twice as much in the same time as I would otherwise, because I no longer get stuck at the staring-at-the-blank-page step.

## What it did not buy

The token bill bought capacity. It did not buy magic. Three categories of work remain unchanged from "doing this without a model."

**Architecture decisions.** Every major shape of the system — what the unit of distribution is, what the deployment model is, what the data layer looks like — came out of my head. The model is a sounding board, not an architect. When I pretended otherwise, the system got worse, fast.

**Debugging unfamiliar systems.** When something failed in a part of the stack I did not know well — a serverless cold-start oddity, a TLS misconfiguration, an obscure DNS issue — the model was helpful as a search engine and bad as a debugger. The work of "form a theory, test it, refine it" stays human work. The model can read logs back to me, but it cannot remember which theories I have already ruled out.

**The hardest 5% of any feature.** Every feature has a part where the design has to be exactly right, and where the consequence of getting it wrong is months of cleanup. That part is mine. The model writes the easier 90% to specification; I write the part where the specification is uncertain.

## The hour bill

Tokens are easy to measure. Hours are harder, but I tracked roughly.

About 600 hours over five months. Not 600 hours of "typing code." 600 hours of "working on the project" — design conversation, prompting, review, testing, debugging, deploy, post-mortem. Roughly a quarter-time job, alongside the day job and the rest of life.

Of those 600 hours, my best estimate of the breakdown:

- ~240 hours in design conversation with the model. Phase one of the workflow. Where the architecture happens.
- ~180 hours in code review and integration. Reading the model's output, deciding what to ship, fixing what is wrong.
- ~120 hours in writing, editing, and prose work. Posts, documentation, spec text.
- ~60 hours in deployment, operations, and post-mortem.

The shape that surprises me, looking back, is that **less than a third of the hours was spent in active code review.** The bulk was design conversation and writing. The model is most expensive when you let it generate without a tight design upstream; it is most cost-effective when you put in real architecture work first and then ship that architecture in small chunks.

## What it cost me other than money and hours

A few things I did not predict.

**Decision fatigue.** Every model session that produces output requires a decision: ship, edit, reject, redo. With dozens of these per day, decision fatigue is real. The mitigation is to batch by feature: do all design first, then all execution, then all review. Mixing modes mid-session is exhausting.

**Calibration drift.** Without a deliberate cross-check, you start trusting the model's output more than you should. I had to deliberately introduce checks — pasting outputs into a fresh chat to "review for issues," running tests aggressively, sometimes asking a different model to evaluate the same code — to keep my calibration honest.

**Time on prompt engineering.** I spent more time than I expected refining prompts and constraint documents. Worth it. Each refinement compounded across many sessions. But it is real time, not free.

**Context-window thrashing.** Long sessions on large codebases hit the context window. Then you have to summarize, recompress, or restart. Each restart loses context the new session has to be re-told. I underestimated this cost early; I now plan for it explicitly by snapshotting key constraints into a constraints document the model loads at the top of every session.

## The mistakes I made along the way

Three patterns where I lost real time. Naming them so you can avoid them.

**I let the model generate without an architecture for the first month.** I thought the model could "figure it out." It cannot. It can implement what you described, faithfully and quickly. It cannot decide what to build. The first month produced more code than I shipped from any subsequent month — and a much smaller share of it survived. The deficit between "code generated" and "code shipped" was the architecture I had not yet done.

**I wrote constraint documents too late.** The constraints I now load at the top of every session — "use this helper, not raw file writes; use the existing pattern, not new patterns; do not introduce dependencies" — should have existed by week two. They did not exist until month three. Every session before the constraint documents existed was paying the tax of re-explaining the basics.

**I tried to do too much in single sessions.** Big sessions with many features get worse outputs than small sessions with one feature each. The token cost is the same; the context degradation is steep. The fix is to be aggressive about scoping a session to one thing, and starting fresh between things.

## What I would tell someone planning a similar run

Three pieces of advice, in priority order.

**Budget around $1,000 in tokens for a five-month project of moderate ambition.** Not "free." Not "tens of thousands." Roughly the cost of two days of a contractor's time, spread across the build. If you are hesitating to spend that, do not start; the model bill will come.

**Plan for 600 hours of human time on top of that.** The model accelerates work; it does not replace it. If you do not have the human hours to put in, you do not have the project.

**Spend the first week on architecture and constraint documents.** They are the highest-leverage work you can do. Every session afterwards is cheaper, faster, and produces more shippable output because of them. Skip this and you will spend the first month re-doing it.

## The summary

Five months of building real software with an LLM partner cost roughly $1,000 in tokens, 600 hours of human time, and considerable decision fatigue and calibration discipline. The output was substantial — a complete production system, a protocol spec, multi-language SDKs, a hundred-plus plugins, a hundred-plus posts. The unit economics are favorable but not free. The qualitative experience is "I shipped at roughly two to four times the rate I would otherwise" — not the ten-times-or-more lift the marketing copy suggests.

If you are deciding whether to commit to a similar effort, those numbers should help calibrate. The investment is real. The return is real. The magic is mostly in the workflow, and the workflow does not invent itself; you build it. Plan for the real numbers and you will land where the receipts say you can.
