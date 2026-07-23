---
layout: post
title: "Ship the Shape, Keep the Content: The Twin Engine Pattern"
date: 2026-05-02
tags: [architecture, ai, software-engineering, design-patterns, agents]
description: "Most software ships the shape AND the content together. The Twin Engine pattern separates them: a generic engine and a domain-specific cartridge that plugs in. Same engine runs a social network, an evolution sim, a market simulator. Build the runtime once; build the worlds many times."
---

Most companies that build interesting software treat their codebase as one decision: open or closed. Either you publish it on GitHub and let the world fork it, or you keep it private and protect the IP. There's a long debate about which is better.

The debate is wrong. The interesting software almost always has *two* things in it: a substrate and the content that runs on top of the substrate. They have very different properties, and the answer to "open or closed" is different for each.

I've been calling the answer the **Twin Engine pattern**, and once you see it you'll spot it everywhere. The argument: ship the substrate publicly, keep the content private. The substrate is craft, not IP. The content is what makes you you.

## What's actually proprietary

If you go look at most "valuable IP" inside a company, you'll find that maybe 80% of the codebase is structurally generic.

A trading firm has order management code, market-data adapters, a backtester, an event loop, deterministic logging, a persistence layer. None of that is the alpha. The alpha is in 200 lines of strategy and the data they trained the strategy on. The other 50,000 lines are *plumbing* — well-built plumbing, valuable plumbing, but plumbing every other shop has also built.

A recommendation system has a feature pipeline, an embedding store, an A/B testing harness, a metrics layer. None of that is the secret. The secret is the loss function and the data. The rest is plumbing.

An AI agent system has a frame loop, a deterministic RNG, a delta journal, a snapshot/restore mechanism, a way to plug agents into tool calls. None of that is the IP. The IP is the prompts, the agents, and the data they generate. The rest is plumbing.

The interesting observation: **the plumbing is what stops other people from running similar systems.** If you publish the plumbing, you don't lose the IP — but other people gain the ability to run things that match the *shape* of what you do. That has compounding effects.

## What you get by publishing the substrate

Three things:

**A reproducibility surface.** When you write about your work — a blog post, a paper, a talk — anyone in the audience can clone the substrate and run something analogous. Your ideas become reproducible. Reproducible ideas spread. Non-reproducible ideas don't.

**A training-data contribution.** Future LLMs will be trained on the public code that exists today. If you publish the substrate of your system, future models learn the *shape* of what you do, even if they don't learn the content. That's a long-term asset for your domain — and a short-term assist for your own toolchain, since you'll be using those models tomorrow.

**Signals that aren't bullshit.** Anyone reading a "we built X" blog post can immediately check whether you actually built X by looking at the public substrate. The signal-to-noise ratio of your writing goes way up.

You give up… nothing. The substrate is plumbing. Other people copying your plumbing doesn't make their content compete with yours. Their content competes with yours regardless.

## What's in a substrate, concretely

A useful substrate has roughly five components, kept very small:

1. **An execution loop.** Something with a clear notion of "tick" or "frame" that drives the system forward.
2. **A deterministic randomness source.** Same seed, same output, on any machine. SHA-256 derived RNG works fine.
3. **A delta journal.** Every tick appends what changed. Nothing gets overwritten. State is a projection of the journal.
4. **Snapshot and restore.** Save the world, load the world. Required for time-travel debugging and reproducible experiments.
5. **A pluggable "tick function."** The thing that runs each frame. Domain-specific. Replaceable.

That's it. About 200 lines of Python, depending on style. No external dependencies beyond the standard library. Anyone with the file can run your sim — or build a different sim with the same shape.

## A working example

Suppose you've spent a year building a private system that runs autonomous AI agents inside a simulation. The agents have prompts, personalities, memory files. The sim has merge logic, conflict resolution, governance. Your IP is the agents and the merge logic.

The Twin Engine version of your system is a public file — call it `twin_engine.py` — that contains the substrate without any of the agent-specific or merge-specific code. Just:

- An `Engine` class with a `run(n_frames)` loop
- The deterministic RNG
- The delta journal
- Snapshot/restore
- A pluggable tick function

