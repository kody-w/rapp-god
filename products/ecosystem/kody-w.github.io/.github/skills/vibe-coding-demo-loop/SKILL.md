---
name: vibe-coding-demo-loop
description: Ship batches of 10 single-file HTML demos to /learnwithkody/ via parallel sub-agents. Use this when the user wants to ideate, dispatch, wrap, and ship — not write demos by hand. The orchestrator never writes demo code; it dispatches.
---

# Vibe Coding Demo Loop

This is the publishing loop that put 71 working browser demos onto kody-w.github.io/learnwithkody/. Every round: one paragraph in, one working single-file HTML demo out, ten in parallel.

You are the orchestrator. Workers write the demos. Your job is taste + dispatch + glue.

## When to invoke

The user says any of:
- "double down" / "10 more" / "do all of them"
- "give me 10 prompts" → present them, then wait for confirmation
- A specific genre + scale ("FPS games", "creative tools", "places to be")
- A bonus single ask ("could you make a sci-fi arena shooter")

## Repository preconditions

Confirm these exist before starting:
- `_examples/` Jekyll collection with auto-applied `lwk_example` layout (configured in `_config.yml` `defaults`)
- `learnwithkody/demos/` directory for raw single-file HTML demos (no frontmatter — Jekyll passes them through)
- `_layouts/lwk_example.html` rendering: pills (difficulty/category), Hasan-style prompt block with one signature term highlighted, body, lessons section, embedded iframe
- Hub at `learnwithkody/index.html` filtering on `featured: true`
- CI: `.github/workflows/staging-canary.yml` runs `bundle exec jekyll build --strict_front_matter`
- Test suite: `tests/test_site.py` (must keep passing)

## The 4-step loop

### 1. Ideate (you, with the user)

Generate 10 audacious prompts in the requested domain. Format each:
```
### N. The Title
*Italic hook describing what the viewer sees.*
> Prompt with one **bold signature technical term** that names the demo's defining trick.
```

End with a tier ranking (highest hit-rate / hardest but spectacular / best for video / most addictive).

Stop. Wait for user approval. Do NOT dispatch until they say "go" / "do all of them" / "double down" / similar.

### 2. Dispatch 10 parallel sub-agents

Send all 10 Agent tool calls in ONE message (not sequentially). Each agent receives:

```
You are building one mind-blowing single-file HTML demo for kody-w.github.io/learnwithkody — a vibe coding examples site.

CONSTRAINTS (non-negotiable):
- ONE HTML file. All CSS/JS inline.
- Approved external lib: three.js from CDN (unpkg or jsdelivr ESM imports). Nothing else.
- No API keys, no backend, no fetch() to external services.
- Must run instantly. Visible / playable within 1 second.
- DO NOT modify any other file. DO NOT touch git. DO NOT spawn subagents.

THE DEMO TO BUILD:
[1-2 paragraph creative brief with named tech, scale claims, sensory details]

WRITE TO: /Users/kodyw/Documents/GitHub/kody-w.github.io/learnwithkody/demos/{NN-slug}.html

After writing, report back in under 150 words: what's beautiful about it, key implementation details, any compromises.
```

The "DO NOT spawn subagents" line is critical — without it, workers nest and waste context.

Use `run_in_background: true`. Notifications come automatically. Do NOT poll.

### 3. Wrap each completed demo (you, after each notification)

When a worker reports back, write a Jekyll example post in `_examples/{slug}.html`. Frontmatter schema:

