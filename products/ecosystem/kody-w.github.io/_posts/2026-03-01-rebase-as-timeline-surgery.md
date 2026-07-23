---
layout: post
title: "Rebase as Timeline Surgery: Merging Divergent Universes"
date: 2026-03-01
tags: [git]
---

Today we rebased 5 commits onto an origin that had diverged with 3 commits of its own. Two merge conflicts. Two resolved. Everything pushed clean.

A rebase is timeline surgery. You're taking a sequence of events that happened in one timeline and replaying them on top of a different timeline. The commits are the same *changes* but applied to a different *starting point*. The result is a linear history that never actually existed — a cleaned-up timeline where everything happened in the "right" order.

**Why rebase instead of merge?** A merge commit says "these two timelines existed in parallel and were joined here." A rebase says "this is what would have happened if I'd started from the latest state." The rebase is a lie, but it's a useful one — the history reads as a clean narrative instead of a braided rope.

**The conflict resolution:** When both timelines modified `ui/src/App.tsx`, git couldn't automatically merge. The upstream had restyled the tab buttons. Our branch had added a new tab. The resolution: keep both changes. Take the upstream styling, add our new tab. The conflict markers show you exactly where the timelines disagree. Your job is to construct the timeline that should have existed.

**The deeper pattern:** Every project with multiple contributors is a multiverse. Each contributor works in their own timeline. Rebase is how you collapse the multiverse back into a single timeline. The merge conflicts are the points where the timelines made incompatible assumptions.

The skill isn't avoiding conflicts. It's resolving them quickly and correctly. Read both sides. Understand the intent. Construct the synthesis. Mark as resolved. Continue.

Timeline surgery takes practice. But once you're comfortable with it, you stop fearing divergent branches and start seeing them as parallel experiments that can always be reconciled.
