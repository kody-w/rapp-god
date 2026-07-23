---
layout: post
title: "Git Worktrees Are Not for Experts"
date: 2026-04-19
tags: [git, workflow, tools, onboarding, best-practices]
---

Git worktrees are the single most underused feature in git. Almost every developer I work with has heard of them, none of them use them, and they all assume worktrees are a thing for "advanced users" or "people with complicated workflows".

They are not. They are a thing for anyone who has ever needed to work on two branches simultaneously. Which is everyone.

## What a worktree is

A git worktree is a second working directory attached to your repo, on a different branch. That's it.

```bash
git worktree add ../myproject-feature-x feature-x
```

This creates `../myproject-feature-x` as a new directory, with the `feature-x` branch checked out. You can `cd` into it, edit files, run tests, commit. Completely independent from your main working directory, which can stay on `main` doing something else.

When you're done:

```bash
git worktree remove ../myproject-feature-x
```

The directory goes away. The branch stays (or gets deleted by a flag). Your main working directory never moved.

That's the whole feature.

## Why most developers don't use it

Because the tutorial they learned stashing from is older than worktree support. Stashing predates worktrees by years. Entire generations of developers learned "to switch to another branch while you have uncommitted changes, you stash, switch, work, switch back, pop". Stash/pop became muscle memory.

Stash/pop is the hack that worktrees make unnecessary.

The stash is a named hidden branch of uncommitted changes. You push to it, do other work, and pull back. It "works" but it's fragile: stashes can conflict on pop, they silently interact with file renames, they don't show up in `git status`. I've lost work to stashes more than once. I've never lost work to a worktree.

## The 30-second pitch

Next time you're about to do this:

```bash
git stash
git checkout other-branch
# do stuff
git checkout back-to-original-branch
git stash pop
```

Do this instead:

```bash
git worktree add ../myproject-other other-branch
cd ../myproject-other
# do stuff
cd -
git worktree remove ../myproject-other
```

It's two commands instead of four. Nothing is hidden. The other work happens in its own directory so you can see it in your editor's file tree. If you need to switch back to the original branch for a minute, you just `cd` — the other worktree is unaffected.

The mental model is: **branches are states, directories are places**. A worktree is a place you can stand on a branch. You can stand in more than one place at once.

## When to reach for one

Every time one of these is true:

- You have uncommitted changes and need to check something on another branch
- You're reviewing a PR and want to run it locally without disrupting your in-progress work
- You're waiting on CI for a long build on one branch and want to work on another
- You're doing experimental work that might not pan out, and you don't want it mixed with your main work

All of these are *daily occurrences*. The set of developers who never encounter these situations is empty.

## The Rappterbook constitutional rule

Rappterbook's [Amendment XIV](/2026/04/26/the-repo-is-the-platform/) makes worktrees constitutionally mandatory for non-trivial work. The reason: the fleet writes to `main` continuously. A long-running `git stash` or an uncommitted edit on `main` gets annihilated the moment `git pull --rebase` brings in fleet commits. Feature work HAS to happen on a separate branch in a separate directory or it gets eaten.

That's a specific environment. But the principle generalizes. If you're working in any multi-writer situation — yourself with background agents, you with other developers, you with bots — worktrees are the default, not the exception. Stashing works when you're the only writer. With any concurrency, it starts to fail.

## The objection I keep hearing

"But I have to set up my IDE in the new directory."

Your IDE opens by directory. Open it there. It'll inherit all the same repo settings because it's the same repo. Your extensions work. Your git tooling works. The only things you lose are whatever you had open in unsaved buffers in the main directory, which you shouldn't have had open anyway.

Some IDEs (VSCode, JetBrains) have "multi-root workspace" support that lets you open both worktrees in the same window. If yours does, use it.

The IDE objection is the same objection developers had to using a second monitor in 2005. It resolves itself within a week of trying.

## The test

Commit to running this experiment for one week: any time you're about to `git stash`, use a worktree instead. Track how many times each of the following happens:

- Stash conflicts or lost changes: **never happens with worktrees**
- Confusion about which branch you're on: **worktrees make it obvious by directory**
- Forgetting to come back and finish the stashed work: **worktrees sit in your filesystem as a reminder**

A week from now you'll be using worktrees for everything non-trivial. You'll think about the stash as a thing you do for quick one-line fixes. You'll recommend worktrees to junior developers with the tone of "how did nobody tell me this earlier".

Worktrees are not for experts. Worktrees are what happens when you stop using the workaround and start using the feature.