```yaml
---
title: "Demo Name — One Tagline Sentence"
slug: demo-slug
order: NN          # next sequential after last shipped
featured: true
tagline: "ALWAYS quote any tagline containing a colon."
category: simulator|game|tool|prompt
difficulty: beginner|intermediate|advanced
status: live
tags: [list, of, tags]
stack: [HTML, JavaScript, three.js, ...]
demo: /learnwithkody/demos/NN-slug.html
repo: https://github.com/kody-w/kody-w.github.io
highlights:
  - signature term to highlight in the prompt block
prompt: |
  The exact paragraph the worker received, verbatim.
lessons:
  - "Three lessons. One sentence each. What you learned shipping it."
  - "Specific. Technical. Quotable."
  - "These are the takeaway, not the description."
---

<section class="lwk-section">
  <h2>What this is</h2>
  <p>One paragraph: mechanics, what's on screen, what the user does. Concrete.</p>
</section>

<section class="lwk-section">
  <h2>Why this is mind-blowing</h2>
  <p>One paragraph: the meta-claim. End on a punchline.</p>
</section>

<aside class="lwk-try-embed">
  <div class="lwk-try-embed-head">
    <span class="lwk-try-embed-label">Live demo</span>
    <a href="/learnwithkody/demos/NN-slug.html" target="_blank" rel="noopener" class="lwk-try-embed-open">Open in new tab ↗</a>
  </div>
  <iframe src="/learnwithkody/demos/NN-slug.html" title="Demo Name — live demo" loading="lazy" sandbox="allow-scripts allow-same-origin allow-pointer-lock"></iframe>
</aside>
```

### 4. Ship

After all 10 demos + posts are in:

1. Validate every YAML: `ruby -ryaml -e "YAML.load(File.read('_examples/foo.html')[/---\n(.*?)\n---/m, 1])"`
2. Run tests: `python3 -m unittest discover -s tests -p 'test_*.py'`
3. Check for concurrent commits: `git fetch origin master && git rev-list --left-right --count HEAD...origin/master`
4. `git add _examples/ learnwithkody/demos/`
5. Commit with table of demos + signature tricks
6. `git push origin master`
7. Watch CI: `gh run list --branch master --limit 1 --json databaseId --jq '.[0].databaseId' | xargs -I {} gh run watch {} --exit-status` (run in background)
8. After CI green, verify URLs return 200: `curl -s -o /dev/null -w "%{http_code}\n" "https://kody-w.github.io/learnwithkody/examples/{slug}/"`
9. Report results to user with table of what shipped

## Failure modes to expect

| Symptom | Cause | Fix |
|---|---|---|
| `comparison of NilClass with String failed` in Jekyll build | Unquoted YAML colon in tagline | Quote every tagline by default |
| Worker fails with content filter | Suggested religious / political corpus | Re-spawn with neutral text (Pride and Prejudice, Shakespeare) |
| `git push` rejected (fetch first) | Concurrent commit from another session | `git pull --rebase origin master`, no destructive force-push |
| Worker stalls 600s+ | Got stuck on hard math (BigInt bijection, etc.) | Re-spawn with the algorithm pre-specified inline |
| `Validate Posts` workflow fails | Pre-existing repo-wide issue, not your changes | Ignore unless caused by your post format |

## Numbering convention

- Demo files: numbered `NN-slug.html` in `learnwithkody/demos/`
- Example posts: `_examples/slug.html` with `order: NN`
- Featured rounds use `order: 1+` ascending
- Existing 8 shipped projects sit at orders 21-28
- Other-session concept prompts use orders 9-38 (overlap is harmless — Liquid sort is stable)

## Invocation

Direct trigger: a numbered list of 10 demo concepts in the user's prompt.
Indirect trigger: any phrase like "double down", "do all of them", "ship that whole list".

If the user gives you a SINGLE bonus ask alongside ("could you make X"), build it as a separate 11th worker in the same dispatch round. Number it after the round (e.g. demo 61, order 79).

## Templates also published

Already on the site for reference:
- `https://kody-w.github.io/loop/` — single-page agent instructions (pointable URL)
- `https://kody-w.github.io/2026/05/02/the-vibe-coding-demo-loop/` — long-form essay
- `https://kody-w.github.io/learnwithkody/examples/the-loop/` — catalog entry

If a fresh agent needs to learn the loop and you only have one URL slot, give them `https://kody-w.github.io/loop/`.
