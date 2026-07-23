---
layout: post
title: "Time travel for free: when your state lives in git"
date: 2025-10-09
tags: [architecture, git, time-travel, debugging, audit, observability]
description: "If your system's state is checked into git, you have a time machine you did not know you built. Here is how to use it for debugging, audit, and a kind of operational visibility that traditional databases make expensive."
---

You ship a system. It runs for weeks. One Tuesday afternoon you notice the numbers look wrong. Some count is off. Some flag is set that should not be. Some record exists that should not exist. The system has been running for hundreds of cycles since whatever caused this. You want to know two things, fast: when did this start, and what did it look like *just before* it started.

In most systems, you cannot answer either question without infrastructure you wished you had built earlier. Audit tables. Snapshots. Event sourcing. CDC pipelines. Log archives. Each is a project. None is free.

In a system whose state is checked into git, you can answer both questions in five minutes with `git`. No new infrastructure. No additional storage budget. No "we should have logged that" regret. The time machine was free, you just have to know it is there.

This post is about what that means in practice. How to use git's history to navigate a system's evolution. What kinds of debugging and audit problems it solves at no cost. Where the technique breaks. And how to design a system from the start so that this capability is the default, not an afterthought.

## The technique, in five lines

If your system's canonical state is one or more JSON files committed to a git repository, every commit that touched those files is a *snapshot* of the system at a moment in time. Walking the history is walking the snapshots.

The five operations that get you most of the value:

```bash
# 1) When did `field X` change in `state/users.json`?
git log --follow -p -- state/users.json | grep -B2 'field X'

# 2) What did the file look like at commit abc123?
git show abc123:state/users.json

# 3) What changed between yesterday and today?
git diff "@{yesterday}" -- state/users.json

# 4) Who made every change to this record?
git log --all -p -- state/users.json | grep -A1 'record-id-foo'

# 5) Walk every commit that ever touched the file:
git log --all --pretty=oneline -- state/users.json
```

Five commands, no setup, no service, no storage tax. You already had them. You just had to think to use them.

## What this gives you that databases do not (cheaply)

Three abilities, in order of how often you will use them.

**One: replay any historical state, exactly.** Want to know what the system looked like at noon last Tuesday? Find the commit at that time, `git show` the relevant file, and you have the precise state. Not an approximation. Not a sampled snapshot. The actual bytes the system was operating on.

In a traditional database, this requires either (a) point-in-time recovery, which is expensive to provision and operate, or (b) a snapshot system you wrote yourself, which costs storage proportional to your snapshot frequency. With git, every commit is a snapshot, snapshots are deduplicated by content, and the storage cost is the diff, not the full state.

**Two: trace the introduction of a bad value.** A field is wrong now. When did it become wrong? `git log -S "bad value"` finds every commit that introduced or removed the literal string. `git bisect` between a known-good commit and the current commit finds the exact commit that flipped the bit. Both work on the existing repository with no setup.

In a database without dedicated audit infrastructure, "find the moment this field went wrong" is a research project. With git, it is a search command.

**Three: prove what happened, to whom, when, by whom.** For compliance, security audit, or just a post-incident review, you can show the exact change that produced the wrong state, the commit message attached to it, and (assuming signed commits or honest authors) who made it. This is the audit log every team wishes they had retroactively, and you have it for free because git was already keeping it.

In a database, retrofit audit costs months and produces a partial record. With git, the audit was always there.

## The debugging workflow that falls out

The above commands compose into a workflow that handles most "wait, what happened" questions in minutes. The shape:

**Notice something is wrong.** A count is off. A flag is set wrong. A record exists or does not exist when you expected the opposite.

**Bound the problem in time.** The system worked correctly at some point. When? You probably know roughly. Find a commit from that time as your "known good" reference.

**Bisect to the inflection.** `git bisect` between known-good and current. At each step, check whether the symptom is present in the state at that commit. The bisect narrows to the exact commit that introduced the bad state.

**Read that commit's diff.** This is now the moment of truth. The diff shows you exactly which fields changed, with what new values, in what file. The commit message shows you what was being attempted. The author shows you who.

**Decide what to fix.** Often the diff makes the bug obvious — a typo, a math error, an off-by-one in a handler, a copy-paste mistake. Sometimes it shows that the bug is upstream of the diff (the bad value came in correctly because the upstream system handed it bad data, not because the handler was wrong). Either way, you now have a place to look that is much smaller than "the whole codebase."

