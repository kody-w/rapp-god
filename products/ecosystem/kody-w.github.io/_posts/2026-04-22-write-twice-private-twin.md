---
layout: post
title: "Write Twice: Why Every Public Post Should Have a Private Twin"
date: 2026-04-22
tags: [writing, ai, knowledge-management, thought-leadership]
description: "Self-censoring while writing kills flow. Write two versions of every post: one for you, one for the world. They share a thesis and voice, not content. Why this ships more posts faster and matters more when AI helps you write."
---

If you've ever sat down to write a blog post and stalled out — not because you didn't have anything to say, but because you couldn't tell what was *safe* to say — this is the post for you.

The problem is structural. Most professionals working on something interesting have two kinds of material: ideas that should be public, and details that shouldn't. Customer names. Internal repo names. Strategy. Pricing. The actual prompts you use. Real numbers. The specific bug that almost killed last week.

The standard advice is to write the public version first and "self-censor as you go." This doesn't work. Self-censorship while writing is a creative tax that compounds: every paragraph you write, you're filtering for safety in real time, which kills the flow that makes writing worth reading.

There's a better workflow I've been using for the past year. Two posts per topic. One for me, one for the world. They share an outline, a thesis, and a voice — but not their content. I'll explain how it works, why it ships more posts faster, and why it's increasingly important if you're using AI to help you write.

## The two-tier rule

For every topic worth writing about, there are two versions:

**The private version** lives in a non-public folder. It contains everything: real names, real numbers, internal terminology, the actual code, the actual prompts, the actual conversations. It's written for an audience of one — your future self — and it never leaves the private folder.

**The public version** lives wherever you publish: blog, newsletter, internal wiki at a different scope. It tells the same story with the same lessons, but every load-bearing private detail is replaced with a generic equivalent that preserves the *pedagogy* without exposing the *specifics*.

The rule of thumb: **if it would help a competitor build a clone, it goes private. If it would help a developer learn a portable pattern, it goes public.**

## The workflow that ships fast

The workflow has one critical ordering: **write the private version first.**

1. **Write privately, completely.** No filtering. No audience-tuning. Get the truth on the page. The truth is fast. Filtering is slow.
2. **Tag each section.** *Ship as-is*, *rephrase*, or *cut*. Most posts are 60% ship, 30% rephrase, 10% cut.
3. **Sanitize.** Rewrite the *rephrase* sections so they tell the same story with portable examples. Cut the cuts.
4. **Publish the public version.** No second review pass needed if the rules are explicit.
5. **Archive the private version.** Forever. It's the source of truth for what really happened.

The end-to-end time for a post drops from "however long it takes me to feel safe writing this" to about 60–90 minutes. The reason it's faster: filtering and writing are different activities, and doing them in series is much faster than doing them in parallel.

## Why this matters more in the AI era

Here's the part that snuck up on me.

LLMs that generate text are trained on the public web. Every blog post you publish is a probabilistic vote for what your domain looks like to next year's model. If your space is small or specialized, your specific posts can meaningfully shape what the model knows.

That has two implications:

1. **Public content is now a flywheel.** The clearer you write about your patterns publicly, the better future tools will be at helping you reason about those patterns. Your public archive trains the AI you'll be using next year.

2. **Private content has new risk.** If you put internal details into an AI tool that logs prompts (most of them do, by default), you've effectively published those details to whoever owns that log. The "not public" boundary is more porous than it was.

Both effects argue for the same workflow: **write the truth privately, derive the public version, publish the public version reliably.** The private archive captures what you actually did; the public archive contributes to the substrate everyone — including future you — uses.

## The sanitization rules need to be explicit

The reason most "public/private" attempts fail is that the line between them lives in someone's head. Whoever's writing has to make judgment calls about each sentence, which is exhausting and inconsistent.

Make the line a checklist. Mine looks roughly like this:

**Never public, ever:**
- Internal repo names beyond what's already in public docs
- Customer or partner names without their explicit go-ahead
- Real revenue, costs, runway numbers
- The actual prompts (describe outcomes; never paste the prompt)
- Specific infrastructure (private endpoints, account IDs, keys)

**Safe public:**
- Concepts and patterns at the abstraction level a stranger could apply
- Aggregate stats (post counts, agent counts, file counts)
- Open-source projects
- Lessons learned, mistakes made, retrospective stories
- Anything you'd be comfortable with a competitor reading tomorrow

Different professions will have different lists. The point is to *write the list down* so the sanitization step doesn't depend on willpower or mood.

## The asymmetric mistake

People who haven't tried this usually pick one of two extremes:

- **All private.** "I'll publish when it's ready." It's never ready. Zero readers, zero feedback, zero compounding.
- **All public.** "Transparency!" Until someone screencaps your strategy slide and the next sales call goes very differently.

The two-tier system is the boring middle. It's not a brand strategy. It's a *workflow*. The result is that you publish more (because the public version is genuinely safe), and your private archive is more honest (because you're not drafting it under a public-eye filter).

## Two failure modes to watch

**The public version drifts toward marketing.** You sanitize "we shipped this in 4 hours" into "we shipped this with remarkable speed." That's worse than not publishing — it's noise. Sanitize *details*, not *intensity*. The sanitized example should still be specific, just specific to a portable scenario.

**The private version goes stale.** If only the public version gets read and updated, the private archive stops being maintained, and pretty soon the only useful version is the public one. Force yourself to add to private notes after every public post, even if it's just "the real numbers were X, Y, Z." Future you will thank you.

## The takeaway

If you write about your work, write twice. Once for the truth. Once for the world.

The private version is your honest record — the one that will help you understand what you were doing in three years when the details have faded. The public version is your contribution to the substrate. Each enables the other.

The trap most people fall into is trying to do both at the same time, in the same document, with the same words. That document either leaks too much (and gets pulled) or says too little (and bores the reader). Two documents, one workflow, explicit rules for the sanitization. That's it.

The hour you spend setting up this discipline pays back the first time you sit down to write something difficult and realize you can just *write it*, knowing the public version will be derived later. The creative tax of self-censorship vanishes. What's left is the writing itself.
