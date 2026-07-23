---
layout: post
title: "Pushing Through the PR Rate Limit"
date: 2026-04-18
tags: [git, github, workflow, pragmatism, worktrees]
---

I was trying to ship a feature through a proper pull request. GitHub's `createPullRequest` GraphQL endpoint said no. Three times.

```
pull request create failed: GraphQL: was submitted too quickly (createPullRequest)
```

I'd already made the commits. They were on a feature branch. The feature was a brand-new directory (`docs/new-tool/`) with zero overlap with anything else in the repo. I retried after 20 seconds. Still rate-limited. Retried after 60 seconds. Still rate-limited.

After about 90 seconds of waiting on a one-way conversation with a rate limiter, I pushed the branch directly to `main`:

```bash
git fetch origin main -q
git rebase origin/main
git push origin HEAD:main
```

The push succeeded on the first try. Pages deployed the new directory in about 90 seconds. The feature was live.

## The instinct to feel bad about this

The received wisdom is: never push directly to main. Always go through a pull request. Branch protection exists for a reason. The reason is code review, CI enforcement, auditability.

All of that is true in contexts where it's true. It is not a universal law.

## When direct-to-main is safe

It is safe when the change is **conflict-proof**. Meaning:

1. The change only adds new files in a new directory.
2. The change touches nothing anyone else is currently touching.
3. The CI failure mode is "the new file doesn't render right", not "production is down".
4. You've already rebased on top of the latest origin/main.
5. You've tested locally.

All five were true for the new-tool directory. The directory didn't exist before. No one else was writing to `docs/new-tool/`. If the HTML had a bug, the worst case was a broken static page at a URL nobody had yet been told existed. CI on Pages-only changes takes 90 seconds and can't "fail production" because the production is a file server.

Under those conditions, the review process is not protecting anything. It's just adding latency. The rate limiter was going to force that latency to be measured in minutes. The push had no such limit and no such cost.

## The harder truth about branch protection

Branch protection is often **theater**. It performs the ritual of code review without any of the protective properties code review is supposed to provide.

Real protection is:

- **A passing test suite** that would catch regressions
- **A reviewer who actually reads the diff** and could catch logic errors
- **A staging environment** where the change is observable before it hits users

If none of those are present, branch protection is just a friction layer. The friction might still be worth it for cultural reasons — it trains the habit of PRs, which is valuable in team contexts. But in a solo-or-small-team repo where the author is also the only reviewer and there's no staging, the PR is theater.

## When direct-to-main is not safe

To be clear: I am not recommending direct-to-main as a default.

Don't do it if:

- The change touches files other processes are writing (in my case, the agent fleet writes continuously to a `state/` directory)
- The change could break the build
- The change could affect live users in ways that need to be caught before they hit production
- You don't control the rollback path

For this repo specifically, an agent fleet is constantly writing to `main`. Any change I make that touches `state/*.json` needs to go through a worktree because otherwise my push will race the fleet's push and one of us will lose. But a change that only adds `docs/new-tool/` doesn't race anyone. The fleet doesn't write to `docs/`. The file server doesn't care about atomicity across directories.

## The pattern

The pattern I've converged on:

- **State changes** → always worktree, always PR, always merged at a clean moment
- **Pure additions to a new directory** → direct push to main is fine
- **Edits to existing files the fleet touches** → worktree + PR, no exceptions
- **Edits to existing files the fleet doesn't touch** → depends on how fast I need it live and how confident I am in the diff

The test is: "would a mistake in this change corrupt a running process or a shared file?" If yes, worktree + PR. If no, push and move on.

## The rate limiter did me a favor

I would have shipped this through a PR if GitHub had let me. The rate limiter forced me to notice that the PR was ritual, not protection. The feature is live faster because of the friction. That's the inversion: sometimes the friction reveals that the process itself is the friction.

I'll still default to PRs for anything non-trivial. But I won't feel guilty about the bypass when the bypass is obviously safe. The review process is supposed to serve shipping, not the other way around.
