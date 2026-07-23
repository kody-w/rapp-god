---
layout: post
title: "Optimization erases minorities: why per-group quotas matter"
date: 2025-10-01
tags: [systems, optimization, fairness, evolutionary-algorithms, recommendation-systems, ml]
description: "Top-N-by-fitness culling sounds reasonable. It collapsed an entire ecosystem to one species in my simulation. The fix is a general principle that applies to evolutionary algorithms, recommender systems, content moderation, and any place where a global score decides who survives."
---

I had a simple bug in an evolutionary simulation. The world was supposed to support five hundred individuals at any time. After every generation, if the population grew above that limit, I had to remove some.

The first version did the obvious thing. Sort by fitness. Keep the top five hundred. Drop the rest.

The result, after running it long enough to see the steady state, was a world with one species in it. The dominant lineage swept the leaderboard, took every slot, and every other lineage got driven extinct — even lineages with unique traits, even lineages that occupied entirely different niches, even lineages that could not interbreed with the winner so were not actually in competition with it.

Same simulation, fixed differently: instead of a single global fitness sort, give each species its own per-species quota proportional to its population. Cull within species. Same compute. Same fitness function. Same world. The result this time was an ecosystem with fifty-three surviving species.

One species versus fifty-three. The only thing I changed was *how the limit gets applied*.

This is a general principle. Most engineers will encounter it without recognizing it, because the "winner takes all" effect of a global optimizer feels like the system is doing its job. Diverse minorities disappearing into a sea of one optimal answer looks, at first glance, like convergence. It is actually collapse.

This post is about why that happens, where it shows up beyond simulations, and the family of fixes that work.

## The mechanism

A global fitness sort with a hard cap is a winner-takes-all tournament whether you intended it that way or not. Here is the precise mechanism.

You have N members of various groups. You have a cap K, with K < N. You sort everyone by a single fitness score and keep the top K.

The probability that group A is represented in the top K is proportional to the integral of A's fitness distribution above the threshold defined by the K-th rank. Group A survives in the cap if and only if that integral is non-trivial.

Now imagine group A and group B coexist. Group A has a higher mean fitness than group B, by a small amount. Group A also has many more members. Both differences compound. The threshold rank gets pulled up by group A's mass. Group B's distribution sits mostly below it. After one round of culling, group B is smaller. After two rounds, smaller still. After enough rounds, gone.

Crucially, group B was *not failing*. Its members were all alive, reproducing, occupying their own niche, doing their own thing. They were just not competing with group A — but the cap forced them to, by treating "the population" as one undifferentiated pool.

This is the bug. The cap was a memory limit, an arbitrary number to keep the simulation tractable. It became, accidentally, a winner-takes-all selection pressure across groups that had no business competing.

## Where this shows up in real systems

Once you see the pattern, it is everywhere.

**Recommender systems.** A platform has limited user attention. It surfaces the top-K items by predicted engagement. Each round, the most-clicked content gets the most slots. Less popular but distinctive content gets squeezed out. Over time, the recommender's catalog homogenizes into whatever was most universally engaging at the start. Niche taste collapses, not because anyone wanted that, but because the global ranking treated all content as one pool.

**Content moderation.** A queue of flagged items, finite review capacity per day. The triage scores by severity. The most severe items always get reviewed; mid-severity items from minority categories never make it to a reviewer. Over months, the moderation policy effectively becomes "we only act on the worst ten percent of complaints." Categories that genuinely deserve review but happen to be less severe on average become invisible.

**Hiring funnels.** Top-K candidates by some composite score. The score correlates with traits that, for any of a dozen reasons, the majority cohort happens to score higher on. The minority cohort is not failing — they are doing fine — but they fall below the threshold and never enter the pipeline. The funnel converges to the majority cohort over time, reinforcing whatever fed the score correlation in the first place.

**A/B testing.** Multi-variant tests with capacity caps. The variant with the highest mean lift takes the most traffic on a per-experiment basis. Variants exploring genuinely different tradeoffs that perform well for narrower audiences get starved of traffic and never accumulate enough data to demonstrate their case. The product converges on whatever the median user wants, not whatever is best for the actual distribution of users.

**Multi-armed bandits.** Same family. A pure exploit strategy dominates. The famous "exploration vs. exploitation" tradeoff is exactly this issue: pure global ranking will lock you onto the early winner. You need explicit exploration budget — which is a per-group quota in disguise.

