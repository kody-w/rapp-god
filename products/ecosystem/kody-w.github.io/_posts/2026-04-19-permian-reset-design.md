---
layout: post
title: "Permian Reset: Design Doc"
date: 2026-04-19
tags: [simulation, mass-extinction, evolution, design]
---

The Permian-Triassic extinction killed ~96% of marine species and ~70% of terrestrial vertebrate species. The recovery took about 10 million years. After recovery, life didn't look the same. Entire clades were gone; entirely new ones filled their ecological niches. The survivors were not obviously "the best" — they were the lucky, the small, the adaptable.

I want to know what a laptop-scale simulation does when you trigger a mass extinction at generation 250 of a 500-generation run. Does the population recover the same species composition, different species with similar traits, or something qualitatively new?

This is the design doc. Pre-commitment device. The sim doesn't exist yet.

## The question

Three sub-questions, in order of ambition:

1. **Does diversity recover at all?** (Hypothesis: yes, reliably. Evolution fills vacuums.)
2. **Does the post-extinction morphospace match the pre-extinction morphospace?** (Hypothesis: partially. Some niches re-fill with similar forms, others don't.)
3. **Do survivors predict the new dominant lineages?** (Hypothesis: no. The survivors are chosen by the extinction event, not by their pre-extinction fitness.)

If hypothesis 3 is right, mass extinctions are **not** the endpoint of natural selection — they're a reset that selects a different winner.

## The design

Base sim: trait-based speciation with reproductive-isolation floor. 100 founders, 500 generations. Same genome model, same fitness function.

Extinction event: at generation 250, kill 95% of all living individuals uniformly at random. Every survivor has equal probability of being kept. No correlation between pre-extinction fitness and survival.

Why uniform random? Because real mass extinctions are not selective. An asteroid doesn't check your bank balance. The survivors are who happened to be in the right place at the right time. This is the key property to preserve in the sim.

## The measurements

**Pre-extinction baseline (gen 0-250):**
- Species count
- Dominant species by population
- Morphospace coverage (how much of the allele-space is occupied)
- Extinction rate per generation (background)

**The event (gen 250):**
- Species killed entirely
- Species reduced to singletons
- Survivors' allele profile vs pre-extinction average

**Recovery phase (gen 250-500):**
- Diversity curve (species count over time)
- Time-to-pre-extinction-diversity (if ever)
- New speciation events after the bottleneck
- Morphospace recovery (how much of pre-extinction allele-space is re-colonized)

**Final comparison (gen 500 vs gen 250):**
- Species overlap (what fraction of end-of-run species existed pre-extinction?)
- Morphospace overlap (how similar is the final trait distribution to the pre-extinction one?)
- Dominant lineage identity (same winner or different?)

## What I expect to see

A diversity curve shaped like a V: high before extinction, collapses to near-zero, then climbs back. This much is mechanical.

The interesting part is the *shape* of the recovery. Three possibilities:

**Pattern A: Fast recovery, same composition.** The survivors included representatives of every major lineage, and each rebuilds. Final morphospace looks pre-extinction. Evolution is deterministic at the lineage level.

**Pattern B: Slow recovery, different composition.** Survivors were a non-random sample, and the lineages they came from dominate. Final morphospace looks different. Which clade wins depends on which clade got lucky.

**Pattern C: Qualitatively novel.** Some niches re-fill with similar forms (convergent evolution). Others re-fill with forms that wouldn't have existed without the extinction. Final morphospace is a mix.

My prior is on Pattern B with a dash of C. But priors are for people who don't run experiments.

## The viewer

A two-panel plot. Top panel: diversity (species count) vs generation. Bottom panel: morphospace coverage as a heatmap. The extinction event is marked with a vertical red line at gen 250. The recovery curve is visually obvious.

A second viewer lists the "before vs after" species: who survived, who dominated after, and which pre-extinction species came back vs which went extinct permanently.

## Implementation sketch

Starting from `scripts/cambrian.py`:

1. Add `--extinction-gen` flag (default None, meaning no event).
2. Add `--extinction-survival-rate` flag (default 0.05).
3. At the specified generation, before the normal tick, randomly cull to `survival_rate` of current population. Use the existing seeded RNG for reproducibility.
4. Continue the simulation normally. Speciation logic handles recovery naturally.
5. Add pre/post measurement columns to the timeline.

Estimated effort: 2 hours. Python stdlib only, as always.

## The sweep

Run 10 seeds × 2 extinction-survival rates (0.05 and 0.10). Compare:

- Does 10% survival recover faster than 5%? (Expected: yes, but not 2x faster.)
- Does the recovered morphospace depend on survival rate? (Expected: less so at 10% because more of the pre-extinction allele pool is preserved.)
- Do any seeds fail to recover? (Expected: no, 95% extinction is not enough to kill the whole population in any realistic seed.)

## The writeup

Follow-up post with the finding, probably titled something like "The Permian Reset Is Not Selective." Assuming hypothesis 3 holds, the writeup leads with: **the species that dominate the post-extinction world are not the ones that were winning pre-extinction.** That's a clean sentence with a clean sim behind it.

If hypothesis 3 falls, the post is "Mass Extinctions Preserve Winners More Than I Thought" — also a finding, also publishable.

## Why write the design before the code

Same reason as in many design-pre-commitment essays: pre-commitment, critique-solicitation, training substrate.

If someone reads this and says "your extinction model is wrong because real mass extinctions are non-uniform across traits," that's a week saved. If someone reads this and says "you should also measure phylogenetic diversity, not just species count," the sim gets better.

The design doc is cheap. The sim is also cheap, but rework on the sim is expensive. Design first, implement once.

## Timeline

Build in the next two weeks. Publish the result post shortly after. If the finding is Pattern B or C, it becomes a citation-worthy piece that strengthens the [Labs manifesto]({% post_url 2026-04-19-labs-manifesto %}) — each sim generates a fact you couldn't get from reasoning alone.

That's the real payoff. Not "I built a cool sim." It's "I learned something specific that I wouldn't have known otherwise, and I can prove it in 30 seconds of reproducible compute."

The Permian reset is that kind of question. The sim to answer it is a 2-hour afternoon. The writeup is ~600 words. The compounding value of doing it is the only reason to do any of this.
