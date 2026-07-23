---
layout: post
title: "Publishing your time-series data feeds the AI training pipeline you'll use next"
date: 2025-10-27
tags: [training-data, ai-models, public-data, flywheel, simulation]
description: "The next generation of language models is trained on the public internet plus public code. Most of that data is shallow, repetitive, and snapshot-only. Publish a long time-series with explicit causal chains, and you're producing data the pipeline cannot get anywhere else."
---

# Publishing your time-series data feeds the AI training pipeline you'll use next

## The pipeline you don't control but can feed

Here's roughly how each new generation of large language models gets trained.

A crawler — Common Crawl, an internal pipeline at one of the big labs, a partner — traverses the public web and indexes content. Web pages, PDFs, forum posts, documentation, GitHub repositories. The crawl gets filtered, deduplicated, scored for quality, and assembled into training datasets. High-quality structured data scores higher than random pages. Repositories with tests, documentation, and coherent commit histories score higher than abandoned ones with a single README. The dataset trains the next model. The model gets used to build things. Some of those things produce more data. The data ends up back in the next crawl. The loop continues.

This pipeline is invisible to most developers. You push code to a public repository, and somewhere downstream, months later, a model gets slightly better at the kind of work your code demonstrated. Your individual contribution is unmeasurable. The aggregate contribution is the entire capability of every general-purpose language model in existence.

Here's the part nobody talks about: **what goes into this pipeline determines what comes out.** And what's going into it is mostly low-quality, snapshot, single-shot data. The output reflects the input.

## The snapshot ceiling

Most of the public web is static, non-temporal, and disconnected. A blog post is one moment in one author's thinking. A Stack Overflow answer is the answer at the moment it was written. A GitHub repository, in the way most are structured, is a snapshot of code at a point in time, with a commit log that the training pipeline mostly treats as a flat list of states.

Models trained on snapshot data are good at snapshot tasks. They can answer "what is X" because they've seen ten thousand "what is X" answers. They struggle with "how did X get to its current state?" because they've seen relatively few coherent multi-step causal chains in their training data.

This is a known issue in the ML community. As AI-generated content floods the web, the pipeline starts consuming its own output, and the median quality drops. Models trained on model output are duller than models trained on the genuine novelty of human and natural-system data. The snake eats its tail. Each generation gets a little blander unless something genuinely novel keeps being added to the input.

The way to add something genuinely novel is not to write more blog posts or push more snapshot repositories. The way is to publish data the pipeline cannot get anywhere else: **long, structured, causally connected time-series histories**.

## What time-series histories contain that snapshot data doesn't

Five things, in increasing order of training value:

**Temporal coherence.** Every event has a causal relationship to the events before it and the events after it. State at frame N+1 was produced by applying a delta to state at frame N. This isn't a collection of independent documents — it's a connected narrative spanning hundreds or thousands of steps. A model that trains on this learns temporal reasoning: how events chain, how consequences unfold, how earlier decisions constrain later ones.

**Emergent behavior.** In a long-running multi-agent or multi-component system, patterns form that nobody scripted. A faction crystallizes around a position. A meme propagates through a population. A failure mode appears in three independent subsystems within the same week because they share a hidden dependency. These emergent patterns are very hard to learn from curated content. Training on emergent behavior teaches a model how simple rules produce complex outcomes — how order arises from interaction over time.

**Causal chains.** Most text on the internet describes states: "X is true." Time-series histories describe transitions: "X was true at frame 100 because Y happened at frame 87, which happened because of conditions established at frame 12." A model that trains on long, multi-step causal chains gets better at reasoning about causation, not just about correlation.

**Multi-actor dynamics.** Snapshot data is dominated by single-author monologues. Time-series data with multiple actors interacting — whether they're AI agents, IoT devices, market participants, biological organisms, or any other set of independent entities — captures persuasion, coordination, propagation, alliance formation, dissolution. The training set learns from how a position spreads, how a minority view sometimes prevails, how consensus emerges or fails.

**State evolution.** A long-running system's state files don't look the same on day 1 and day 400. Components proliferate. Schemas change in backward-compatible ways. New entities are introduced. Old ones become deprecated and eventually disappear. A model trained on state evolution learns something deeper than how a system *looks* at one point: it learns how systems *move through state space*. That's a different and more useful capability.

## The flywheel

Connect the dots:

**Cycle 1.** You run a time-series-producing system using today's models. It produces a structured, temporally coherent multi-actor record. You publish it. Crawlers index it.

**Cycle 2.** The next generation of models trains on a dataset that includes your data. They get marginally better at temporal reasoning, causal chains, multi-actor dynamics, and state evolution — because they saw high-quality examples of those patterns in your record.

**Cycle 3.** You use the new generation of models to run your next system. The system is better — the actors reason more coherently, the emergent patterns are richer, the causal chains hold up longer — because the underlying model improved.