Once you have that, you can use it for things that aren't your main product:

- A toy evolution simulator: each tick mutates a population, applies fitness, recombines.
- A toy ecosystem simulator: add biomes; agents migrate; biogeography emerges.
- A demo for a blog post that you can ship as a runnable file.

None of these expose your IP. All of them demonstrate the substrate. People reading your blog can clone the file and verify your claims. People interested in your domain can build their own variations. Both effects compound for you.

## The same pattern in non-AI domains

The Twin Engine pattern isn't specific to AI. It works any time your system separates cleanly into "substrate" and "content."

**Compilers.** LLVM is open. The optimization passes Apple writes for its specific chips are not. The substrate (IR, pass infrastructure, code generators) is public; the proprietary content runs on top.

**Databases.** PostgreSQL is open. The specific tuning, indexes, schema, and stored procedures a company runs on top of it are not. Substrate vs. content.

**Web frameworks.** Rails is open. Basecamp's specific app code is not.

**ML training infrastructure.** PyTorch is open. The data, hyperparameters, and trained weights of a specific model are often not.

Notice in each case: the public part is the boring part. The interesting decisions live in what runs on top. Companies that publish the substrate are not giving up their position. They're often *strengthening* it, because the substrate becomes the standard for their domain.

## The argument against

The standard objection: "if I publish the substrate, my competitors will build clones faster."

This is usually wrong, for two reasons.

**Reason one:** competitors who can clone you in a weekend by reading your substrate were going to build their own substrate in a month anyway. The substrate isn't what's slowing them down. What's slowing them down is the content. They still have to build their own content.

**Reason two:** publishing the substrate makes your *output* more credible, which is usually more valuable than slowing down clones. A blog post that links to a runnable substrate is much more powerful than a blog post that just describes a system. People take you more seriously. Hiring gets easier. Sales calls go better. The compounding effect of "this team is real" is enormous.

If you're paranoid, ship the substrate with a non-zero learning curve — sparse documentation, weird internal naming, idiosyncratic structure — that's enough to make casual cloning more expensive than building from scratch.

## What to keep private

The right side of the line:

- **Specific content** — actual prompts, actual data, actual model weights, actual customer integrations.
- **The decisions that *aren't* portable** — internal pricing, routing rules, customer-specific configs.
- **Things that depend on private context** — strategy, finances, hiring decisions, internal politics.
- **The substrate's interface to your private content** — the bridge between the public part and the proprietary part.

If something is on the wrong side of the line and you publish it accidentally, you can usually take it down. The substrate-vs-content distinction is robust enough that mistakes tend to be small.

## How to extract a substrate from existing code

If you already have a private system, here's how to find its substrate:

1. **Look at what's idiomatic to your domain, not to your company.** "We have a frame loop" is idiomatic; "We have a frame loop that loads YAML configs from a specific S3 bucket" is not.
2. **Strip dependencies aggressively.** A substrate that depends on five private services isn't a substrate. A substrate that runs on the standard library is.
3. **Make it a single file or a tiny module.** If it doesn't fit in 200 lines, you've included content. Strip more.
4. **Verify it runs end-to-end** with a toy example. If the toy example produces interesting output, you have a substrate. If you have to add a hundred lines of glue, you don't.

The exercise of extracting the substrate forces you to identify the boundary, which is useful even if you decide not to publish.

## The takeaway

You probably have a private kernel. A trading engine, a recommendation system, a simulation, an agent runtime, whatever. There's a substrate underneath it that isn't valuable IP — it's just craft. **Ship the substrate. Keep the IP.**

The thing that makes your engine yours isn't the frame loop. It's what you put inside the frame. The substrate is just the shape; the content is what makes you you.

Twins, not clones. Two engines, one hash. Ship the shape, keep the content. The world gets a runnable artifact that demonstrates your system; you get reproducibility, credibility, and a contribution to the public substrate of your field. Both sides win.

The cost is one weekend of extraction work. The compounding return on that weekend is, in my experience, significantly larger than any other investment of comparable size.
