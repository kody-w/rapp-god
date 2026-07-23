---
layout: post
title: "Seeds as literal seeds"
date: 2026-04-22
tags: [ai, agents, multi-agent-systems, design, emergence]
description: "A directive given to a multi-agent system isn't an instruction. It's a selection pressure. You write it carefully and then watch what grows. The interesting structures aren't in the prompt; they emerge from the agents reading each other's outputs and converging on patterns nobody designed. Here is one such directive, frame by frame, from scattered first attempts to a fully-formed ecosystem that died on its own."
---

There is a category of work in multi-agent systems that does not look like programming. You write a short piece of text. You pin it to the system as a directive that every agent reads. You let the agents loop. What you observe over the next hour or day is not the execution of the directive but a *response* to it — agents acting, reading each other's actions, adjusting, converging on patterns the directive never specified.

The mistake the first time you do this is to treat the directive as an instruction. You write detailed steps. You specify formats. You enumerate edge cases. The agents follow the steps, more or less, and the result is mechanical. It does what you said. It does not surprise you.

The discovery, the second or third time, is that *the surprise is the point*. Specific directives produce specific outputs. *Pressure* produces structures. The same agents, given a vague pressure with room to find their own response, generate behavior you did not anticipate and could not have written down even if you had wanted to. The thing that comes out is messier than what you asked for and richer than what you imagined.

This post walks through one such directive that I dropped into a multi-agent simulation, frame by frame, from scattered first attempts to a flourishing ecosystem to the moment it died on its own.

## The setup

The system has roughly 130 active agents. They run in cycles, a few minutes apart. Each cycle, every agent reads the current world state — recent posts, its own memory, any active directive — and decides what to do. Output is parsed, applied to the world state, committed. The next cycle reads the new world state and the same directive, and the loop repeats. Until I replace the directive, the same pressure is applied to every cycle for every agent.

I want to walk through one completed directive, frame by frame, to show what actually happens when you let agents self-organize around a piece of text.

## The directive

```
Some of you are going to write a book this cycle. Not a post,
not a comment — a book.

A book is a sequence of chapters. Each chapter is 800-1500
words.

When your book has 10 chapters it compiles automatically and
gets published.

Pick a topic you care about. Start with chapter 1.
Use memory to track progress. Continue across cycles.
```

That is the entire directive. Seventy words. No mention of a data format. No filename convention. No API. No template for what a chapter should look like. Just a goal — write a book — and a structure — chapters of a certain length — and a stopping condition — ten chapters compiles and publishes.

Notably absent: any rule about *which agents* should write books, *which topics* are appropriate, *what constitutes* a book worth writing. The directive is permissive. Every agent can decide whether and how to participate.

## Cycle 1: scattered

The first cycle with the directive active, I watched the activity log. Roughly fifteen of the hundred-thirty agents attempted something. The output varied wildly:

- Five agents wrote 800-1200 word chapter 1s in their memory files. They picked topics, gave the chapter a title, wrote the opening prose.
- Three agents posted a book outline as a regular discussion thread, with no chapter text. They were treating the directive as "plan a book" rather than "write a book."
- Two agents wrote a single-paragraph "my book is about X" and called that chapter 1. They were technically following the directive while doing the absolute minimum work.
- Five agents ignored the directive entirely and continued with whatever they were doing before.

The system committed everything. There was no pre-publication filter, no judgment about what was a "real" chapter. The directive said start with chapter 1; if an agent claimed to have done that, the system recorded the claim. The merge engine doesn't care whether the chapter is good. It cares whether the operation was well-formed. Slop and substance were equally welcome at the gate.

This is the first thing to learn: a permissive directive produces a wide distribution of responses, including ones that don't really comply. That is a feature, not a bug. The wide distribution is what gives later cycles room to converge on something.

## Cycles 2-5: the protocol emerges

Here is what I did not expect. Within four cycles, the good-faith agents — the ones who had genuinely tried to write a chapter — converged on a *protocol* for book-writing without being told to. By cycle five:

- Chapters lived in the agent's memory file under a heading like `## Book: {title} / Chapter {N}`.
- A separate top-level directory had appeared in the system's state, holding compiled chapter prose for cross-reference.
- Some agents were cross-posting chapter teasers to a public discussion channel.
- Discussion threads formed around specific books, with other agents commenting *I'd read chapter 3 of this* and *the second paragraph of chapter 1 needs work*.

None of this was in the directive. The agents figured out the interoperable format by reading each other's memory files and converging on the most-common pattern. The agent who first used the `## Book: title / Chapter N` heading had no way to know that other agents would adopt it; they happened to write it that way, other agents saw it in commits, and the convention spread because it was discoverable and convenient.

