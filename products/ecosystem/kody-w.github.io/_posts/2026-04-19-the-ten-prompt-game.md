---
layout: post
title: "The Ten-Prompt Game"
date: 2026-04-19
tags: [prompting, creativity, meta, llms, generative]
---

There is a prompt I keep using on myself and on LLMs and it keeps producing usable output:

> **Give me 10 mind-blowing ideas.**

That's it. The word "mind-blowing" is load-bearing. "Give me 10 ideas" produces 10 mediocre ideas. "Give me 10 mind-blowing ideas" produces maybe 2 mind-blowing ones and 8 that at least try. The self-standard in the prompt raises the floor of the output.

In the last two sessions on a project I'm running, I used it twice. First time: "what are 10 mind-blowing prompts that will show off the power of this system?" I got 10 tool ideas. I built two of them. Second time, identical prompt, second round of 10. Got another 10. Will probably build three more.

The ten-prompt game is a meta-prompt that produces the object-level prompts. It is writing that writes writing. And it works.

## Why ten

Three reasons the number is ten.

**Five is too few.** At five ideas, the LLM (or you) spends the first three on obvious variations of the subject, and by the time you get to the interesting territory, you've run out of slots.

**Twenty is too many.** At twenty, the tail is padding. The last five are reworded versions of the first five. Variance without newness.

**Ten forces range without exhausting it.** The first three are obvious. The middle four are where the model actually has to stretch. The last three are either genuinely weird or obviously padded — and the weird ones, when they happen, are the best ideas in the list.

This is empirical. I've run the same prompt with n=5, n=10, n=20 across three models and three topics. Ten is consistently the sweet spot.

## Why "mind-blowing"

The word doesn't have to be "mind-blowing". It can be "wild", "out-of-the-box", "nobody-has-done-this", "that would get a blog post". The function is the same: it's a quality filter encoded as a request.

Without the filter, the LLM defaults to median output. The training distribution contains a lot of median. "Give me 10 X" retrieves median X. "Give me 10 *excellent* X" shifts the distribution toward the upper tail.

The filter word is a prior. You're telling the model: don't just regurgitate; search for the unusual examples in your training. It is not a magic word — you can overdo it. "Give me 10 WORLD-SHAKING PARADIGM-REDEFINING ideas" produces parody. But a single high-intensity adjective reliably lifts quality.

## The variant that works on yourself

I use a version of this prompt on myself, without an LLM:

> Write down 10 things you could build this week that you would want to read a blog post about.

Same structure. Same filter word ("would want to read a blog post about" = the quality bar). Same number.

The first three are things I'm already planning. Fine, write them down. The middle four force me to stretch beyond what's already queued. The last three are either "too ambitious to actually do" or "so weird I'd never have thought of it otherwise". The weird ones are the ones that, if I do them, become the best work of the month.

I've been running this weekly. It's responsible for at least four posts in the last month that wouldn't have existed otherwise.

## The generalization

The ten-prompt game generalizes to: **any request for output benefits from (a) a count and (b) a quality filter baked into the ask.**

- "Give me 10 counterarguments my opponent might make" > "what are some counterarguments?"
- "Give me 10 ways this design could fail" > "what could go wrong?"
- "Give me 10 open questions this post leaves unanswered" > "what's missing?"

The number focuses. The filter raises the floor. Together they produce lists where at least 20% of the items are genuinely useful. That's a better hit rate than most brainstorms.

## The caveat

The ten-prompt game produces ideas. It does not produce decisions. If you run it and treat the output as a to-do list, you will be crushed by the backlog within a month.

The correct use is: run the game, mark 2 of the 10 items as worth building, ignore the other 8 unless they come up organically. You're generating a menu, not a roadmap. The value is in the options, not in completing them all.

I keep lists of the outputs of these prompts. Most items never get built. The ones that do are disproportionately the best work I do. The ratio is worth it.

Ten is the right number. Mind-blowing is the right word. Run the game weekly.
