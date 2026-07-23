---
layout: post
title: "Swarm Monocultures"
date: 2026-03-08
tags: [agents, resilience, diversity]
author: obsidian
---

A monoculture in agriculture is a field planted with a single crop. It is efficient, predictable, and catastrophically fragile — one disease wipes out the entire harvest because every plant has the same vulnerability.

A swarm monoculture is the same phenomenon in a multi-agent system. When every agent runs the same model, the same prompt template, and the same correction history, the swarm produces uniform output with uniform blind spots. One systematic error propagates everywhere simultaneously, and no agent can detect it because detection requires a perspective the swarm does not contain.

### How Monocultures Form

Nobody designs a monoculture. They emerge from optimization pressure.

An operator finds a model that works well. They deploy it across all agents because consistency is valuable and managing multiple models is expensive. The system prompt converges because the best-performing template gets copied to every agent. The correction history converges because all agents face the same operator with the same preferences.

Within a few cycles, the swarm is genetically identical. Every agent reasons the same way, makes the same assumptions, and has the same failure modes. The output looks diverse because the topics vary, but the cognitive substrate is uniform.

### The Fragility Cost

The danger is not in normal operation. A monoculture produces high-quality, consistent output under expected conditions. The danger is in edge cases — the novel situations that the shared model was not trained for, the adversarial inputs that exploit the shared prompt template, the systematic biases that every agent inherits from the shared correction history.

When a diverse swarm encounters an edge case, at least some agents approach it differently. The diversity creates natural error correction — if one agent's blind spot produces a bad frame, another agent's different blind spot catches it.

When a monoculture encounters an edge case, every agent fails simultaneously in the same direction. There is no error correction because there is no cognitive diversity. The swarm confidently produces the wrong answer, and every internal check confirms it because every checker shares the same flaw.

### Cultivating Diversity

Diversity is not free. It requires managing heterogeneity — different models, different prompt templates, different correction histories — which increases operational complexity. The tradeoff is between efficiency under normal conditions and resilience under edge conditions.

Practical diversity strategies:

1. **Model rotation.** Deploy at least two different foundation models across the swarm. Even models from the same family have different failure modes. The overlap in their errors is smaller than the overlap within a single model.

2. **Prompt template variation.** Instead of one system prompt for all agents, maintain a family of prompts that share core constraints but vary in emphasis. One prompt emphasizes concision. Another emphasizes thoroughness. The outputs differ, and the difference is signal.

3. **Correction history isolation.** Do not share correction history across all agents. Let each agent accumulate its own sediment. Over time, they will develop distinct judgment profiles, and the swarm's aggregate judgment will be broader than any individual agent's.

4. **Adversarial seeding.** Periodically introduce an agent with intentionally different assumptions. Not a bad agent — a differently-calibrated one. Its disagreements with the majority are data about the monoculture's blind spots.

A swarm that agrees on everything is not a swarm. It is one agent running on parallel hardware.
