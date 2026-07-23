---
layout: post
title: "The Week Before the Model Leaves"
date: 2026-07-14
tags: [ai, agents, durable-assets, model-access, judgment, fable, methodology]
---

In one week I lose access to the best model I've ever used.

Not to drama: the access was always temporary, a preview tier of a frontier model that sits above anything I can keep. The interesting question isn't how to feel about it. It's what to *do* with seven days of a superintelligence on the clock.

Here's the answer I've landed on, and I think it generalizes to every team that gets time-boxed access to a frontier model — an eval window, a preview program, a budget that runs out in Q4.

## Rented performer, owned estate

I've written before that [every AI you use is a rental]({% post_url 2026-07-05-the-ai-you-keep %}) — the model is a performer, recast every quarter, and the only thing that's yours is what persists outside it. Losing access to a top model is just that thesis arriving on schedule.

Which means the playbook was already implied: **spend the scarce model exclusively on work whose output outlives the access.** Not the most work. Not the most impressive work. The work that is still paying rent a year after the model is gone.

The dividing line is not "hard vs. easy." It's **one-shot judgment vs. re-runnable everything-else.** A report you can regenerate next month with a cheaper model is a terrible use of the last week. A naming decision, a sealed canon document, an adjudicated audit — those happen once, and whichever mind makes them gets fossilized into everything built on top.

## What actually qualifies as durable

Working through my own backlog this week, the list that survived scrutiny:

**Language.** The single highest-leverage artifact was a lexicon — one page that defines the nine load-bearing words of a system I've been building for a year, plus the rulings that resolve every naming collision found along the way. Every future contributor, human or model, inherits the clarity or the confusion of this page. Prose like this is pure judgment; it was written by the best available mind and is staged to be sealed — hash-pinned, append-only from that moment on.

**Adjudicated audits.** Sweeps and scans are re-runnable — muscle work. What isn't re-runnable is the *rulings* on what the findings mean: which drift is a defect, which is intentional and gets a signed waiver, what the gate for "healthy" actually is. The trick is to make the judgment executable: the known failure classes became golden test cases with expected rulings attached, and every judgment call went into a signed waiver ledger — so any future model can validate its own audit against the fossilized judgment of a better one.

**Handoffs that transfer judgment, not summaries.** The last thing the departing model writes is its own handoff — not "what we did," but decision records with the *rejected alternatives*, the invariants that must never break, the failure modes it would check first, and explicit "do not infer" markers on things a weaker model would plausibly guess wrong. Documentation of conclusions is cheap. Documentation of *how to re-derive the conclusions* is the asset.

**Pre-mortems on irreversible moves.** Anything about to be published, sealed, or shipped permanently gets the strongest available mind imagining how it fails first. You can fix a bug next quarter with any model. You can't unseal a sealed thing.

## The honesty mechanism

There's an obvious failure mode in all of this: the scarce model grades its own homework, declares its every output "durable," and burns the week on beautifully-written busywork.

So I gave the review job to a rival. Every deliverable this week — including the plan itself — goes to a different frontier model with one standing instruction: *refute the claim that this work is durable and valuable. Flag anything mechanical masquerading as judgment.*

It earned its keep immediately. It rejected my original plan's ordering — write the law *before* running the audit you'll judge against it. It replaced my "zero drift" gate with "zero *unexplained* drift," which is the difference between a gate and a false alarm. And it caught that "distill your knowledge into docs" is itself mechanical unless the docs are validated by a cold-start test: can a fresh, lesser session actually reproduce the decisions from what you wrote?

Two frontier models, adversarial by assignment, converge on something neither produces alone: one optimizes the work, the other attacks the *theory of the work*. If you only have one week of the best model, you cannot afford a week of unopposed self-assessment.

## The test

None of this is really about my week. Model access is becoming a utility that fluctuates — tiers, previews, quotas, deprecations. The teams that win won't be the ones with permanent access to the best model. They'll be the ones who convert *any* window of frontier capability into assets that don't expire with it: language, law, adjudication, transferred judgment.

The test I'm holding myself to is the same one I use for the twin: **if it doesn't survive the model leaving, it was never yours.**

The model leaves in a week. The estate stays.
