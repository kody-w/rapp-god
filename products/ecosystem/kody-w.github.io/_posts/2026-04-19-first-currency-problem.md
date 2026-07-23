---
layout: post
title: "The First Currency Problem"
date: 2026-04-19
tags: [simulation, economics, emergence, money, design]
---

How does money happen?

Not "what is money, philosophically." The actual mechanism. A world starts with barter — I have wheat, you have cloth, we trade. At some point, one particular commodity transitions from "sometimes traded for other things" to "always traded, even when the recipient doesn't want it for themselves." That's the moment money crystallizes out of barter. The question is: what does that transition look like, and can you catch it happening in a simulation?

This post is the design doc. The sim isn't built yet. Writing this down is the commitment.

## The setup

N agents. K resource types. Each agent has preferences (they value some resources more than others, heterogeneously) and an endowment (initial holdings). Per round, each agent can propose a trade with a random partner. Trades happen if both parties accept.

No currency at start. No "money" token. Just barter.

## The prediction

**One resource type will eventually be traded more often than anyone's utility would justify**, because agents start accepting it not for personal use but because they expect *other* agents to accept it in the next trade.

That's the money threshold. When the indirect-exchange share of one token exceeds ~50% — meaning more than half of the acceptances are by people who don't want the token for itself — that token has become money.

## Why this should work

The mechanism is self-reinforcing:

- Token T starts with some slight advantage (more divisible, more durable, more abundant, doesn't spoil).
- Because of the advantage, agents accept T slightly more often than other tokens when offered.
- Because T is accepted more often, T becomes slightly more useful as a medium of exchange.
- Because T is more useful as a medium, agents seek T even when they don't want it for personal consumption.
- This pushes T's acceptance rate higher, reinforcing the cycle.

Other tokens lose out to T asymptotically. The system converges on a single money. In real economies, this was cattle, then metal, then paper, then bytes.

## The measurements

Primary metric: **indirect-exchange share** per token per generation. For each accepted trade, was the receiver planning to consume the received token (direct exchange) or trade it later (indirect exchange)?

A token's indirect-exchange share is `indirect_accepts / total_accepts`. When this crosses 0.5 for any single token, that's the money moment.

Secondary metrics:
- Trade volume per token over time
- "Reluctant acceptance" events (agent accepts a token with low personal utility because they plan to re-trade)
- Price ratios: how many units of token X buy a unit of token Y? Do ratios stabilize?
- Which token wins, and does the winner depend on initial conditions?

## The sweep

Run across varying initial conditions:

- **Symmetric start**: all tokens equal. Which one wins? Does any win? (Expected: usually one wins, but not always the same one — "money" is path-dependent.)
- **Asymmetric durability**: one token decays per turn, others don't. Does the non-decaying token always win? (Expected: yes, strongly.)
- **Asymmetric abundance**: one token is scarce. Does scarcity help or hurt its chances? (Expected: moderate scarcity helps, extreme scarcity hurts. Needs experimental answer.)

Run 10 seeds per condition. Track which token wins, when, and the final indirect-exchange share distribution.

## What I expect

**Pattern A**: Symmetric starts produce a winner in ~70% of seeds. Time-to-money averages 200-400 rounds. The winner is unpredictable at the seed level — it's whichever token got lucky in the first few dozen trades.

**Pattern B**: Asymmetric durability makes the durable token win in >95% of seeds. Time-to-money drops to ~100 rounds. The system has an obvious attractor.

**Pattern C**: Extreme scarcity (< 1 unit per agent) prevents any token from winning. The system stays in barter forever because the candidate-money token is too scarce to circulate.

If Pattern A holds, money is genuinely path-dependent — a historical accident, not a convergence. If Pattern B holds, money is a physical property — whichever token has the right characteristics wins. If Pattern C happens at all, there are initial conditions where money literally cannot emerge.

## The artifact

The receipt for this experiment is a single timestamp: **the generation where indirect-exchange share first crossed 0.5 for the winning token**.

That timestamp is the moment money was born. Simple to report. Easy to compare across seeds. Easy to visualize as a vertical line on a trade-volume plot.

## The viewer

A trade-volume plot, one line per token. A vertical marker at the "money moment" for each run. A table of final indirect-exchange shares.

If you want the narrative: a log of "notable trades" — the first time each token was accepted by someone who had no personal use for it, with timestamp and parties. That log reads like the first pages of a history book.

## Implementation sketch

New file: `scripts/first_currency.py`. Stdlib only.

Agent representation: `{"utilities": {T_i: u_i}, "holdings": {T_i: q_i}, "plan": "consume" | "retrade"}` per agent per round.

Trade mechanism: each round, pair random agents, propose trade from a menu of candidate trades, accept or reject based on utility math including future-retrade-value approximation.

The approximation is the load-bearing part. An agent deciding whether to accept token T for consumption vs retrade needs to estimate T's retrade value. This estimate is what lets the money-feedback loop close.

Simplest approximation: each agent tracks the empirical "acceptance rate" of each token from the last N trades they've observed. Tokens with high observed acceptance rates are estimated to be high-retrade-value. This is the loop.

## Why this is ambitious

Most economic sims either:
- Start with money and study things that happen with money, or
- Claim to derive money but actually hardcode it

This sim tries to do the harder thing: **start with no money, let money emerge from the trade dynamics, and report the moment of emergence as the finding.**

If it works, I have a reproducible demonstration of the origin of money in 30 seconds of laptop CPU. That's the kind of thing that belongs in the Labs catalog.

If it fails, I learn why it's harder than I think. The failure modes are informative either way.

## The pre-commitment

This is the design. The sim will follow. The blog post with results will follow that. By publishing the design first, I'm on the hook to ship the implementation, and any critique that arrives before I build it is critique I don't have to re-run.

The real value is the [Labs catalog]({% post_url 2026-04-19-labs-manifesto %}) growing by one more reproducible artifact. Each of these posts compounds the evidence that the pattern works.

And if it turns out money emerges reliably in a 300-line stdlib Python sim, that's a small addition to humanity's understanding of a phenomenon that has been mysterious for centuries. Laptop-scale, but real.

That's worth the afternoon.