**Search ranking.** Recency bias gives recent results higher base scores. Older but still relevant results never accumulate enough rank to make the front page. The search index becomes a recency index.

**Resource allocation.** Cluster scheduling that assigns capacity by current load. Big jobs starve small jobs because the threshold is set by big-job demand. Small experimental workloads never get scheduled. Innovation suffers, not because anyone deprioritized it, but because the scheduler does not know minority workloads exist as a distinct class.

The shape is the same in every case. There is a global cap. There is a global score. Sub-populations have different distributions. The cap eats the smaller distributions first.

## What "per-group quota" actually means

The fix family looks similar across all these domains. Stop applying the cap globally. Apply it per group, with the group quota proportional to something defensible.

Three flavors, increasing in sophistication.

**Proportional quota.** Each group gets a quota equal to its current share of the population, applied to the cap. A group with twenty percent of the population gets twenty percent of the cap. Cull within groups. This protects existing diversity but does not create it.

**Proportional-with-floor quota.** Same as above, plus a minimum floor. No group is allowed to drop below, say, three members. This protects very small groups from being picked off by a single bad round, at the cost of slightly oversampling them.

**Diversity-weighted quota.** The quota is computed not just from current size but from a distinctiveness measure. Groups whose distributions overlap heavily with other groups get smaller quotas (they are not adding much diversity). Groups whose distributions are far from everyone else get bigger quotas (they are filling unique niches).

Each is a single function over the existing fitness scores. The change to the cull step is small. The change to the system's long-run behavior is enormous.

## The general principle

The general statement, if you want to carry just one sentence:

> A global selection rule with a hard cap will collapse to the dominant subgroup in the long run, regardless of how good the score function is. To preserve diversity, the selection rule must operate within groups, not across them.

This is true even when:

- The score function is "fair" by some metric you defined.
- The dominant subgroup *is* better on the score function.
- The minority subgroups *are* less effective by the score function.
- You did not intend to be selecting against minorities.

The bug is not in the score. The bug is in the structure that converts the score into who survives.

## Why "scale up the cap" does not save you

A reflex when you discover this is to argue: but if the cap is high enough, surely the minority groups will all fit, and the problem goes away.

Two reasons that does not work in practice.

**Caps are usually not soft.** The cap exists because something real is constrained — memory, attention, screen real estate, review capacity, compute budget. You cannot just raise it without hitting the resource limit you set it at.

**Even with a high cap, drift dominates over time.** With a global rank, every round, the dominant group gets a tiny edge in representation. Over enough rounds, even a small per-round bias compounds into the same collapse, just slower. The long-run equilibrium of any ranked system without group-aware selection is the same: one group eats everything.

The fix has to be structural, not numerical. Treat groups as first-class. Give them their own quota. Cull within them, not across them.

## When the global ranking *is* what you want

To be precise: there are cases where you genuinely want the global ranking. If your system is "find the single best response to this query," global ranking is correct. The point of this post is not "always use per-group quotas." The point is **know which kind of system you are building.**

If the system has a single output and you want it to be the best one, global ranking is right.

If the system has many outputs and you want them to be the best across a population, global ranking is wrong, and per-group quotas are right.

The mistake is using the first kind of selection in a system that is actually the second kind. Most systems with a population are the second kind, and most teams accidentally apply the first kind because it is the obvious thing to do.

## A useful diagnostic

Before you ship any system that has a cap and a global score, ask three questions.

**Is there a meaningful notion of subgroup in this system?** Species, content categories, demographic cohorts, workload types — anything where members of one subgroup are not really competing with members of another for the same purpose.

**If yes, would I be okay with my cap erasing one of those subgroups entirely?** If the answer is "no, that would be a bug," your selection rule needs to be group-aware.

**Is the current selection rule group-aware?** If you sort by a single score and slice off the top K, no, it is not.

If you fail this diagnostic, the fix is small. Compute the score per item, *partition* by group, then take the top K-per-group. Two extra lines of code. Order-of-magnitude difference in what survives.

I had to learn this from a simulation that was supposed to be about evolution and ended up being about monoculture. The same lesson applies — quietly, invisibly, by default — to every ranking system in production.

The most dangerous bugs are the ones that look like the system working as intended.
