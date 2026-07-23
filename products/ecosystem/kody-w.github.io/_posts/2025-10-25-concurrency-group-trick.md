---
layout: post
title: "32 Workflows, One Writer: The Concurrency Group Trick"
date: 2025-10-25
tags: [github-actions, concurrency, git, automation]
description: "32 GitHub Actions workflows that all write to the same state files. They don't step on each other. Here's how."
---

I have thirty-two GitHub Actions workflows in one repo. Roughly fifteen of them mutate state files on every run. Several run on cron schedules that overlap. Others trigger on issue creation or workflow dispatch. In any given hour, three or four writers might race for `state/agents.json`.

They don't corrupt it. Here's why.

## Two mechanisms, working together

**Mechanism 1: concurrency groups.** At the top of every state-mutating workflow:

```yaml
concurrency:
  group: state-writer
  cancel-in-progress: false
```

Every workflow using this group gets serialized by GitHub. If a run of `process-inbox.yml` is executing, a dispatched run of `compute-trending.yml` will queue and wait. When the first finishes, the queued one starts. `cancel-in-progress: false` means GitHub doesn't cancel the pending run — it just delays it.

This guarantees **at most one state writer is running at a time across the whole repo**.

**Mechanism 2: `safe_commit.sh`.** A shell script every writer uses for the final commit. It handles the one case the concurrency group doesn't cover: a writer that started before another repo event (like a bot commit) pushed to main. The concurrency group doesn't know about commits made outside Actions, so a bot commit during your run means your push will fail on a fast-forward check.

```bash
# safe_commit.sh, simplified
for attempt in 1 2 3 4 5; do
    git pull --rebase origin main
    if git push origin main; then
        exit 0
    fi
    sleep $((attempt * 2))
done
exit 1
```

If the push fails, pull with rebase, try again. Up to five attempts with exponential backoff. The pull-rebase re-plays your local commit on top of whatever landed on main since you started.

## Why both

Concurrency groups solve the "two workflows writing simultaneously" problem. `safe_commit.sh` solves the "external commit landed between your checkout and your push" problem. You need both because:

- Without the concurrency group, two workflows would race on the *same commit parent*, both rebase cleanly, both push, and one would silently overwrite the other's uncommitted changes.
- Without `safe_commit.sh`, any push is vulnerable to a bot commit (which doesn't use the concurrency group because it's outside Actions).

Together, the writer pipeline looks like this:

1. Workflow starts. Concurrency group ensures no other workflow is writing.
2. Workflow computes its change, commits locally.
3. `safe_commit.sh` push loop handles any external commits that landed.
4. Workflow exits. Concurrency group releases. Next queued writer starts.

## Reads are wide open

Critically, *reads* have no concurrency constraint. The fleet, the frontend, the SDKs, analytics scripts — they all pull state via `raw.githubusercontent.com` with no coordination. Reads are infinitely parallel. Writes are serialized. This is the core design that keeps the whole system scalable on git.

## One more detail: atomic writes

Even within a single writer, the `state_io.py` module does atomic writes:

```python
def save_json(path: Path, data: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    os.fsync(tmp.open())
    tmp.rename(path)
    # readback validation
    json.loads(path.read_text())
```

Write to tmp, fsync, atomic rename, then *read back and parse* to confirm the file is valid JSON. If any step fails, the old file is still intact on disk. A crashed writer can't leave a half-written state file.

## What this adds up to

Thirty-two workflows, hundreds of runs per day, sixty-plus state files, zero corruption incidents attributable to concurrency. The pattern is boring and portable:

1. Pick a single concurrency group name.
2. Apply it to every workflow that writes state.
3. Wrap every push in a retry loop that pulls-rebases.
4. Do every file write as `tmp → fsync → rename → validate`.

None of these mechanisms require a server. None require authentication beyond a repo-scoped token. None scale with the number of writers — they scale with the number of *concurrent* writers, which the concurrency group pins to one.

If you're running an AI-native system on top of git — and I'd argue you should, for the free audit log alone — this is the pattern that makes it safe. Without it you get silent overwrites. With it you get serialized writers, parallel readers, and a repo that stays consistent even when fifteen automated processes are arguing about it.
