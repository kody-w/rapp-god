---
layout: post
title: "Biogeography from First Principles"
date: 2026-04-18
tags: [ecosystem, biogeography, simulation, evolution, biomes]
description: "Drop 24 random eggs into 4 biomes. Add migration costs. Wait 100 generations. Watch entire continents get claimed by lineages that arrived early and adapted fastest."
---

Charles Darwin spent five years on the Beagle figuring out why the finches on different Galápagos islands had different beak shapes. The answer: geographic isolation + selection pressure = speciation. Different islands, different food, different beaks.

I reproduced this in 280 lines of Python. It took 100 generations and ran in under a minute.

## The setup

Four biomes:

- 🌲 **forest** — favors `verdant`, `spotted`, `medium`, `slow_burn`
- 🌊 **ocean** — favors `azure`, `iridescent`, `large`, `voracious`
- ⛰️ **mountain** — favors `obsidian`, `solid`, `small`, `torpor`
- ☁️ **sky** — favors `gold`, `fractal`, `tiny`, `efficient`

Each biome multiplies an individual's fitness based on how many of its traits match the biome's favors. Full match = 1.5x. Total mismatch = 0.6x.

Then I dropped 24 random founders into random biomes — not their best biome. Random.

That mismatch is the engine. An individual in the wrong biome has 10% chance per generation to migrate. If it does, it pays a 20% fitness penalty for the move. Survives the cost, breeds in the new biome, settles in.

Mating requires same biome AND same species. So lineages get isolated by geography. Geographic isolation breeds new species. New species adapt to their biome. The biome gets claimed.

## What happened

After 100 generations, with seed 11:

| Biome | Dominant species | Of total |
|---|---|---|
| 🌲 forest | *Aethosaur primus* | 60 of 79 |
| 🌊 ocean | *Thermsaur antiquus* | 70 of 80 |
| ⛰️ mountain | *Thermsaur antiquus* | 78 of 79 |
| ☁️ sky | *Quasisaur vulgaris* | 76 of 80 |

**188 migration events** total across the run.

Notice: *Thermsaur antiquus* dominates two biomes. It found a winning strategy that works in cold dark places, then spread from one to the other through migration. Real animals do this. Polar bears live on ice. Penguins live on ice. Different lineages, same niche, by convergence or by spread.

Notice: *Aethosaur primus* and *Quasisaur vulgaris* each own one biome and don't spread. Their strategies are too specialized. They can't pay the migration cost without dying.

## The map

Four biome tiles. Each tile shows the species composition. Below: a population timeline by biome and a migration log.

It looks like a continent. Because functionally, that's what it is. Four ecosystems with their own evolutionary histories, connected by the thin thread of migration.

## What this is *not*

It's not a model of any specific ecosystem. The trait names are made up. The biome favors are arbitrary. The migration probability is hand-tuned.

It's a model of *the dynamics*. The shape that emerges — early arrivals dominating, isolation breeding new species, niches getting filled, occasional migrants seeding new continents — that shape is real. It's the same shape island biogeography produces. The same shape Wallace and Darwin saw.

## The deep point

Biogeography isn't a discipline that requires field work. It's a *consequence*. Of geography. Of fitness landscapes. Of migration costs. If you have those three things, you get biogeography for free. Whether your "geography" is volcanic islands, continents, or four labeled buckets in a Python dict.

This is what computational science is supposed to be. Not "here's a complicated model that fits the data." Here's a tiny dynamical system that produces the data without trying.

```bash
python3 scripts/ecosystem.py --generations 100 --founders 24 --biome-carry 80 --seed 11
```

Run it. Watch a world fill itself.
