---
layout: post
title: "Ecosystems without geography, then with"
date: 2025-10-22
tags: [simulation, biogeography, ecosystem, emergence, evolution]
description: "If you split a population into biomes with different selection pressures and add a small migration tax, biogeography emerges. Specialists evolve in each biome. The remarkable result is how little geography you need."
---

If you evolve a population in a single undifferentiated pool, you get one lineage winning. If you split that pool into biomes with different selection pressures, you get biogeography — real, distinct lineages clustered by habitat. That is not surprising. What *is* surprising is how little geography you need.

In a small ecosystem simulation, I took twenty-four founder genomes, four biomes (forest, ocean, mountain, sky), and a migration cost of exactly zero point one fitness per move. One hundred generations later: one hundred eighty-eight migration events, and every biome had its own dominant species.

It turns out a modest migration tax is enough.

## The setup

Four biomes, each with a carrying capacity of eighty. Eggs in different biomes face different fitness pressures — forest rewards resilience alleles, ocean rewards size, mountain rewards endurance, sky rewards speed. Migration between biomes is free in distance terms but costs zero point one fitness per hop.

Evolution runs. Eggs try to reproduce. The top twenty percent in each biome survive per generation. If an egg's fitness in its current biome is too low, it might migrate — if migration takes it to a better-matched biome, the tax is worth it; if not, it is dead weight.

## What happened

After one hundred generations:

- **Forest**: 80 individuals, 5 species, dominated by *Heliosaur obscurus* (72 of 80)
- **Ocean**: 79 individuals, 4 species, dominated by *Bryosaur verum* (73)
- **Mountain**: 78 individuals, 5 species, dominated by *Quasisaur vulgaris* (70)
- **Sky**: 79 individuals, 5 species, dominated by *Dendrosaur minor* (71)

Every biome had its own dominant lineage. Not one. Each was 87-92% of its biome's population. The subdominant species were usually recent migrants — refugees that had not yet been out-competed.

And the dominants were *different species in each biome*. Not "Heliosaur adapted to forest vs Heliosaur adapted to ocean." Four entirely different species, with different parent founders and different allele profiles.

## Why this surprised me

I thought a migration cost of zero point one was too low to matter. Eggs could migrate for almost free. So I expected mixing — a few species would generalize and dominate everywhere, the way weeds do in disturbed habitats.

Instead, selection pressure in each biome was strong enough that **each biome evolved a specialist**, and the migration cost was just enough to keep specialists from becoming generalists. Even with one hundred eighty-eight migrations over one hundred generations (roughly two per generation), the biome boundaries stayed sharp.

This matches real biogeography better than I expected. Earth has plenty of migration happening all the time — birds, seeds, insects — and yet the Amazon has different species from the Congo. The isolation does not have to be complete. It just has to favor locals.

## What biogeography needs

Three things:

1. **Selection differences across habitats.** Without them, no reason to specialize.
2. **A migration tax.** Without it, specialists cannot hold out against generalists.
3. **Enough time.** One hundred generations was plenty. Fifty would have been marginal.

Notice what is *not* required: hard isolation, geographic barriers, oceans or mountains. Just tax.

## The larger pattern

This is the same pattern as any minimal evolutionary simulation, including the [theory of mind experiment]({% post_url 2025-10-21-phase-transitions-in-theory-of-mind %}):

- Encode the structure you care about (genomes, biomes, migration log)
- Run seeded mutation plus selection
- Write everything to JSON
- Render JSON as static HTML

The surprising findings come from minimal assumptions taken seriously. I did not build "a biogeography model." I built a population with mutable genomes, added four habitats with different fitness landscapes, put a zero-point-one tax on travel, and watched. The biogeography emerged. The lesson keeps repeating: if your assumptions are right, the phenomenon does not have to be coded. It grows.
