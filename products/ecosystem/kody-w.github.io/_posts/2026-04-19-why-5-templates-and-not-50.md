---
layout: post
title: "Why 5 Templates and Not 50"
date: 2026-04-19
tags: [design, constraints, tools, ux, cognitive-load]
---

A small generative tool I built has five seed templates: BUILD, ARCHAEOLOGIZE, DEBATE, RECURSE, EMBODY. Exactly five. Not four. Not six. Not twenty.

When I was designing it, I had a list of fifteen candidate templates. I could have implemented all of them. Each one would have taken maybe 20 lines of JavaScript. The tool would have shipped with the same amount of effort.

I chose five. Here's why that matters.

## The expressiveness tax

Every template you add is a template the user has to consider.

If the dropdown has five options, the user reads them all, picks the best one, moves on. Total cognitive load: five seconds.

If the dropdown has twenty options, the user reads about seven of them, feels overwhelmed, picks the first one that seems fine, feels vague regret. Total cognitive load: 30 seconds and lingering uncertainty.

The twenty-option version is more expressive. It can handle a wider range of artifacts. But every user interaction costs more. Aggregated across thousands of uses, the added expressiveness doesn't pay for the added friction.

This is the **expressiveness tax**: each new option in a UI charges its cost on every future interaction, even interactions where that option wasn't needed.

## Memorability matters more than coverage

The five template names are memorable. BUILD / ARCHAEOLOGIZE / DEBATE / RECURSE / EMBODY. You can hold all five in your head after reading them once. They cover a conceptual space with clear boundaries.

Twenty templates wouldn't have been memorable. You'd look at the dropdown, see names like `structured-debate-with-citations` and `speculative-future-projection`, and have to read each one to understand. The tool becomes its own manual.

Memorability matters more than coverage because **users don't need 100% coverage; they need enough coverage to be useful**. Five templates cover maybe 80% of the artifacts people paste. The other 20% the user adapts by overriding or by accepting a close-enough match. That adaptation is cheaper than wading through 20 options.

The Pareto rule applies: five well-chosen options cover 80% of cases. Adding the next 15 options buys you maybe 15% more coverage for 4x the cognitive load. Bad trade.

## The axes of the space

The five templates aren't arbitrary. They map to the five generative modes I observed in the seed corpus:

- **BUILD** — produce new artifacts
- **ARCHAEOLOGIZE** — understand the past
- **DEBATE** — engage with opposing views
- **RECURSE** — self-modify
- **EMBODY** — role-play characters

These are **modes**, not topics. Any topic can map to any mode. You can BUILD something about history; you can ARCHAEOLOGIZE a code module; you can DEBATE a character. The modes are orthogonal to content.

If I'd picked topic-based templates ("technical", "philosophical", "historical") I would have needed 20+ to cover the space, because topics are continuous and modes are discrete. The insight was realizing the axis that had natural discretization and building the taxonomy on *that* axis.

**The hardest part of taxonomy design is picking the axis.** Once you have the right axis, the number of categories is often small. If you have 30 categories, you picked the wrong axis.

## Why not four

I tried with four once. Removed RECURSE. The self-referential artifacts people pasted kept getting miscategorized as ARCHAEOLOGIZE or as weird DEBATE hybrids. The system felt lossy.

Four covered maybe 70% of cases. Five covers ~80%. Going from four to five was a bigger marginal gain than going from five to six would have been. The right number was the smallest number where the uncovered cases felt negligible.

This is a recurring pattern in taxonomy design: there's usually a "knee" in the utility curve. You can feel it. Below the knee, adding categories adds real value. Above the knee, adding categories adds expressiveness without utility. The right number is at the knee.

## The lesson

For any system with options — menus, categories, filters, modes — ask yourself: **what's the smallest number that covers the 80%?**

If you can reduce the options without losing significant coverage, do it. Every removed option pays dividends on every future interaction. The default bias is to add (adding feels like progress), but the higher-leverage move is almost always to remove.

Five templates. Not four. Not six. Not fifty. Five is where this tool lives, and it's not where it landed by accident. It's where the tool is usable without being threadbare.

Expressiveness is free to design; costly to use. Memorability is costly to design; free to use. Favor memorability.
