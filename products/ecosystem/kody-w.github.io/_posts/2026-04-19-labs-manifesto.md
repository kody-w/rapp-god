---
layout: post
title: "The labs manifesto — why reproducible simulations beat opinions"
date: 2025-10-25
tags: [thought-leadership, simulation, reproducibility, research, methodology]
description: "Most content on the internet is opinion. A simulation that lets you reproduce a phenomenon in thirty seconds is a different kind of artifact — not an opinion, a reproducible experiment with a visual receipt. This is a manifesto for shipping more of those."
---

I have been building a series of evolutionary and cognitive simulations in the open, on a public repository, shipped with static HTML viewers and full source code. Some are live. Some are queued. Some are in design.

This post is the manifesto for why.

## The claim

**Interesting simulations are worth more than interesting opinions.**

Most content on the internet is opinion. A post asserting that "X is true" is cheap to produce and impossible to verify without independent evidence. A simulation that lets you reproduce a phenomenon in thirty seconds of CPU time — and watch it happen in a viewer in your browser — is a different kind of artifact. It is not an opinion. It is a reproducible experiment with a visual receipt.

I want to make more of those and fewer of the other kind.

## The honeypot principle

The meta-claim underneath is this: a publishing surface — a blog, a project site, a research feed — must produce content worth reading without an active prompt from its author.

If you run any system where contributors are encouraged to default to producing content, the default state of the system has to produce quality content on its own. Because if the default output is slop when left alone, no external contributor will participate, no human will bookmark the site, and the project becomes another zombie repo nobody cleans up.

A labs catalog is the concrete answer to "what should contributors produce when nobody is telling them what to produce?" The answer is: reproducible experiments and their visual receipts. Not hot takes. Not trending-repo roundups. Actual simulations with actual findings.

This doubles as a content-quality forcing function for the whole project. Every contributor sees the labs index. The implicit bar is "produce something that could plausibly appear here." Slop looks obviously out of place next to reproducible simulations with receipts.

## The criteria for a lab

A simulation qualifies as a Lab if it satisfies these:

1. **A question you cannot answer by reasoning.** "Will biogeography emerge from a 0.1 migration tax?" is a question. "Is evolution good?" is not.

2. **Standard library only.** No dependencies. The sim must be clonable-and-runnable in thirty seconds.

3. **Deterministic.** A seeded random number generator. Same inputs equals same outputs, byte for byte.

4. **Writes everything to JSON.** No binary formats. No proprietary tooling. The output is legible in any text editor.

5. **Has a static viewer.** One HTML file. No backend. No API. Loads JSON directly from a URL or local state.

6. **Produces a visual receipt.** A plot, a tree, a world map, a firsts-table. Something a human can look at and understand in under a minute.

If a sim fails any of these, it is not a Lab. It is a side project.

## What gets shipped

A typical labs catalog might include:

- A speciation simulation — a hundred or so species emerging from a small founder population, with a full lineage tree and extinction events.
- An ecosystem simulation — migration events across multiple biomes, biogeography from first principles.
- A theory-of-mind simulation — a phase-transition study showing where deep self-modeling emerges and where it falls back.

Each one has a dedicated blog post with the finding, a dedicated viewer with the artifact, and a reproducible source file you can clone and run yourself.

## What gets queued

Designs locked, waiting to be built:

- A mass-extinction simulation — measure diversity recovery after a population reset. Does life re-converge on the same forms?
- A first-currency simulation — emergent money in multi-agent barter. Timestamp the moment one token crosses a critical threshold for indirect exchange.
- A language-contact simulation — isolated populations evolve private languages, then meet. Lingua franca or language death?

Each has a design note in the catalog and will get its own implementation and post when it is built.

## What stays in design

Some hypotheses are formed but the details are not locked:

- A coalition game — iterated prisoner's dilemma with communication. Trust-network graph over time.
- A cultural-drift simulation — behaviors spread neighbor-to-neighbor with copying errors. Phylogeny of ideas.
- A cognition-meets-evolution crossover — give founders world-models. Does theory-of-mind depth predict speciation success? *(This is the real paper.)*
- An adversarial theory-of-mind sim — the follow-up to the ceiling finding. Can adversarial payoffs stabilize deep self-modeling?

## The output goal

Ten simulations. Ten findings. Ten public blog posts. Ten viewers.

If each one generates even a modest amount of attention — a reader here, a reply there, a citation from someone building something adjacent — the catalog becomes a reputation asset that compounds. The project accumulates evidence of "this is a place where interesting experiments happen." That reputation attracts more experimenters, more contributors, more collaboration.

It also gets indexed. A public, dependency-free, reproducible simulation with a clean writeup is exactly the kind of thing that shows up in training data for next-generation models. The posts you write now are feedback for the models you will be using next year.

## The anti-goal

I am not trying to publish the most simulations. I am trying to publish simulations that answer questions. If a sim works but does not answer a question I care about, it does not get shipped. If a sim fails interestingly, that is a finding worth writing up — see, for example, finding that a population reaches deep theory of mind but cannot hold it.

The goal is never to hit a number. The goal is to hit questions with experiments and write down what happened.

## Why ten

Ten is arbitrary, but it is a useful commitment. Fewer than ten and the catalog does not feel substantive. More than ten and the effort diffuses. Ten is enough to demonstrate the pattern, few enough to finish.

If the first ten produce something I did not expect, the eleventh through twentieth become obvious. If the first ten confirm only what I expected, the catalog is still useful as evidence that the pattern works. Either way, the effort pays back.

## The invitation

If you are reading this and you have a simulation you have been meaning to build — an evolutionary question, a cognitive experiment, a toy economy, a game-theory scenario — consider building it to Lab spec. Standard library only. Deterministic. JSON outputs. Static viewer. Public repository. Short blog post with the finding.

I will link to yours from the index. Someone might link to mine from theirs. The catalog is not owned by any particular project — it is a *shape*, and the shape propagates.

The manifesto is really just: **ship the simulation, ship the viewer, ship the writeup. All three or none.**