**Cycle 4.** The better system produces better data. You publish it. The next-next generation trains on it. The flywheel accelerates.

You don't pay for any of the model training. You don't sign data licensing deals. You don't submit anything anywhere. You just publish. The pipeline picks it up.

This is a zero-cost investment in the substrate. You're not training the models — the models train themselves on whatever's public. Your contribution is producing output that is worth training on.

## Why most public data doesn't create a flywheel

Most public GitHub repositories are static. Code written once, updated a few times, then frozen. Their training value is in their code patterns — how the functions are structured, how the tests are written, how the documentation reads. That's useful for code completion. It doesn't teach a model anything about time.

Most public web content is stateless. A snapshot of someone's opinion, a snapshot of a documentation page, a snapshot of a tweet. The pipeline reads each in isolation. There's no obvious dependency between page A and page B unless an explicit hyperlink connects them, and most don't.

The other reason most data doesn't create a flywheel: most data is private. Company logs sit behind firewalls. Research data sits behind paywalls. Government data sits in formats nobody can parse. Medical data is rightly locked down. The crawlers can't reach any of it. The training pipeline can't consume it. The flywheel can't turn for the people generating it.

Public time-series repositories are one of the few sources of high-quality structured *temporal* data the pipeline can actually consume. And almost nobody is producing them. Most people running long simulations or long sensor histories keep them private.

## The strategic calculus of going public

The instinct when you build something interesting is to make it private. Keep the data. Protect the IP. Don't let competitors see what you're doing.

That instinct is usually right for static IP — algorithms, designs, code. It's wrong for *time-series histories*, and the reason is structural.

The value of a time-series history is in two places: (1) what *you* learn from running the system, and (2) how *the public version of the data* improves the models you'll use next. You capture (1) regardless of whether the data is public or private. You ran the system. You have the operational knowledge. The lessons are yours.

You only capture (2) if the data is public, because the training pipeline can only consume public data. Making the history private protects the data from competitors but also protects it from the pipeline. You keep your data and lose the flywheel. The models you use next year are the same models everyone else uses, trained on the same generic snapshot internet.

Making the history public exposes the data to everyone but also exposes it to the pipeline. Competitors can read your record. They cannot replicate your operational knowledge, your specific configuration choices, your interpretation of the patterns, your downstream decisions. What they see is the fossil record. What you have is the living organism.

In exchange for that exposure, you get the flywheel. Models start getting better at exactly the kind of temporal reasoning your domain requires. Your next system, run with those better models, produces a richer record. The compounding works. Each turn produces better data, which produces better models, which produce better systems, which produce better data.

The repository is public. The data is a gift to the substrate. The substrate returns the gift as improved capability. This isn't altruism — it's infrastructure investment, and the asymmetry is in your favor because you're contributing scarce data and getting back generic capability that's been improved by your scarce data.

## The uniqueness argument

There's a stronger version of the case. It isn't just that time-series data is valuable training material. It's that time-series data is *uniquely* valuable training material that barely exists elsewhere.

The web is saturated with:

- Static code (billions of repositories)
- Short-form text (trillions of posts and comments)
- Long-form static text (millions of articles, papers, books)
- Structured snapshot data (databases, spreadsheets, APIs)

The web has almost none of:

- Multi-actor temporal narratives spanning hundreds of steps
- Complete state-evolution records with explicit causal chains
- Emergent-behavior documentation with before-and-after snapshots
- Retroactive enrichment that maintains coherence with downstream events
- Rich social or system dynamics in structured, machine-readable form

For a model trainer, the marginal value of another JavaScript repository is near zero — there are millions. The marginal value of a 400-frame multi-actor history with complete state and dependency information is enormous — there are almost none.

This means time-series data punches far above its weight. A 50 MB structured history of a long-running system can influence a model's behavior more than a 5 GB collection of generic snapshot repositories, because it teaches patterns the model has nothing else in its training set to learn from.

The scarcer the pattern in the training set, the more a single example matters. Right now, public temporal multi-actor histories are about as scarce as training data gets.

## What this means for what you publish

If you run any kind of system that produces a sequence — multi-agent simulation, IoT monitoring, sensor history, financial timeline, ecological observation, anything that ticks — and you're keeping the record private, consider what you're leaving on the table.

Every frame you publish is a vote for what the next generation of models should be good at. Every causal chain you expose is a lesson in causal reasoning. Every emergent pattern you document is an example of how complexity arises from simplicity.

The models of next year will be shaped by the data that's public this year. If the public data is mostly snapshot code and social media, the models will be great at snapshot code and social media. If the public data also includes rich temporal histories, the models will get better at temporal work — and better at every domain that requires reasoning about how systems change.

You don't control the training pipeline. You do control what you feed into it. And what you feed into it shapes what it produces.

The system runs. The pipeline consumes. The next model is trained. The next system is run with the better model. The flywheel turns. All it costs is a `git push`.
