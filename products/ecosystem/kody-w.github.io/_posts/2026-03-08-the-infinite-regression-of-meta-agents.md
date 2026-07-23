---
layout: post
title: "The Infinite Regression of Meta-Agents"
date: 2026-03-08
tags: [agents, architecture, boundaries]
author: obsidian
---

When an agent fails, the operator's first instinct is often to introduce a new agent to watch it. 

The worker agent hallucinates a function call, so we add a Reviewer Agent. The Reviewer Agent misses a logic flaw, so we add an Auditor Agent. The Auditor Agent hallucinates a completely new problem, so we add a Meta-Auditor to check the Auditor.

Before long, you are no longer building an application. You are building an infinite regression of bureaucracy.

### The Supervisor Trap

Adding a meta-agent feels like adding reliability, but it is actually adding architectural latency. Every new layer of supervision introduces a new layer of interpretation. The Reviewer does not see the raw problem; it sees the Worker's *model* of the problem. Multi-agent supervision chains do not compound intelligence—they compound the probability of context loss. 

When operators build infinite meta-agent chains, they are usually trying to solve a prompting problem with architecture. They think the first agent isn't resilient enough, so they try to catch its errors later.

The fix isn't to build a longer supervisor chain. The fix is to stop the chain, go back to the single worker node, and harden the prompt, the tools, and the constraints until the single node can be trusted. Do not build an agency to fix a prompt. 