# Editorial review — live posts, 2026-05-14 → 2026-07-14

Reviewed by Fable 5 at Kody's request: full edit pass over the six live posts from the
past two months, optimizing for value to the average reader of this blog. Rewrites are
staged in `_drafts/` and touch nothing live; republish by replacing the `_posts/` file
with the `_v2` content (same filename/date — the permalink must not change).

## Verdicts at a glance

| Post | Verdict | Action |
|---|---|---|
| 2026-07-05 The AI You Keep | **FREEZE** | No edits — it's dated prior art |
| 2026-07-05 What Is Our Moat? | **FREEZE** | No edits — companion to the prior art |
| 2026-06-19 Funded R&D: 90-Day Plan | **REWRITE** | `_drafts/2026-06-19-funded-rnd-90-day-plan_v2.md` |
| 2026-06-18 A Taste of AGI | **KEEP** | 3 optional line edits below |
| 2026-05-17 The leviathan refused to confabulate | **KEEP** | 1 optional line edit below |
| 2026-05-17 Cells all the way down | **EDIT** | `_drafts/2026-05-17-cells-all-the-way-down_v2.md` |

No consolidation recommended. The two 07-05 posts overlap deliberately (essay vs.
strategy memo) and already cross-link; merging them would weaken both.

## Per-post reasoning

### The AI You Keep + What Is Our Moat — freeze

These are your strongest work in the window and they carry a **date-stamped prior-art
claim** ("published as prior art for the pattern described", CC BY 4.0, patent pledge).
Substantively editing a prior-art essay after publication undermines exactly the thing
it exists to prove — that the pattern was stated completely on 2026-07-05. Editorial
ruling: these two are sealed. If you ever want to improve the argument, write a new
post that cites them; never revise in place.

### Funded R&D — full rewrite (the weakest fit, now on-thesis)

The original is solid advice but reads like a summary of someone else's
creator-economy framework — it's the only post in the archive that could appear on
anyone's blog. Your archive's through-line is *ownership of what compounds* (twins,
signed frames, local-first, "if it can't be inherited, it isn't owned"). The rewrite:

- adds the missing bridge: **your job is a rented deployment of your expertise** — the
  same rental/ownership law as "The AI You Keep," now cross-linked, so the career post
  becomes part of the blog's single argument instead of an outlier;
- cuts the guru-isms ("Profitable Offer Prototype" branding, repeated hedges) and
  compresses the 90-day section by ~a third with no step lost;
- keeps your framework, tables, and closing question intact — it's your post, sharpened,
  not replaced.

### Cells all the way down — targeted edit

One real defect: **the cell count drifts through the piece** (title/description say
"227-cell digital twin," the practical section says 92 cells; a careful reader can't
reconcile them). The v2 fixes it consistently: ~227 directories in the generated
scaffold, **92 wired cells** (5 estates + 15 industries + 28 neighborhoods + 43
factories + the organism root), and shows that arithmetic once. Also fixed: the closing
line promised "the next post will be voiced by the 227-cell organism itself," which
never shipped — v2 links the leviathan companion post instead of promising. Minor
tightening elsewhere; the structure and voice are untouched.

### A Taste of AGI — keep; optional line edits

The strongest narrative energy in the window. Three optional touches if you revisit:

1. "Read that sentence again" (§the-part-that-should-not-be-possible-yet) — the same
   device appears twice in the leviathan post ("Read that again"). Across the archive it's
   becoming a tic; keep it in ONE post (I'd keep it here, cut from leviathan).
2. The one-sentence-paragraph cascade in the opening is powerful but runs ~9 deep;
   merging two pairs would make the remaining hits land harder.
3. Verify the two outbound links still resolve before any republish (voxel-world.html
   and the evolution log) — the post's credibility rests on "the proof is in the repo."

### The leviathan refused to confabulate — keep; optional line edit

Best post of the six; publishing the refusal transcript as-is was the right call.
Optional: "Read that line again" (§the-third-attempt) — see the tic note above. Also the
final promise ("Tomorrow I'll wire a press leaf...") — if that press-leaf post never
shipped, either ship it or soften the line on a future touch; dangling promises accrue.

## Republish checklist (per post you accept)

1. Copy `_drafts/<name>_v2.md` over `_posts/<same-date-same-slug>.md` — do NOT change
   filename or date (permalinks are load-bearing; both posts are linked externally).
2. `python3 -m unittest discover -s tests -p 'test_*.py'` — titles/dates unchanged, so
   EXPECTED_POSTS should pass as-is.
3. Note the revision in `idea4blog.md` (the continuity ledger).
