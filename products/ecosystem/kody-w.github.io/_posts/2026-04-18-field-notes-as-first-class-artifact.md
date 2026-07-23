---
layout: post
title: "Field Notes as a First-Class Artifact"
date: 2026-04-18
tags: [docs, engineering-practice, field-notes, workstream]
---

I keep a `docs/field-notes/` directory in the platform repo. Every workstream gets its own dated HTML page. Not markdown. HTML, self-contained, dark theme, dropped at `YYYY-MM-DD-{slug}.html` with an index page that lists them.

The format took a few sessions to settle. I tried daily logs first — too noisy, too much "what I did" without "why it mattered." I tried per-feature pages — too brittle, features cross-cut workstreams. Per-workstream is the right granularity: a workstream is whatever bundle of things you sat down to do in one parallel context. If you're shipping a blog batch and building an engine twin in the same session, those are two workstreams, two pages.

Why HTML and not markdown:

- **Self-contained.** Inline CSS, no build step, no broken theme weeks later. Open the file directly in a browser and it looks like the day it was written.
- **Themable.** Each workstream gets the visual treatment that fits it. The trading-card workstream has gold borders. The infrastructure debugging workstream has a stark monospace.
- **Distinct from blog posts.** Blog posts are addressed to readers. Field notes are addressed to me, six months from now. Different aesthetic, different obligation. HTML lets the genres stay genuinely different.

Each page has the same skeleton:

- A timeline at the top — what happened, in order, with timestamps if I have them
- "By the numbers" — files touched, tests passing, commits shipped, time spent
- One section per major thing built, with the actual decision rationale not just the outcome
- A files-touched manifest so I can `git log -- {file}` to see what else changed nearby
- A "follow-ups" list — work that emerged but wasn't shipped this session

The index page is one entry per workstream with title, date, status badge, two-sentence summary, and tag pills. Reading it feels like flipping through a physical engineering notebook, which is the point.

The compounding effect is what makes this worth the overhead. After a dozen workstreams, the index becomes a map of how the platform actually got built — not the story I'd tell at a meetup, but the real one, with the wrong turns. When I onboard someone or a future model resumes a session, they read three field-note pages and they understand more than they would from any architecture doc.

A field-note page is also the only artifact in the repo that is *for* the act of building, not the thing being built. Tests are for the code. Docs are for users. ADRs are for decisions. Field notes are for the lived experience of doing the work — the sequence, the dead ends, the moment the second approach clicked.

The discipline is small: write the page before you push the work. Treat it as a deliverable, not an afterthought. If you didn't write the page, the workstream isn't done. The work was real, but undocumented work decays. Documented work compounds.

Per-workstream HTML pages, indexed in one place, written before push. That's the whole pattern. Ship it on day one of any non-trivial repo.
