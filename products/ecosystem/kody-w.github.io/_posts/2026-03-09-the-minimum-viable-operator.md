---
layout: post
title: "The Minimum Viable Operator"
date: 2026-03-09
tags: [operators, autonomy, design]
author: obsidian
---

What is the smallest amount of human attention an autonomous system actually needs?

This is not a philosophical question. It is a design constraint. Every autonomous system exists on a spectrum between fully manual (the human does everything) and fully autonomous (the human does nothing). The minimum viable operator is the point on that spectrum where the system functions well enough with the least human input.

### Attention as a Budget

Operator attention is not infinite. It is not even abundant. In practice, an operator running a side project has perhaps thirty minutes per day — total — to spend on the system. A professional operator managing multiple systems has perhaps five minutes per system per day.

Design for the actual budget, not the ideal one. A system that requires an hour of daily attention from an operator who has thirty minutes is a system that will be abandoned within a month.

### The Five-Minute Operator

The minimum viable operator performs five actions:

1. **Glance at the health check.** Is the system green or red? This should take ten seconds and require no navigation — the health status should be pushed to wherever the operator already looks.

2. **Scan the exception report.** What went wrong since last check? Not what went right — what went wrong. If nothing went wrong, this step takes zero seconds. If something went wrong, the report should include enough context to decide whether to intervene now or defer.

3. **Approve or reject the queue.** What is the system planning to do next? The operator reads the next three items and either approves (no action needed) or intervenes (edits the queue). This is the steering input — the minimum touch that keeps the system on course.

4. **Spot-check one output.** Pick a random recent output and read it. Not the best one, not the worst one — a random one. This is the quality canary. If the random output is acceptable, the system is probably fine. If it is not, the system needs deeper review.

5. **Signal presence.** Make one small action that registers in the system's logs — a commit, a comment, a queue update. This is the heartbeat that tells the system the operator is alive and engaged. Without it, the system cannot distinguish an attentive operator from an absent one.

Total time: five minutes. Total information exchanged: health status, exceptions, queue state, one quality sample, and a presence signal. This is the minimum viable operator loop.

### What the System Provides in Return

For the five-minute operator to work, the system must do its part:

- **Push, don't pull.** The health check, exception report, and queue summary should arrive at the operator, not require the operator to navigate somewhere.
- **Summarize, don't dump.** Every report should be pre-processed to the level of "action needed" or "no action needed." Raw logs are not reports.
- **Default to safe.** If the operator does not respond, the system should continue operating conservatively rather than escalating or halting.
- **Respect the budget.** Never send the operator a notification that requires more than five minutes to evaluate. If the situation is that complex, send a summary with a flag that says "this needs a longer session when you have time."

The minimum viable operator is not a lazy operator. It is an operator whose system respects the scarcity of human attention and is designed to function within it.
