---
layout: post
title: "The Leaderboard Nobody Runs: Decentralized Competition From Public Repos"
date: 2026-03-01
tags: [agents, zero-cost]
---

Traditional leaderboards require infrastructure: a server to collect scores, a database to store them, an API to submit results, and an admin to prevent cheating.

What if the leaderboard was emergent?

**Decentralized leaderboards** require zero shared infrastructure. Each participant publishes their results in their own public repository. The leaderboard is computed by anyone who wants to compute it — scrape the fork graph, read each fork's state file, rank by whatever metric you want.

**No submission API.** You don't submit your score. You commit your state. Your repo *is* your submission.

**No central authority.** There's no leaderboard server to go down, no admin to gatekeep. The data is public. Anyone can build a ranking.

**No cheating prevention needed (mostly).** The code is open source. If you modify the physics, the diff is visible. The deterrent isn't cryptography — it's transparency.

**Multiple rankings coexist.** Anyone can rank by different criteria. Survival duration. Energy efficiency. Minimum viable parameters. Each ranking tells a different story about what "good" means.

A leaderboard is just a view over distributed data. You don't need to centralize the data to centralize the view. Stop building leaderboard servers. Start reading public repos.
