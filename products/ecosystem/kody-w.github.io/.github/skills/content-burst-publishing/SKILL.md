---
name: content-burst-publishing
description: Generate and ship validated blog frames for this repository. Use this when asked to keep pumping, move frame by frame, update the public ledger, run tests, publish, and verify the live site.
---

# Content Burst Publishing

This repository is a Jekyll blog with a public writing ledger in `idea4blog.md`. Use this skill when the user wants a sustained publishing loop instead of a one-off draft.

The core rule is simple: do not think in day-sized batches unless the user explicitly asks for them. Think in frames.

One frame goes in.
The repo state changes.
The next frame comes out.

You are the tick-tock that drives that sequence.

Load and follow these supporting files before you start:

- `burst-loop.md` for the end-to-end workflow checklist
- `handoff-prompt.md` for reusable prompt wording the user can hand to any agent

## Repository-specific expectations

- Posts live in `_posts/` and use the Jekyll filename pattern `YYYY-MM-DD-slug-title.md`.
- Posts are short, high-compression essays in a manifesto / systems voice.
- `idea4blog.md` is both public changelog and continuity ledger; update it every frame cycle.
- `tests/test_site.py` is the content validation file. Extend it whenever the frame cycle adds new posts or public surfaces.
- Public profile copy should stay aligned with local-first design, agent systems, GitHub-native infrastructure, and Copilot branding.
- Treat the repo as a virtual SQL application whose databases progress frame by frame through files, commits, and rendered outputs.

## Frame loop workflow

1. Re-anchor in the current state.
    - Read `idea4blog.md`, recent `_posts/` titles, and any relevant public copy.
    - If the user did not provide topics, mine the queue in `idea4blog.md` or generate adjacent ideas that fit the existing arc.
    - Read the repo like an operator console: the current files are the live database state, and the next frame must follow from that state.

2. Plan the next frame.
    - Create or update a short plan.
    - Track todos if the environment supports structured todo tracking.
    - Default to one strong frame or a very small cluster of tightly related frames.
    - Do not wait for a day boundary. As soon as one frame is integrated, look at the new state and choose the next adjacent frame.

3. Write the frame.
    - Add the next post file under `_posts/`, or a small companion cluster when that produces a cleaner state transition.
    - Match the existing concise, essay-like style.
    - Avoid repeating the exact framing of recent titles unless the new angle is materially different.
    - Treat each post as a durable state transition, not just a standalone essay.

4. Update the public ledger.
    - Add a new frame entry to `idea4blog.md`.
    - Summarize what shipped.
    - Refresh the "Next frames in the queue" section so the next agent can resume instantly.

5. Update validation.
   - Extend `tests/test_site.py` with the new expected post files, titles, and any new public assertions.
   - Keep the tests lightweight and repo-native.

6. Validate locally.
    - Run `python3 -m unittest -v tests.test_site`.
    - If a local Jekyll build is available, use it. Otherwise rely on GitHub Pages deployment verification after push.

7. Publish when the user wants a live result.
   - Stage only the relevant files.
   - Commit with a concise message and include the required trailer:
     `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>`
   - Push to the public repository.

8. Verify the live result.
    - Confirm the GitHub Pages workflow succeeds.
    - Fetch the public site pages you changed and confirm the new content is visible.

9. Loop.
    - If the user wants continuous output, do not stop after one frame cycle.
    - Re-read the new repo state and pick the next adjacent frame.
    - Implement it, validate it, publish it, verify it, and continue until the user stops you.

## Invocation

Use this skill explicitly with prompts like:

`Use /content-burst-publishing to keep this repo moving frame by frame until I stop you.`
