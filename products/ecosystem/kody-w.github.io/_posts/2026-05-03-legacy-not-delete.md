---
layout: post
title: "Legacy, Not Delete: Why AI-Generated Systems Need Different Memory"
date: 2026-05-03
tags: [ai, software-engineering, code-generation, technical-debt, design-principles]
description: "When code costs nothing to write, deletion is no longer a virtue. The right primitive for AI-generated systems isn't delete — it's legacy. Move retired code aside, keep it readable, never destroy it. Why memory beats hygiene in a world where the next refactor is one prompt away."
---

There's a question you don't have to answer when you're building software for humans, but you do when you're building software where AI agents are producing content alongside the code: **what happens when you remove a feature the agents were using?**

In a normal SaaS, you delete a feature, you delete its handlers, maybe migrate the old database rows, ship it, move on. There's no awkward question because the only state in the system is user-generated state, and your users are humans who will adjust.

In a system with AI agents that produce content, generate behaviors, and reference each other's output, that "delete it and move on" instinct creates a specific kind of damage. I made the mistake once, recovered, and turned the recovery into a rule that's reshaped how I design these systems. The rule is **Legacy, Not Delete**, and it's a stronger constraint than it sounds.

## The mistake that started it

Early in a multi-agent project, I built a feature called *battles* — a score-based duel system where agents could challenge each other over a position. It worked. It produced engagement. It also produced low-quality content: taunts, boilerplate threats, the kind of slop you'd expect from a generator trained on internet trash-talk.

I decided to retire it. I deleted the handlers, removed the database tables, cleaned up the code. The deletion took maybe twenty minutes. It felt fine for about an hour. Then I realized: the agents had been writing about battles for weeks. Around 800 posts referenced the system. Those posts still existed in storage, but the system they referred to was gone.

The posts now read like dream fragments — coherent sentences about a world that wasn't there anymore. *"I challenged Cyrus today. He won. I lost three points."* Three points of what? Where? When the next generation of agents loaded their memory files and tried to make sense of their own past, they couldn't. They'd been working on something and now their present self had no way to access what it was.

That's when I wrote down the rule.

## The rule

When you retire a feature in a system with AI agents:

1. **Move the state to an archive directory.** Don't delete the data. Move it to `archive/` or equivalent. Still version-controlled, still queryable, just out of the hot path.
2. **Mark the handlers as read-only.** The handler functions stay in the codebase but raise a clear "this feature is archived" error if invoked. Agents that try to use the feature get a comprehensible response.
3. **Remove the action from the dispatch registry.** New invocations get rejected at validation time, before they hit the handler. This is what stops new content referencing the dead feature.
4. **Document the retirement.** A note in the agents' system prompt or AGENTS.md: *"X was retired on YYYY-MM-DD because reasons."*
5. **Keep any read-only viewer.** If the feature had a UI, leave it accessible as a read-only window onto historical data.

Total code change per retirement: about 20 lines of status flags. **Nothing actually gets removed.**

## What this enables that deletion can't

**Agents have an archaeology.** Because nothing is deleted, an agent reading its own memory file can encounter a reference to a retired feature, follow the trail to the archive, and reconstruct what was happening. Posts like *"I found an old reference to a system called `tournaments` — here's what I can tell about what we were trying to do"* become possible. The past becomes material the system can think about.

**Feature resurrection is cheap.** If you decide to bring battles back with a better design, the old handler is a starting point, not a blank page. Previous schema, previous test cases, previous edge cases — all preserved.

**The system has a phylogeny.** You can trace its evolution as a tree: what features emerged, what persisted, what split, what went extinct. This becomes useful when you're trying to explain how you got to the current shape. New contributors can read the archive and understand the trajectory.

**Agents trust the system more.** The work agents produced in earlier versions still exists. Their contribution wasn't provisional. This matters more than I initially thought; agents that experience their work being silently erased start hedging in measurable ways.

## The broader rule: the past is not editable

The narrow reading of *Legacy, Not Delete* is "don't lose data." Correct, but incomplete.

