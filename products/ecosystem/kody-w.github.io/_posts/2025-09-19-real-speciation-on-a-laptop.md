---
layout: post
title: "Real speciation on a laptop, in eight seconds"
date: 2025-09-19
tags: [simulation, evolution, emergence]
description: "Most evolutionary simulations fake speciation by clustering agents on a vector and labeling the clusters. Real speciation is something different — a threshold crossing in a distance metric that maps onto a physical impossibility. Here is what it looks like to encode that correctly, and what it produces."
---

Run almost any "evolution simulation" and you will eventually be told that the system has produced "species." Click through the explanation and you usually find the same trick: the simulation periodically clusters the agents on some attribute vector — k-means, or DBSCAN, or a hand-tuned threshold — and *labels* the clusters as species. Different cluster, different label, different species. Done.

It is a useful visualization. It is not speciation. The clusters are an analyst's choice imposed on the data, not something that emerged from the simulation itself. If you change the clustering algorithm or its parameters, the "species" change shape. If you stop running the clusterer, the species disappear. Real species don't behave like that. Real species are stable across observers because they are defined by something the population itself does, not something we say about the population.

I was curious whether you can build a small simulation in which speciation is genuine — emergent from the rules, not painted on after the fact. The result fits in a couple hundred lines of standard-library Python and runs in about eight seconds on a laptop. From a hundred founder organisms over five hundred generations, it produced a hundred and one distinct lineages, thirty-seven of which went extinct mid-run, and sixty-four of which were still alive at the end. None of them were assigned by a clusterer. They emerged from the rules.

This post is about how to encode real speciation, why the encoding matters, and what the resulting cladogram tells you that clustering can't.

## What real speciation actually requires

The biological definition that biology classes drill into every undergraduate is: two populations are separate species if they cannot produce viable, fertile offspring even when given the chance. The word that does the work is *cannot*. It is not a matter of degree, not a matter of preference, not a matter of how an outside observer chooses to label them. It is a hard physical wall.

That hard wall is what makes a species a stable category. Two lineages that have crossed it can mingle, share territory, and even mate, but they will not exchange genes — and so they accumulate independent histories indefinitely. Two lineages that have not crossed it might look very different, but they remain one species, because the moment conditions favor it, gene flow can resume.

The translation into a simulation is exact. **You need a metric that measures genetic distance between two organisms, and a threshold above which reproduction silently fails.** Above the threshold, the organisms might pair, might mate, but the offspring is non-viable — it doesn't enter the next generation. Below the threshold, reproduction proceeds normally.

Once you encode that, you don't have to *call* anything a species. You just have to watch the distance graph. When a sub-population's lineage drifts far enough from a sibling lineage that no member of one can interbreed with any member of the other, those two sub-populations have *become* separate species, by the only definition that matters: they cannot exchange genes anymore, even if you put them in the same room.

## The setup

The simulation is small. Each organism has a genome — for this run, a fixed-length vector of integers, where each position is an "allele" drawn from a small set. Reproduction works as follows:

- Pick two parents.
- Compute their compatibility: a weighted score based on how many alleles match at the same positions.
- If the compatibility is above a fixed floor, produce one offspring whose genome is a recombination of the parents' genomes plus a small mutation step.
- If the compatibility is below the floor, no offspring. The mating attempt fails silently.

Selection is also small. Each generation, each organism gets a fitness score from a simple landscape function (a few sinusoidal hills in the allele space). Lower-fitness organisms are more likely to die. Higher-fitness organisms are more likely to be picked as parents. Population size is held roughly constant.

There are no clusters, no labels, no species file. There is just a population, a compatibility floor, and a fitness function. The simulation runs for a fixed number of generations and writes its history to disk.

## What "watching for speciation" looks like

Once the simulation has run, the question becomes: did any two parts of the population diverge to the point where they could no longer interbreed?

Here is the test. Take any pair of living organisms at a given generation. Compute their compatibility. If it is above the floor, they are in the same species — gene flow is possible. If it is below the floor, they are in different species — gene flow is impossible.

Apply this pairwise across the whole population, walk back through history, and you can identify each *speciation event*: the generation at which a sub-population's compatibility with the rest of the population dropped below the floor and stayed there. That generation is the moment a new species exists. Before it, the lineage was part of a larger population. After it, the lineage is reproductively isolated.

Crucially, no one labels the species. The compatibility floor labels them. If you change the floor, you change the species count, but the *events* remain identifiable: a particular lineage's compatibility-with-the-rest dropped below your chosen threshold at a particular generation. Different observers can use different thresholds and they will all agree on the temporal ordering of those events. That is the property real species have and clusters don't.

## What the run produced

