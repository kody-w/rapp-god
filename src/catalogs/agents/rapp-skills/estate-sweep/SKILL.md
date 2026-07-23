---
name: estate-sweep
description: Clone-and-lint drift sweep across every public kody-w repo using the shared rapp-drift-lint. Use when Kody says "sweep the estate", "estate sweep", "lint all my repos", "is the estate clean", "check everything for drift", or after a canon/spec change that could ripple across the RAPP estate. Read-only — reports per-repo violations; fixing is a separate judgment step.
---

# estate-sweep — the whole public estate through one lint

The 2026-07 drift fix taught the lesson: drift accumulates silently across the
estate (sha256 name-hash minting reached 10 sites before anyone looked). This
skill is the look. It clones/refreshes every public `kody-w` repo shallow and
runs `rapp-drift-lint` over each, emitting a per-repo violation tally.

## Run it

```
REPO_LIMIT=0 bash ~/.claude/skills/estate-sweep/scripts/sweep.sh ~/.cache/rapp-estate-sweep
```

- Workdir `~/.cache/rapp-estate-sweep` is reused — re-runs pull instead of re-cloning.
- `REPO_LIMIT=N` caps the sweep to the first N repos (smoke runs). Unset/0 = full estate.
- The script checks that the active `gh` account is `kody-w` and WARNS if not —
  never `gh auth switch` on Kody's behalf; surface the warning and stop.
- The lint itself comes from `kody-w/rapp-drift-lint` (cloned into the workdir
  unless a path is passed as arg 2).

## Read the report, then judge

The output ends with `<N> repos dirty, <M> total violations`. The sweep NEVER
auto-fixes. For each dirty repo:

1. Re-run the lint on that repo alone and read the actual violations.
2. Classify: real drift (fix at its real layer) vs. lint false-positive
   (fix the lint in `rapp-drift-lint`, not the repo).
3. Fixes are per-repo and traceable — one issue or commit per repo, never a
   blind bulk rewrite. Canon: the name is RAPP in prose; `rapp/1` is only the
   lowercase wire tag; identity is never sha256(owner/slug).

## Don'ts

- Don't sweep with the work `gh` account active (kody-w repos 403 under it).
- Don't fix anything in the same breath as the sweep — report first.
- Don't touch private repos; the sweep is public-estate only by design.
