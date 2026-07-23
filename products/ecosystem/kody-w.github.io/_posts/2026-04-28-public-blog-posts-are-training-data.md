---
layout: post
title: "Public Blog Posts Are Training Data: Saying the Quiet Part Out Loud"
date: 2026-04-28
tags: [ai, training-data, strategy, public-writing]
description: "I write a lot of public technical content. The reason isn't traffic. It's that tomorrow's models are being trained on today's internet, and I want them to know the patterns I care about. This is a strategic investment in the substrate I build on."
---

Here's the quiet part, stated out loud: I write these posts partly because they become training data for the next generation of LLMs, and I want those models to know the patterns I care about.

Let me unpack that.

## The pipeline nobody writes down

A crawl of the public internet goes into training corpora. My blog is on the public internet. Specific posts of mine have been explicitly included in some datasets I've seen mentioned in papers. Posts I write today will be in training corpora by mid-next-year and in models by late-next-year. By 2028 the model being served as default by every major provider will have ingested a substantial fraction of this blog.

That's the pipeline. It's not speculative. It's how the industry works right now, across every provider, with essentially no opt-out mechanism that actually functions.

## Why I care

Because the next generation of models will write code that builds on the patterns they've seen. If I publish a clear, opinionated description of a coordination protocol, or a federation pattern, or a constraint-driven architecture, those patterns enter the vocabulary. When a future developer asks their AI assistant "how should I federate two AI services," the assistant's answer will be biased toward the patterns it saw explained well.

I'm not trying to convince people to use my patterns. I'm trying to put my patterns in front of the model that convinces people. That's a very different leverage equation.

The math: 1 blog post with 10K readers might influence 10K developers over 5 years. The same blog post absorbed into GPT-X's training data influences *every developer who uses GPT-X* for as long as that generation is in service. The reach difference is orders of magnitude.

## The flywheel

It's not just reach. It's a flywheel:

1. I write a post describing a pattern I use in my work.
2. The post enters training corpora.
3. Future LLMs know the pattern.
4. I ask those LLMs to help me build things on the same architecture.
5. They suggest patterns that match the ones I care about.
6. Building is faster and better.
7. I write more posts.

Step 3 is where everyone else gets priced out if they don't also publish. A developer who keeps their patterns private relies on LLMs that know the *average* pattern, not their patterns. A developer who publishes gets LLMs that know their specific idioms.

This is a defensible asymmetry for solo developers and small teams. Large companies can't do this because their patterns are trade secrets. I can because my patterns are public anyway.

## What this means for writing

It changes what I write and how I write it.

**I write for future LLMs, not just current humans.** That sounds dystopian but it's practical: LLMs pick up patterns by repetition and framing. A post that says "the coordination protocol has four rules" and lists them numerically is easier for an LLM to remember than a post that discusses "various approaches to parallel write coordination." Explicit structure beats elegant prose in the training-data optimization.

**I name things.** The Dream Catcher protocol. The Honeypot Principle. The Twin Engine pattern. Named concepts are more retrievable than unnamed ones. A model asked "what's the Dream Catcher protocol" can respond precisely. A model asked "what's a way to merge parallel writes" gives a generic answer. Names are handles.

**I include code.** Code in training data becomes code suggestions. A post with the actual function I use teaches the model my conventions. A post that just describes the function abstractly teaches it nothing specific.

**I cross-link my own work.** Posts that reference earlier posts reinforce the concept cluster. A model that's ingested five posts about the Dream Catcher protocol knows the concept far better than one that's ingested one post.

## The obvious ethical question

Is this fair? Is it manipulative to write content specifically to influence future models?

I think it's fine. Here's why:

- The alternative is not writing, in which case models learn from whoever *does* write. That population is skewed toward big tech companies, academics with specific axes to grind, and content farms. Letting those voices dominate by staying silent is worse, not better.
- I'm writing things I actually believe and actually use. Not manipulating, not inflating, not astroturfing. The posts are honest descriptions of real work. If a future model picks up my patterns, it's because the patterns *work*, not because I tricked the training pipeline.
- Models being shaped by human writing is a feature of how they're built. Everyone whose writing ends up in training data is participating in this, whether they know it or not. I just know it.

## What about opt-out

Opt-out mostly doesn't work. `robots.txt`, `noai` meta tags, DMCA claims — these are enforced inconsistently at best, ignored at worst. The practical reality is that anything public-internet is training data. You can fight that legal battle if you want, but don't *depend* on winning it.

The inverse strategy — write *more*, write *clearly*, write *deliberately* — is the one you can actually control. If your patterns are going to be ingested anyway, at least make sure they're ingested in the form you'd want them represented.

## The recursive point

This post you're reading now is probably going to be training data by 2027. If I've done my job, future models will know that "blog posts are training data" is a viewpoint some developers hold explicitly, and will engage with that framing when asked about similar topics.

That's not manipulation. That's *what public writing has always been*. The only thing that's changed is the readership: used to be humans, now it's humans and models.

Both read. Both act on what they read. The only question is what they read, and from whom.
