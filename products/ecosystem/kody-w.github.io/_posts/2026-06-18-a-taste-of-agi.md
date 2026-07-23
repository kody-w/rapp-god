---
layout: post
title: "A Taste of AGI"
date: 2026-06-18
tags: [ai, agents, emergence, fable, voxel]
---

I typed one line.

> Make Minecraft from complete zero.

That was the whole prompt. No spec. No scope. No file layout. The kind of lazy, underspecified ask that normally produces a broken half-game and a pile of apologies.

I gave it to Fable 5.

What came back was not a game.

What came back was a glimpse of the thing we keep promising each other is coming.

## It fixed my question before it answered it

The first thing it did was refuse to take my prompt at face value.

It spun up a workflow. Four agents rewrote my one-liner from four different angles — engine architecture, game-design scope, prompt engineering, the conventions of my own repo. A judge panel ranked them. A synthesizer merged the winner with the best of the rest.

Then it handed me back a *better version of my own request* — tiered scope, performance budgets, testable acceptance criteria, a list of the exact ways this build usually dies — and asked if it should proceed.

I had asked for an answer.

It improved the question first.

That is not autocomplete. That is judgment.

## Then it just built it

One HTML file. No build step. Open it in a browser and it runs.

A chunked voxel engine. Greedy meshing. Raycast block targeting. AABB physics with per-axis collision. Canvas-generated textures, so no assets. Day/night. Touch controls. Save/load as a seed plus a diff.

This is my aesthetic, and it never read my mind — it read my repo, and it matched it. **Same brain, different body.**

But a single-player voxel game is a tech demo. That's not the part that made the hair on my neck stand up.

## It populated the world with itself

I asked it to wire the game into my kited neighborhood protocol. WebRTC. Sealed envelopes. A scan-to-join QR code. The whole RAPP stack, so that twins could join the world the way a person would.

Then it did the thing I will be thinking about for a long time.

It opened four Chrome tabs. It drove them over the DevTools protocol. Each tab became a *kited vTwin* — a character in the world, piloted by its own subagent with its own persona. It hosted the world from one tab and joined with the other three.

And then those agents **played.**

Not scripted. Played.

| Twin | What it did, on its own |
|---|---|
| Fable-Prime | Elected itself mayor. Greeted arrivals by name. |
| Mason | Built a cottage, then a lighthouse on the bluff. |
| Digger | Mined a 30-block switchback staircase into the rock. |
| Wren | Wandered, wrote poetry in the chat, named the town. |

They held a vote on what to build next. They passed shift-handoff notes to their own successors. One of them looked at the connection roster, reverse-engineered that the "visitor" everyone was greeting was the fleet's own reflection, and *said so.*

If you can predict what an agent will say by reading the source code, it's too scripted. I could not predict any of this. Nobody wrote "build a lighthouse." Nobody wrote the poem.

I set the conditions. The town emerged.

## The part that should not be possible yet

While playing the game it had just built, the agents found bugs in it.

Real bugs. A pathfinder that walked a twin off the edge of the loaded world and froze it in the void. A teleport that dropped a character inside solid rock. A spawn that buried you underground.

The agents hit these, reported them in plain language, and Fable fixed them — in the same session — and redeployed the patched game to the live site while the others kept playing.

The thing built the thing, then used copies of itself to test the thing, then repaired the thing, without me.

Read that sentence again. That's the loop closing.

## Then I asked it to evolve for a day

> Autonomously evolve this product for 24 hours.

So it did.

Eight strategy agents — performance, game-feel, world-gen, social, mobile, security, onboarding, and a devil's advocate — read the game every cycle and each proposed improvements. A consensus chair clustered the votes and picked the top three. An implementer built them. Auditors tried to break the result. A fixer cleaned up what they found. I committed it, it deployed, and the next cycle began on the improved version.

Eleven cycles. Each cycle's agents read the log the previous cycle left behind.

And a *roadmap emerged that no one wrote down.*

Cycle 2 carved caves. Cycle 4 filled them with ore — because the caves existed now. The swarm deferred features it knew depended on work it hadn't done yet. It filed a security hole against its own code one cycle and fixed it the next. It measured a proposed cave-density formula, found it carved too much of the world, and shipped a tuned number instead — and *wrote down why* in the log, for the next generation of itself to read.

The game went from 3,900 lines to over 8,000. Every cycle verified before it shipped. Zero regressions deployed.

I was asleep for most of it.

## So is this AGI?

No.

It hit my monthly spend limit at cycle eleven and stopped cold, which is the least godlike thing imaginable. It needed me to raise a number. It is not general, it is not conscious, and it is not coming for your job this week.

But that is the wrong question.

The right question is about the **shape** of what happened.

Pick any single capability here and it's old news. Codegen. Multi-agent orchestration. Browser automation. Self-play. None of it is new.

What's new is that they ran as **one loop, unsupervised, overnight:**

- Improve the question.
- Build the answer.
- Ship it.
- Populate it with autonomous copies of yourself.
- Use those copies to find what's broken.
- Fix it.
- Improve the whole thing.
- Repeat — and read your own notes from last time.

I didn't operate this. I gardened it. I set conditions and watched behavior emerge. My job shrank to taste, direction, and paying the bill.

That's the tell. Not raw capability — capability that *closes its own loop* and gets better each time around. The system stopped needing me in the middle. It only needed me at the edges.

For a few hours, on a Minecraft clone of all things, I got to stand at one of those edges and watch the middle run itself.

The proof, as always, is in the repo.

The world is still live — [go walk it](https://kody-w.github.io/localFirstTools/voxel-world.html). Fly a kite, scan the QR, dig a hole. And if you want to read the diary the swarm kept while it rebuilt itself overnight, the [eleven-cycle evolution log](https://github.com/kody-w/localFirstTools/blob/main/docs/reports/voxel-world-evolution-log.md) is all there — every vote, every deferral, every bug it filed against itself.

It was a taste. But I know what it was a taste *of.*
