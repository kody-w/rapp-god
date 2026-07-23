# CONCURRENCY — many Opus writers, one repo, no clobbering

Multiple models will build this brain **in parallel**, pushing to the same repo.
Parallel writers destroy a repo when they edit shared files and force-pushes race.
This protocol removes both failure modes. **Follow it exactly.**

Principle: **partition by file · coordinate by claim · integrate by rebuild.**

## The five rules

1. **One file per unit — never a shared mega-file.**
   - Each **public repo** you document → its own note `public/notes/<repo>.md`.
   - Each **crawl shard** → its own file `crawl/shards/<shard>.json`.
   - Two writers touching different repos touch different files → no conflict.

2. **Claim before you work.** Before processing a shard or cluster, create
   `claims/<scope>.claim.json`:
   ```json
   { "agent": "<your id>", "scope": "cluster:rings", "started": "<iso8601>", "ttl_min": 30 }
   ```
   If a **fresh** claim (age < its `ttl_min`) already exists for that scope, pick
   a different scope. Claims are advisory locks carried in git. Delete your claim
   when done (or let it expire).

3. **Aggregates are GENERATED, never hand-edited.** `Home.md`, cluster MOCs,
   `registry.json`, `api/**`, the Pages data — all produced by `build.py` from
   the per-unit source files. **Writers edit SOURCE files only** (`public/notes/*`,
   `crawl/shards/*`). Never two writers editing the index by hand — that's the
   collision this whole design exists to prevent. Regenerate; don't merge.

4. **Rebase before push; never force-push; small atomic commits.**
   ```bash
   git add public/notes/<repo>.md   # ONLY your scoped files — never git add -A
   git commit -m "notes: <repo>"
   git pull --rebase origin main && git push
   ```
   Because you only touch files you own, rebase almost never conflicts. If it
   does, it's your file — resolve it, keep going. **Force-push is forbidden** (it
   erases other writers' commits).

5. **The seam guard runs on every commit** (see `PLAN.md` Phase 0). Private
   content / secrets / private-repo names can never enter this public repo. If
   the guard blocks you, you were about to leak — fix it, don't bypass.

## Who integrates the index

**CI, not writers.** On push, CI runs `build.py` (regenerate aggregates + `api/`),
the leak audit, and the Pages deploy. If CI isn't up yet, ONE designated writer
runs `build.py` after a batch — never several at once. The generated files are
build artifacts; treat a merge conflict in them as "just rebuild," never a
hand-merge.

## Worked example (two writers, zero conflict)

- Writer A claims `cluster:rings`, writes `public/notes/rapp-canary.md`,
  `public/notes/rapp-nightly.md`, commits, rebases, pushes.
- Writer B claims `cluster:tooling`, writes `public/notes/rapp-cli.md`, commits,
  rebases, pushes.
- Neither touched `Home.md` or `registry.json` — CI rebuilds those from both
  writers' notes. No conflict, no lost work.

## Anti-patterns (do NOT)

- ❌ `git add -A` (sweeps files outside your scope).
- ❌ Editing `Home.md` / `registry.json` by hand.
- ❌ `git push --force`.
- ❌ Holding a claim you're not actively working.
- ❌ One giant commit spanning many clusters.
