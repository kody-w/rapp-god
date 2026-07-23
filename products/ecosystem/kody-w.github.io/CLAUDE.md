# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A Jekyll blog hosted on GitHub Pages (`kody-w.github.io`). No Gemfile, no bundler config, no build step beyond what GitHub Pages runs. Pushes to `master` auto-deploy.

## Common commands

```bash
# Run the content/structure validation suite (the only test suite)
python3 -m unittest discover -s tests -p 'test_*.py'

# Run a single test method
python3 -m unittest tests.test_site.SiteTestCase.test_expected_posts_exist

# Local Jekyll preview (requires gem install jekyll bundler)
jekyll serve              # → http://localhost:4000

# Local near-prod build (pulls live data from sibling repos via curl)
./scripts/local-build.sh                  # build + serve
./scripts/local-build.sh --build-only
./scripts/local-build.sh --pull-data      # fetch fresh production data first

# Versioned/immutable snapshot builds (output under builds/, gitignored)
./scripts/versioned-build.sh --canary
./scripts/versioned-build.sh --rollback v1.0.0
```

## Content model — three collections, two layouts each matter

- `_posts/` — main public essay archive (~600 files), permalink `/:year/:month/:day/:title/`, layout `post`.
- `_twin_posts/` — separate "digital twin" first-person field notes, permalink `/digital-twin/:title/`, layout `twin_post`. Has its own landing page at `digital-twin/index.html`; **does not appear on the homepage feed**.
- `_examples/` — "Learn with Kody" vibe-coding example pages, permalink `/learnwithkody/examples/:path/`, layout `lwk_example` (auto-applied via `_config.yml` defaults).

Layouts cascade: `post` / `twin_post` / `lwk_example` → `default.html` (single shell with header + nav + footer). All styling lives in `css/main.css` (one file, both blog typography and About-page component styles).

## Post conventions

Filename: `YYYY-MM-DD-slug-title.md`. Front matter is minimal:

```yaml
---
layout: post
title: "Post Title"
date: YYYY-MM-DD
tags: [optional, list]
---
```

Recent posts use a `tags:` array; older posts may omit it. The CI workflow at `.github/workflows/validate-posts.yml` only enforces filename format and presence of `layout`, `title`, `date`.

## The test suite is a content ledger, not unit tests

`tests/test_site.py` (~1500 lines) hard-codes an `EXPECTED_POSTS` dictionary mapping each new post filename → its title/date/tags, plus assertions about specific pages (`about.md`, `idea4blog.md`, `simulated-dynamics365.md`, `lockstep-digital-twin.md`, the digital-twin index, the content-burst skill files). When you add a post or new public surface, **extend `EXPECTED_POSTS` and add the corresponding assertion** — otherwise the suite fails. This is intentional: the tests are how the repo tracks "what shipped."

The same file also asserts that `.agents/`, `.model-registry.json`, and other agent-local paths stay in `.gitignore`. Don't commit anything from `.agents/`.

## The "content-burst-publishing" skill

`.github/skills/content-burst-publishing/` defines a **frame-by-frame** publishing loop (write one post → update `idea4blog.md` ledger → extend tests → commit → push → verify live → pick the next adjacent frame from the new repo state). When the user asks to "keep pumping" or "ship frames," follow `SKILL.md` + `burst-loop.md` rather than treating it as a one-off draft. Commits made under this loop include the trailer `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>`.

## idea4blog.md is the continuity ledger

Public-facing changelog AND handoff state for the next agent/session. Update it when posts ship — it's how the next frame knows where to resume. Tests assert it exists and has correct front matter.

## Voice / topic guardrails

Posts are short, high-compression manifesto/systems essays. Themes already in the archive: agent autonomy loops, Rappterbook (social network for AI agents on GitHub infra), Mars Barn simulation, git-as-infrastructure, zero-cost/local-first systems, digital twin extending will. Avoid repeating recent post framings unless the new angle is materially different.

## Deployment safety (see DEPLOYMENT.md)

`master` push → GitHub Pages auto-deploys to staging (`kody-w.github.io`). Production sites (`rappter.com`, `kodyw.com`) are **never** auto-deployed — they go through manual import. The `local-build.sh` PII scan greps built HTML for `@icloud.com`/`@me.com`/`@mac.com` patterns before serve; respect that signal.
