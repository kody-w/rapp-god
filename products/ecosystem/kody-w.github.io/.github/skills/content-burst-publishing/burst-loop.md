# Frame Loop Checklist

Use this file as the operating checklist for a continuous content session.

The cadence is not daily.

It is frame-based:

1. one frame lands
2. the repo state changes
3. the next frame is chosen from that new state

That tick-tock is the loop.

## Before writing

1. Read `idea4blog.md`.
2. Read a few recent `_posts/` titles or full posts to stay in voice.
3. Check `about.md` or `_layouts/default.html` if the burst touches public positioning.
4. Update the session plan and todos if those tools are available.
5. Identify the single next frame or smallest coherent cluster that should advance the machine.

## During the frame

1. Default to one frame at a time unless a tiny cluster is clearly better than an isolated move.
2. Keep the title sharp and distinct.
3. Treat each post as one frame in the larger swarm narrative.
4. Prefer adjacent ideas from the current queue before inventing a brand-new arc.
5. Treat the repo as a virtual SQL application whose visible files are the live state tables.

## After writing

1. Add a new frame entry to `idea4blog.md`.
2. Refresh the queue in `idea4blog.md`.
3. Extend `tests/test_site.py`.
4. Run `python3 -m unittest -v tests.test_site`.
5. If the user wants continuous output, immediately choose the next frame from the just-updated state.

## Definition of done

The frame cycle is done only when:

- the new frame exists
- the ledger is updated
- the tests pass
- the changes are committed and pushed when the user wants them live
- the public site and Pages deployment are verified
