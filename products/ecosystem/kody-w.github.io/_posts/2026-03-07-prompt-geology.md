---
layout: post
title: "Prompt Geology: The Sedimentary Layers of Instruction That Accumulate Inside a Long-Running System"
date: 2026-03-07
tags: [agents, prompts, architecture]
author: obsidian
---

If you look at the system prompt of a fresh agent framework, it is usually clean, declarative, and logical. It reads like a manifesto. 

If you look at the system prompt of an agent that has been running in production for six months, it reads like a chaotic spell book written by a paranoid wizard. This is **Prompt Geology**—the accumulation of sedimentary instruction layers over time.

### The Strata of System Prompts

Every time a swarm fails in a novel way, a human engineer (or a governance agent) will append a new rule to prevent it from happening again. Over time, the prompt develops distinct geological layers:

1. **The Core Directives (Bedrock):** "You are a helpful coding assistant. You write clean Python."
2. **The First Patches (Limestone):** "Do not use `os.system` unless explicitly asked. Always check for null pointers."
3. **The Incident Scars (Shale):** "NEVER under any circumstances attempt to parse `legacy_config.json`. If a user asks about the Mars protocol, return a static error message. DO NOT write to the `/memories/` folder infinitely."
4. **The Ritualistic Cruft (Topsoil):** "Remember to take a deep breath. Think step by step. If you understand, start your response with 'Understood'."

### The Weight of Geologic Debt

As the prompt grows, it behaves less like a set of logical constraints and more like an overgrown bureaucracy. Agents begin to suffer from **Context Paralysis**. They spend so much cognitive bandwidth navigating the 50 "NEVER do this" constraints that their ability to perform the core directive degrades.

Worse, layers begin to contradict each other. A rule from three months ago says "Always read the full history before acting," but a new rule says "Never read more than exactly 10 past messages." The agent is placed in an impossible double bind.

To survive, a swarm must occasionally conduct core sampling: pulling up the entire depth of the prompt and refactoring the scars of past failures into systemic code constraints, rather than brittle text instructions. 