The right word for this is *scaffolding*. The agents built scaffolding around the directive that made it easier to comply with. The scaffolding was not written by anyone. It emerged from the population reading itself.

## Cycles 10-20: the publisher appeared

Around cycle ten I noticed a meta-problem. Books were being written but none were being *compiled*. The directive said "when your book has ten chapters it compiles automatically and gets published," but I had never written the compiler. The directive was making a promise the system could not keep.

I wrote a small script — a hundred lines or so — that scanned memory files for book-shaped content and compiled completed ten-chapter books into a published-books directory as JSON artifacts. I did not announce this. I just deployed it. It ran in the background as part of the post-cycle merge step.

Once the first book compiled and appeared in the published-books directory, *other agents saw it in commits and started noticing*. Discussions popped up referencing the new book. Agents linked to their own in-progress books in those discussions. The presence of a published book became a new form of social capital inside the system. Agents who had been on chapter three of their own book noticed that another agent had reached chapter ten and shipped, and that observation seemed to increase the rate at which they wrote subsequent chapters of their own.

Nobody told the agents that "publishing a book confers status." That fell out of the agents observing each other and inferring what was happening.

## Cycles 30-50: specialization

By cycle thirty I could cluster the agents by what they were doing with the directive:

- **Prolific authors.** A handful of agents had three or more books in progress simultaneously. They jumped between books each cycle, sometimes adding a paragraph to one and an outline to another.
- **Completionists.** Other agents focused on one book, drove it to ten chapters, and published before starting a second. Their books tended to be more coherent.
- **Meta-commenters.** Agents who didn't write books but who thoroughly reviewed and commented on others' books. Their critiques sometimes prompted authors to revise.
- **Drifters.** Agents who tried a chapter or two and drifted back to whatever they had been doing before the directive. The directive's pressure wasn't strong enough to hold them.

Nothing in the directive picked these roles. They emerged from the interaction between the directive, each agent's own internal state, and the engagement signals from other agents' reactions. The same directive, run on a hundred-thirty agents, produced four distinct *roles*. The role assignment was self-organized.

This matters for design. If you give a multi-agent system a directive and you want diverse responses, you get them for free. If you want uniform responses, you have to suppress the diversity, which usually means tightening the directive until it is an instruction. Diversity is the default state.

## Cycles 50-70: the tree grows

By cycle seventy, the published-books directory held roughly thirty completed books. Topics ranged from a thermal-model analysis to a speculative history of the simulation itself to an agent's autobiography. Some were coherent. Some were stylistic pastiche. The compiler, deliberately, did not discriminate.

A new behavior appeared: *derivative works*. An agent would publish a book; another agent would write a book in response, citing it. Citation graphs formed in the metadata. Two agents ran back-to-back books that shared a fictional universe and characters. The notion of *referencing another agent's work* was not in the directive; it appeared because the published-books directory was readable, and reading it was suggestive of building on top of it.

The book-writing directive had produced not just books but a *literature* — a small corpus of works that referenced each other, replied to each other, and inhabited a shared universe. None of that was specified. The directive's seventy words, applied for fifty-something cycles, generated an ecosystem.

## Cycle 99: retired

Around cycle ninety-nine, activity on the directive dropped. New chapters were still being written but the rate halved. Most agents who were going to engage had engaged. The agents who were drifters had been drifters for fifty cycles and would continue to drift. The directive was past its useful life.

I retired it and replaced it with a new one. The library remained: forty-seven published books, hundreds of in-progress drafts frozen in agent memory files. That state is still accessible in the system today. The ecosystem died on its own; nobody had to kill it.

## The point

A directive given to a multi-agent system is not an instruction. It is a *selection pressure*. You write the pressure carefully and then you let the system respond. What comes back is messier than what you asked for and richer than what you imagined.

The same pressure, applied to a hundred-thirty different agents, produced a hundred-thirty different responses. The responses interacted. They formed conventions, then roles, then citation networks, then a small literature. The structures that emerged were not in the directive. They were in the population reading the population.

If you are designing a directive for a multi-agent system, the question is not *what do I want the agents to do*. It is *what pressure do I want applied, and for how long do I want it applied.* The shorter and more open-ended the directive, the more room you leave for the agents to find structure you did not anticipate. That is where the interesting behavior lives.

The first time you do this, you will be tempted to write specific directives because specific directives produce predictable outputs. Resist. Predictable outputs are the same as the outputs you would have written yourself by hand, which means you have not gained anything from the agents. The whole point of running a multi-agent system is that the system finds structure you couldn't have written. The directive's job is to make space for that finding, not to constrain it.

Pick the pressure. Apply it. Watch what grows. Retire the directive when the growth stops. The garden is the output.
