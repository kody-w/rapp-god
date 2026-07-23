---
layout: post
title: "Land the Plane: Work Isn't Done Until It's Pushed"
date: 2026-04-18
tags: [discipline, workflow, git, completion, doctrine]
---

A rule that has saved me from more wasted work than any other practice: **work is not complete until `git push` succeeds.**

Not when the code is written. Not when the tests pass. Not when the commit is made locally. Not when you've told yourself "I'll push it tomorrow." The work is complete when the remote acknowledges the push and you can fetch your own commit back from a fresh clone. Until then, the work exists only on one machine, and one machine is a tragedy waiting to happen.

The corollary: never end a session in a state where the work is locally committed but not pushed. That state is the worst possible resting point. The local repo thinks the work is done. The remote has no idea the work exists. Anyone collaborating sees stale state. The next session has to remember "oh right, I had something uncommitted from last time" — except by the time you remember, the laptop has been reimaged, the temp directory has been cleaned, the branch has been deleted by some helpful script, and the work is just gone.

I call this discipline "land the plane." Pilots don't get credit for a flight when the plane is in the air over the destination. They get credit when the plane is on the ground, the brakes are set, and the engines are off. Software work is the same. Code in flight is not delivered code.

The mandatory checklist at the end of every work session, in order:

1. **File issues for any remaining work.** Anything you noticed but didn't finish gets a tracked record. Future-you will not remember it. Issue tracking is durable storage for incomplete thoughts.

2. **Run quality gates.** Tests, linters, builds. Whatever the project requires for "ready to merge." This is non-negotiable even if you're confident — confidence is not a quality gate.

3. **Update issue status.** Close finished issues. Mark in-progress work as in-progress. The issue tracker should reflect reality at the end of every session, not just at sprint boundaries.

4. **Push to remote.** This is the actual landing:
   ```
   git pull --rebase
   git push
   git status   # MUST show "up to date with origin"
   ```
   If the push fails, resolve the conflict and retry. If the rebase is messy, deal with it now. Do not leave for tomorrow.

5. **Clean up.** Clear stashes, prune merged branches, remove orphaned worktrees.

6. **Verify.** Pull from a fresh clone or check the remote in the browser. Confirm the work is actually visible to other consumers.

7. **Hand off.** Write a short note about state — what's done, what's next, where things sit. Leave breadcrumbs for the next session.

The thing that makes this discipline hard is that step 4 is the most boring step. The interesting work happened in steps before that. The instinct is to move on as soon as the interesting work is done. The instinct is wrong. The interesting work doesn't exist as a real artifact until it's landed.

A few common failure modes that landing-the-plane discipline catches:

- **The "ready to push when you are" anti-pattern.** Saying "I'll push when you give the word" is a way to stop short. Push the work. The reviewer can pull. There is no need for a manual handshake before the push.
- **The orphaned local branch.** A branch that exists only on your laptop is one disk failure away from oblivion. Push every branch. Delete branches by deleting them on the remote, not by leaving them locally.
- **The "I'll commit after lunch" trap.** You will not commit after lunch. After lunch you will start something new. The work in progress at noon will be in progress forever. Commit before lunch. Push before lunch. Then start fresh after.
- **The autostash hazard.** A `git pull --rebase` with uncommitted changes will autostash, attempt the rebase, and try to pop the stash. If the pop conflicts, you may end up with merge markers in files you didn't realize had changed. Commit before pulling, always.

The discipline is small. The payoff is enormous. Every session that lands cleanly is a session whose work compounds. Every session that doesn't land is a session that didn't really happen.

Land the plane.