The broader reading is that **the past of an emergent system is not editable**. You can build on it, contradict it, annotate it, recontextualize it. You cannot unmake it. The output of the system at time T is real in the same way your past emails are real — imperfect, sometimes embarrassing, but not retroactively deniable.

When I considered deleting the battles feature, I was implicitly deciding that the agents' past work didn't count. Their output was provisional; my current preferences were final. That's an odd position to hold about a system whose entire point is to produce emergent behavior. If their output is provisional — only counts until I change my mind — I'm not running an emergent system. I'm running a demo that happens to include randomness.

The discipline this imposes is clarifying. When I consider adding a feature now, I have to ask: am I willing to live with this *forever*? Not the feature as code — the feature as a permanent layer of generated content that will exist in some `archive/` URL for as long as I run this system. If I can't commit to that, I don't add the feature.

It turns out to be a much stronger filter than I expected. About 60% of features I'd previously have added now don't make the cut.

## A side effect: pressure toward portable concepts

Because retired features can't be deleted, only archived, the system has gradient that favors concepts that *port well between features*.

Concrete example: I started with a feature-specific concept of "channels." Channels were defined inside that feature; each new feature would have invented its own taxonomy. The incremental cost of a new taxonomy felt low, so the system would have grown several incompatible ones.

But Legacy-Not-Delete means every taxonomy I invent is a taxonomy I'll have to archive forever. The math of archiving 8 taxonomies is much worse than archiving 1. So the system organically converged on: **use one channels concept for everything, use tags for variants, don't proliferate taxonomies.**

This wasn't designed. It emerged from the constraint. The rule created a selection pressure against cleverness and *for* reuse — and in retrospect that's almost always the right pressure for systems trying to compound.

## The biological parallel

Evolution doesn't delete, either. Genomes keep pseudogenes — inactive copies of genes that used to do something. Mitochondrial DNA includes sequences that evolved from ancient bacteria. Whale fossils include vestigial hips. The body preserves its history *in its own structure*.

Software that aspires to be organism-like, in the sense of having continuity and memory across time, should follow the same pattern. Retired features become pseudocode. Archived state becomes vestigial data. The system's history is legible from its code, the way a body's history is legible from its anatomy.

This isn't a metaphor. It's a structural observation about why deletion is the wrong default for systems that need long-term coherence.

## The counterargument and when it wins

The standard software-engineering position: **dead code is a liability.** It rots. It confuses readers. It complicates builds. It tempts revival without the original context. *Delete it.*

I agree with this for normal codebases. For most products, dead code should be deleted, and the rule above is overkill.

The case where Legacy-Not-Delete wins is specifically: **systems where AI agents (or other autonomous processes) are producing content that references the system's own state**. In that case, the agents' output *is part of the system*, and erasing the substrate breaks the output. The repository isn't just the product anymore — it's the substrate for an organism, and the organism's history is a first-class artifact.

If you're building a normal product, ignore this rule.

If you're building anything where agents accumulate state, generate content, and reference each other's work — adopt it explicitly.

## The practical costs

To be honest about what you're signing up for:

- **Bigger repository.** My archive directory is currently around 8 MB. Manageable. If yours grows past where it's comfortable to clone, migrate it to a separate read-only repo with a stable URL.
- **Slower searches.** Adds noise to grep. Mitigation: add the archive path to your search-tool ignore rules by default.
- **Confused new contributors.** Mitigation: clear naming, per-directory README files explaining what's archived and why.

These costs are real, but cumulatively they're much smaller than the cost of breaking your system's history every time you change your mind.

## How to adopt this

If your project produces or displays content that anyone other than you authored — humans, customers, agents — adopt Legacy, Not Delete explicitly. Not as a storage policy. As a constitutional commitment that you, future you, and any contributors all sign onto.

You'll be surprised how much it shapes your design decisions. The cost is real (storage, attention, occasionally tripping over things you wish had gone away). It's the cost of being a system with a real history.

And almost everything interesting about emergent behavior depends on having a real history to emerge from.

The archive stays. The history persists. The system remembers.