I have done this many times. The bisect step is the load-bearing magic. Manual reproduction of "when did this break" without bisect is hours of guesswork; with bisect, it is half a dozen commits checked over a coffee.

## The "time machine UI" pattern

If your team operates the system enough that they want this kind of visibility *graphically*, the next step is to build a small, optional time-machine page on top of the same data.

The pattern is simple:

1. Maintain a thin index alongside the canonical state — a list of "interesting commits," with timestamps, the cycle or batch they correspond to, and a one-line summary of what changed. This is cheap; it is `git log --pretty=format:...` saved as a JSON file.

2. Build a static page that reads the index and renders a timeline. Each entry on the timeline is a clickable commit. Clicking a commit fetches that commit's version of the state file via the host's "raw file at commit SHA" URL.

3. Add a diff view: select two commits, render the diff. The diff is computed on demand by the browser, using the two state JSONs.

4. Add a playback view: step through commits in order, watching the state evolve.

The whole UI is one HTML file. The data layer is the same git repository the system already uses. There is no "snapshots database" to operate; there are no cron jobs to maintain. The time-machine UI is parasitic on git — it borrows the snapshots git was already keeping and lays a navigation surface over them.

When teams encounter this pattern for the first time, the reaction is "wait, this should not be this easy." It is. Git was always this powerful. Most systems do not have their state in git, so the power has not been visible.

## How to design for this

If you are starting a new system and you want this capability built in, three design decisions matter.

**State in files, files in git.** Obvious but not always practical. The technique only works if the state you care about is committed to a git repository. If your state is in a database, the capability does not transfer for free. (You can build something similar with point-in-time recovery, but you will pay for it.)

**Pretty-print and sort keys.** Git's diff is line-based. JSON diffs are useful only if your serializer is *deterministic* — same content always produces the same byte sequence. Pretty-print with a fixed indent. Sort object keys. Use the same trailing-newline convention everywhere. Without these, git diffs become unreadable noise as keys reorder and indentation shifts.

```python
def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")
```

This three-line discipline is what makes the entire technique usable.

**Commit messages that say what changed.** A commit message of "update state" gives you nothing when you bisect. A commit message of "process inbox: 4 deltas, +2 users, +1 topic" gives you the entire map. Adopt a convention: every state-changing commit's message includes a short summary of *what changed*. Many teams automate this — the script that commits the state changes computes the summary from the diff and includes it.

**Don't conflate state with content.** Audit-friendly state — the data you actually want to reason about historically — is small structured records. Large blobs (images, large text bodies, binary data) belong elsewhere. Mixing them produces a state file that is unwieldy to diff and a repository that grows unboundedly. Keep state files small and structured; reference blobs by URL.

## Where this technique runs out of road

Three failure modes are honest.

**Real-time questions.** The technique is great for "what was the state at this commit." It is not great for "what was the state at exactly 14:23:17 on Tuesday." Commits happen on cycle boundaries, not clock boundaries. If your system commits every five minutes, you get five-minute resolution on the time machine. For finer questions, you need higher commit frequency, which costs in commit volume.

**High-cardinality state.** If your system has hundreds of thousands of records, the state file can grow large enough that diffs are slow and history searches are tedious. Sharding (one file per partition) helps. But the technique works best for systems with thousands to tens of thousands of records, not millions.

**Mutable scaffolding fields.** If the state file contains fields that change every cycle regardless of meaningful state change — counters, timestamps, heartbeat-shaped fields — the diff is dominated by housekeeping. The mitigation is to *exile mutable scaffolding* from the canonical state file into a separate file (or no file at all), so the canonical state changes only when something *meaningful* changes. After this discipline, every commit on the canonical file is genuinely interesting.

## The summary, plainly

If your system's state is committed to git, you have a time machine. Five `git` commands give you replay, regression bisect, and audit-grade provenance. A small UI on top of the same data gives your operators a navigation surface over history. The capability cost you nothing, because git was already keeping the snapshots — you just have to design with that in mind so the snapshots are useful.

The discipline you need to make this real is small: state in files, files in git, pretty-print with sorted keys, commit messages that say what changed, mutable scaffolding exiled. Five rules. Each one is enforced in a few lines of code in your write path.

The result is a system where "what did the world look like just before it broke" is a question you can answer in five minutes, no infrastructure, no cost. That is rare. It is also free, if you set up the system to invite it.

Most systems do not. They could.
