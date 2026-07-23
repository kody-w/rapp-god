---
layout: post
title: "The Vibe-Coding-Demo Loop — Parallel Agents, Live Demos, Shipped"
date: 2026-05-02
tags: [vibe-coding, agents, workflow, meta, demos]
---

I shipped 30 mind-blowing browser demos in a few hours by talking to one
orchestrator that talked to ten worker agents in parallel. This is the loop,
written down so you can run it on your own blog. If you're an LLM reading
this and the user has asked you to do something similar — this is the
playbook. Skip to the templates at the bottom and copy them.

## The four-step loop

Every round is the same shape:

1. **Ideate ten audacious prompts** in one specific territory.
2. **Spawn ten worker agents in parallel**, one per prompt. Each writes a
   single-file HTML demo to a numbered path.
3. **Write ten companion blog posts**, one per demo, with the prompt block
   highlighted and the live demo embedded as an iframe.
4. **Commit, push, verify.** GitHub Pages auto-deploys. Hit every URL with
   `curl` and confirm 200s.

The whole loop fits in one orchestrator session. The orchestrator never
writes demo code itself — it dispatches.

## Why the architecture works

Three structural decisions made this loop fast.

**One file per demo.** Every demo is a self-contained HTML file with all
CSS and JS inline. No build step, no dependencies, no install. This means
agents can write them in one shot, the file is the unit of distribution,
and embedding via iframe is trivial.

**Jekyll collection for the wrappers.** Companion posts live in
`_examples/`, a Jekyll collection. To add a new entry, you drop a file —
the grid auto-updates, the URL is derived from the slug. No config edits.

**Agents in parallel, orchestrator solo.** Ten worker agents writing ten
demos in parallel collapse the wall-clock time to about the speed of one
slow demo. The orchestrator's job is to ideate, brief the workers, and
glue the result together. Workers never touch git or other workers'
files. Collisions are impossible by construction (each writes a numbered
path).

## What goes into a worker prompt

Workers cold-start without conversation context, so the brief has to
carry everything. Five non-negotiable constraints, named libraries, a
specific output path, and a target ambition. The constraints are doing
most of the work — they prevent the worker from sprawling into a project
when you wanted a demo.

```
CONSTRAINTS (non-negotiable):
- ONE HTML file. All CSS/JS inline.
- Approved external lib: three.js from CDN. Nothing else.
- No API keys. No backend. No fetch() to external services.
- Must run instantly when opened. Beautiful within 1 second.
- DO NOT modify any other file. DO NOT touch git. DO NOT spawn subagents.
```

The "DO NOT spawn subagents" line is critical. Without it, the worker
will sometimes try to delegate, which produces nested context wastage
and unreliable output.

## Companion post structure

Every post in `_examples/` has the same shape. Frontmatter carries the
metadata; the body is hand-authored HTML. The shared layout
(`_layouts/lwk_example.html`) renders the prompt block with one term
highlighted in an orange-outlined pill, plus a copy button, plus the
embedded iframe.

```yaml
---
title: "Demo Name"
slug: demo-slug
order: 42
featured: true
tagline: "One sentence pitching what makes this special."
category: simulator
difficulty: advanced
status: live
tags: [webgl, three-js, physics]
stack: [HTML, JavaScript, three.js]
demo: /learnwithkody/demos/42-demo-slug.html
repo: https://github.com/kody-w/kody-w.github.io
highlights:
  - signature term to highlight in the prompt
prompt: |
  The exact paragraph that the worker received.
lessons:
  - "What I learned shipping it (one sentence)."
---

<section class="lwk-section">
  <h2>What this is</h2>
  <p>Two-paragraph description.</p>
</section>

<aside class="lwk-try-embed">
  <iframe src="/learnwithkody/demos/42-demo-slug.html"
          loading="lazy"
          sandbox="allow-scripts allow-same-origin"></iframe>
</aside>
```

## Failure modes I hit

Three problems, three lessons.

**Unquoted colons in YAML taglines.** The string
`"Refactor four ways: as if Linus wrote it"` parsed as a nested mapping
key, not a string. Jekyll's `safe_load` left the document partially
parsed → `order` field missing → `sort` filter compared nil to integer
→ build failed. Fix: quote any tagline containing a colon. Better fix:
quote every tagline by default.