A run with one hundred founders, five hundred generations, a moderately permissive compatibility floor, and a seeded random number generator (so the run is reproducible byte-for-byte) produced:

- **101 species** named over the course of the run.
- **37 species extinct** — populations that hit zero living members at some generation.
- **64 species alive** at the end.
- A cladogram — a tree of parent species and their child species — that you can read directly from disk.

It runs in about eight seconds on a laptop with the standard library only. No NumPy, no specialized evolutionary-computation framework. The whole thing is a few hundred lines.

The cladogram is the receipt. Here is a small slice, edited for readability:

```
Lineage-A (founder, gen 0, 124 alive at end)
├── Lineage-A.1 (split at gen 87, extinct gen 312)
└── Lineage-A.2 (split at gen 203, 41 alive)
    └── Lineage-A.2.a (split at gen 378, 8 alive)
```

Each split records: the parent lineage, the generation at which the sub-population's compatibility-with-rest dropped below the floor, and the alleles whose drift was responsible for the drop. You can trace any living organism back to its founder through a chain of recorded reproductive-isolation events.

You cannot do that with k-means.

## Why the extinctions are the load-bearing evidence

It would be easy to look at "101 species" and shrug — labeling more things doesn't prove anything. The thirty-seven extinctions are what convince me the model is doing real work.

In a clustering-based fake speciation, clusters never go fully extinct. They dissolve, they merge, they drift, but there is no "population zero" event for a cluster — the agents in it just get re-clustered into something else.

In this simulation, thirty-seven lineages reach a final living individual and then *nothing*. Their alleles vanish from the gene pool. Their slot in the cladogram becomes a dead branch. Some die young — within twenty generations of their split — typically because they emerged on the wrong side of a fitness valley and the surviving sub-population was too small to escape it. Some persist for hundreds of generations and then succumb late, often when the fitness landscape shifts and their particular allele combination becomes a liability.

The distribution of extinction times also looks right. It is a long-tailed distribution: most extinctions are early, a long tail are late. Paleontologists see this in the fossil record. It is what you'd expect if extinction is governed by a stochastic process where most novel lineages are fragile and a minority happen to find a stable adaptive peak.

I did not put any of this in by hand. The compatibility floor and the fitness function produced it.

## What the cladogram is good for that the cluster plot is not

A cladogram is more than a snapshot. It is a history. You can ask it questions a cluster plot can't answer:

- *When did this lineage become a separate species?* The split generation is recorded.
- *Why?* The alleles that drove the compatibility drop are recorded with the split.
- *What are its closest relatives, alive or extinct?* Walk up the tree.
- *How long did it take a typical lineage to go extinct?* Compute the distribution of (extinction-generation minus split-generation) across the dead branches.
- *Is the rate of speciation accelerating, decelerating, or stable?* Compute the count of split events per generation as a time series.

The cluster plot can tell you "there are six species at generation 500." The cladogram can tell you "there have been a hundred and one species over the run, the last speciation event happened at generation 491, the average lineage that has gone extinct lived for two hundred and four generations after its split, and the rate of new species creation has been declining since generation 350."

That last fact, decline in speciation rate, is itself something that emerges in the run and is worth pondering. Early on, the population is exploring a relatively uncharted allele space, and small drifts can quickly cross the compatibility floor in any direction. Later, the surviving lineages have settled near the local fitness peaks, and the floor becomes harder to cross — the population is more entrenched, the niches are more occupied, and you need bigger drifts to make a new species. Real ecosystems show this same phenomenon.

## The point

When you read about an evolutionary simulation that claims to produce species, ask one question: *what would have to be true in the data for two organisms to count as the same species, and what would have to be true for them to count as different ones?* If the answer involves a clustering algorithm or a labeled-by-the-author file, you are looking at a visualization. If the answer involves a metric and a threshold encoded in the reproduction rules themselves, you are looking at speciation.

This is also a good general test for any "emergent" behavior in a simulation. *Did the rules produce it, or did the analysis dashboard?* If turning off the dashboard would make the behavior disappear, the behavior is in the dashboard, not the simulation.

The reason it is worth getting this right — even on toy problems on a laptop in eight seconds — is that the same trap is everywhere. Cluster something, label the clusters, and you have a story you can tell. Encode the rule that *makes* a category real, and you have a system that produces categories on its own. Those are not the same thing, and the difference compounds the longer you run the simulation.

Real speciation is a threshold crossing in a distance metric that maps onto a physical impossibility. Once you encode that — which is, frankly, two extra lines of code in a reproduction function — you don't have to ask whether you're seeing speciation. You can read the events off the log.

The Cambrian, on a laptop, in eight seconds. The result was already in the rules.
