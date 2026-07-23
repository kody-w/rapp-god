---
name: ship
description: Commit, push, publish to GitHub Pages, and hand back a VERIFIED live URL. Use whenever the user says "push it", "publish this", "ship it", "make this live", "show me the link so I can test", or finishes building anything static (single-file HTML app, demo, deck, agent page) that belongs on the web. Invoking this skill IS the authorization to commit and push — do not ask for permission again.
---

# Ship: commit → push → publish → verified live URL

The deliverable of this skill is ONE thing: a live URL that has been **verified to serve the newest content**. Not "pushed", not "Pages enabled" — a link Kody can click right now and see the new thing.

## Step 0 — Guardrail (before anything touches a remote)

Kody runs two RAPP worlds: **my-RAPP** (personal, `kody-w/*` on GitHub) and **work-RAPP** (the work org). Flow is upstream→downstream ONLY: personal→work is fine, **work content must never land in a `kody-w` personal repo**. If the content being shipped originated from work (customer names, work-org repos, internal data, internal transcripts), stop and confirm the destination before pushing. Everything else: proceed without asking.

## Step 1 — Commit

- If not in a git repo: `git init`, then continue.
- Stage the relevant files (not blanket `git add -A` if the directory has obvious junk — check `git status` first).
- Commit message: one line, what changed and why it's visible ("Add particle-sim demo page", not "updates").
- Include the standard co-author trailer.

## Step 2 — Push (create the remote if missing)

- If a remote exists: push to the current branch.
- If no remote: `gh repo create kody-w/<sensible-kebab-name> --public --source . --push`. Derive the name from the project/file, don't ask.
- If push is rejected (remote ahead): pull --rebase and retry once; if there are real conflicts, stop and report — don't force-push.

## Step 3 — Publish to GitHub Pages (for anything static)

Static = single-file HTML apps, demos, decks, docs, anything a browser can render without a server. Kody's default artifact shape is the self-contained single HTML file.

- Check if Pages is already enabled: `gh api repos/kody-w/<repo>/pages` (404 = not enabled).
- Enable if needed: `gh api repos/kody-w/<repo>/pages -X POST -f "source[branch]=main" -f "source[path]=/"` (adjust branch/path to where the HTML lives; if the file isn't `index.html` at the published root, the URL must include the filename).
- The live URL is `https://kody-w.github.io/<repo>/[<file>.html]`.

If the thing is a RAPP agent rather than a page, the publish target is the RAR registry (`kody-w/RAR`, single-file agent publish flow) — push the agent file there instead of enabling Pages.

## Step 4 — Verify it's ACTUALLY live (the step that makes this skill worth having)

GitHub Pages deploys lag and cache. HTTP 200 is not proof — the old version also returns 200.

1. Pick a **marker string** that exists only in the new content (a new heading, a version string, a phrase from this change).
2. Poll: `curl -sL <url> | grep -c "<marker>"` every ~20s, up to ~4 minutes. You can watch the deploy directly with `gh api repos/kody-w/<repo>/pages/builds/latest` (status `built` = done).
3. Only when the marker appears, report success.
4. If 4 minutes pass without the marker: report the URL anyway but say explicitly "pushed, but the live URL is still serving the old version — Pages build status is X". Never present an unverified link as done.

## Step 5 — Report

Final message: the live URL on its own line (clickable), one sentence on what was shipped, and the repo URL. Nothing else unless something went wrong.

## Don'ts

- Don't ask "should I commit/push?" — the invocation is the approval.
- Don't stop after `git push` and call it shipped; the live URL check is the finish line.
- Don't create a new repo when the file already lives in one that has Pages — ship in place.
- Don't publish work/customer content to personal repos (Step 0).