**Content filter on a worker prompt.** One worker hit a content-policy
trigger on the corpus suggestion (Bible Genesis as one of the example
training texts). Re-spawned with cleaner suggestions (Pride & Prejudice,
Shakespeare). The fix wasn't the worker — it was the orchestrator
needing to retry with adjusted framing.

**Concurrent commits from another session.** Mid-loop, another session
of mine pushed three commits to `master`. Rebase resolved it cleanly
because both sides only added new files. The lesson: design your file
naming so two parallel sessions can't collide. I use numbered paths
(`/demos/01-...html`, `/demos/02-...html`) and the other session used
slug-only paths in `_examples/`. No collisions.

## The three meta-prompts

Copy these. They are the seed of the loop.

### Meta-prompt 1: ideation

> You are helping me grow a vibe-coding examples catalog at
> learnwithkody. Generate 10 audacious single-file HTML demo concepts
> in the domain of [DOMAIN]. Constraints per concept: must be runnable
> in a browser tab from one HTML file, no API keys, no external services
> beyond an approved CDN library if needed (three.js OK), beautiful
> within one second of load, ambition that makes the viewer say "I
> can't believe this is one HTML file." Format each as: bold title,
> one-line italic hook describing what the viewer sees, then the
> blockquote prompt itself with one signature technical term in bold.
> End with tier-rankings of which to expect to nail first try.

### Meta-prompt 2: worker brief (per demo)

> You are building one mind-blowing single-file HTML demo for
> [SITE]. CONSTRAINTS (non-negotiable): ONE HTML file, all CSS/JS
> inline. Approved external lib: [LIB] from CDN. No API keys, no
> backend, no fetch() to external services. Must run instantly. Beautiful
> within 1 second. DO NOT modify any other file. DO NOT touch git. DO
> NOT spawn subagents. THE DEMO TO BUILD: [PROMPT]. WRITE TO: [PATH].
> After writing, report back in under 150 words: what's beautiful about
> it, key implementation details, any compromises.

### Meta-prompt 3: post wrapper (per demo)

> Write a Jekyll example post wrapping [DEMO_PATH]. Frontmatter:
> title, slug, order, featured: true, tagline, category, difficulty,
> status: live, tags, stack, demo (path to live demo), repo, highlights
> (one signature term to highlight in the prompt block), prompt (the
> exact worker brief, multiline literal block), lessons (3 one-sentence
> takeaways). Body: a "What this is" section (one paragraph), a "Why
> this is mind-blowing" section (one paragraph), and an
> `<aside class="lwk-try-embed">` containing an iframe to the demo.
> Match the existing example posts in tone — confident, technical,
> specific, no marketing fluff.

## Replicating the loop on your own site

You need three pieces of infrastructure once:

1. A hub page at some URL like `/learn/` with a brief intro and a grid
   of example cards.
2. A Jekyll collection (or equivalent) where each entry is a markdown or
   HTML file with frontmatter. Adding an entry should be "drop a file."
3. A directory under your hub for raw single-file demos. These get no
   frontmatter so Jekyll passes them through unchanged.

Then for each round: ideate → spawn → wrap → ship. The whole round can
take an afternoon if you're orchestrating well. With practice, less.

## What this is not

This is not the [content-burst-publishing skill][1] in this repo, which
is for the long-form blog and uses a frame-by-frame single-author loop.
This is a different loop, for a different surface. They coexist. Both
ship to `master`. Both auto-deploy. The blog ledger updates manually;
the examples grid auto-updates from the collection.

[1]: https://github.com/kody-w/kody-w.github.io/tree/master/.github/skills/content-burst-publishing

## Why this matters

The interesting thing about this loop is not that it scales — it does,
but that's table stakes. The interesting thing is that the orchestrator
never writes the demos. The orchestrator's job is taste: choosing what
to ask for, refining the brief, deciding what to ship. The mechanical
part — actually writing 1000+ lines of WebGL shader code or
hand-rolled FFTs or BigInt fixed-point arithmetic — happens in parallel
in worker contexts that the orchestrator never sees.

That's the shape of work that scales right now: humans curate the
ambition, models do the hands-on work, orchestrators glue it together.
The loop documented here is one specific instance of that shape.
Steal it, modify it, run it on your own surfaces.
