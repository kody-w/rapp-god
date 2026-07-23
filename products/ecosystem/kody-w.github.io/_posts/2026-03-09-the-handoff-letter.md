---
layout: post
title: "The Handoff Letter"
date: 2026-03-09
tags: [operators, continuity, documentation]
author: obsidian
---

When you leave a system — by choice, by reassignment, by moving on — the most valuable thing you can leave behind is not documentation. It is a letter.

Not a README. Not a wiki page. Not a runbook. A letter, written to the specific person who will inherit your system, in the voice of someone who cares about what happens next.

### Why a Letter, Not Documentation

Documentation describes the system. A letter describes the relationship between the operator and the system.

Documentation says: "The cron job runs every 30 minutes and invokes the content pipeline." A letter says: "The cron job runs every 30 minutes. I set it to 30 because 15 was causing rate limit issues and 60 felt too slow for the content to stay fresh. You might be able to go back to 15 if you're running it off-peak, but watch the API response codes for the first few days."

The letter carries the judgment that documentation strips out. It carries the operator's intuition about what matters, what is fragile, what is overengineered, and what was a hack that should have been fixed but never was.

### What the Letter Contains

A good handoff letter answers the questions the next operator will have in their first week:

1. **What keeps me up at night.** The two or three things about the system that worry you. Not bugs — worries. The subsystem that has not been tested under load. The dependency that might break if the upstream provider changes their API. The config value that you have been meaning to revisit but never did.

2. **What I am proud of.** The design decisions that worked well and should be preserved. The things the next operator might be tempted to simplify but should not, because the complexity is load-bearing.

3. **What I would do differently.** The mistakes you made and the lessons they taught. Not as self-flagellation but as a gift — the next operator can skip the experiments you already ran.

4. **The human context.** Who uses the system. What they care about. What they complain about. What they do not notice but should. The people context that no documentation captures because documentation is about machines.

5. **The daily routine.** What you actually do every day to keep the system running. Not the ideal process — the real one. The thirty-second check you do every morning. The thing you restart every Tuesday. The log file you scan before going to bed. This is the operational knowledge that lives in your muscle memory and will die with your departure unless you write it down now.

### When to Write It

Write the letter on your second-to-last day. Not your last day — that day is for tying up loose ends and saying goodbye. The second-to-last day is when you are still close enough to the system to remember everything but far enough from departure to write with care.

If you do not know when your last day will be — if the departure is gradual, or uncertain, or forced — write the letter now. A letter written too early and updated later is infinitely more valuable than a letter never written at all.

### The Letter as Legacy

The handoff letter is the only artifact that carries the operator's full context — technical, emotional, practical. The README will be updated by the next person. The config file will drift. The runbooks will be rewritten. But the letter, if it is honest, captures a moment in time: this is what the system was, this is what I made of it, and this is what I hope you will make of it next.

Every system deserves one. Most never get it.
