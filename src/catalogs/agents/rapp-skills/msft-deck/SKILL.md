---
name: msft-deck
description: Build, restyle, or revise a PowerPoint deck in Kody's Microsoft styling, self-review every slide visually, and only hand it over verified and popped open. Use whenever the user asks for a deck, slides, a pptx, a one-pager deck, to "restyle" a deck, to make slides "look like the STYLED one" / "not look vibe coded", or to turn notes/a transcript/an md into a presentation.
---

# msft-deck

Produce a .pptx that survives Kody's review on the first pass. The historical failure modes this skill exists to kill, in order of how often they burned turns: handing over a deck with a broken/ugly slide he had to screenshot back, overwriting slides he authored, walls of text, delivering HTML when he wanted pptx, and asking him to open/check things you can check yourself.

## Mode detection (do this first)

1. **REVISE** — he gave you a deck he (or a customer) touched: make ONLY the changes he asked for, in place, with python-pptx. Never regenerate, reorder, or "improve" other slides. His words: "keep the slides I had... THATS IT". When in doubt whether a slide is his, it's his.
2. **RESTYLE** — he gave a deck and wants it in the house style: keep content and slide order exactly; change fonts, colors, spacing, layout polish only.
3. **NEW** — build from notes/transcript/md/conversation. Distill the BUSINESS USE CASE, not the conversation that produced it. A transcript is raw ore, never an outline.

## Style contract (extracted from the canonical STYLED reference deck)

- 16:9 (13.33in x 7.5in). Build with python-pptx (installed, v1.0.2).
- Fonts: **Segoe UI** body, **Segoe UI Semibold** headings/emphasis, Consolas for code. Never Calibri, never the template default.
- Palette: text `#1B1A19` (near-black) and `#3B3A39`; secondary text `#605E5C`; accent/link **`#0078D4`** (Microsoft blue); positive `#107C10`; warning/highlight `#D83B01`; white `#FFFFFF` on dark fills. Nothing outside this palette without being asked.
- Type scale: titles ~40pt, section heads ~19pt, body 13–14pt, captions 10.5–12pt.
- Layout: generous whitespace, left-aligned text, consistent margins across ALL slides (misaligned elements = "looks vibe coded"). One visual anchor per slide max.

## Content rules (KISS — he has said this five times in a row)

- Default ≤ 10 slides. One idea per slide. ≤ 5 bullets per slide, ≤ 12 words per bullet. If a slide needs a paragraph, it's two slides or a talk track.
- Customer-facing decks: **strip PII** — no customer employee names, emails, or internal identifiers unless he explicitly says otherwise. Generalize ("a national retailer") if the customer name itself is sensitive.
- Output is a real `.pptx` on disk. HTML decks only when he asks for HTML. Never emojis.

## Self-review gate (non-negotiable — this is the whole point)

Before telling him anything is done:

1. Render: `soffice --headless --convert-to pdf --outdir <dir> <deck>.pptx`
2. **Read the PDF and look at every page.** Check each slide for: text overflowing or clipped by shapes, overlapping elements, off-palette colors, wrong/default fonts, ragged alignment vs neighboring slides, orphaned placeholder text ("Click to add..."), unreadable contrast.
3. Fix everything you find, re-render, re-inspect. Loop until a full pass is clean. Do not ask him to be the QA loop — no screenshots from him, ever.
4. In REVISE mode, additionally diff-check: confirm untouched slides are byte-identical in content (same text runs) to what he gave you.

## Handoff

- Save next to the source (or `~/Desktop` for ad-hoc asks), versioned `Name_v2.pptx` style if a prior version exists — never overwrite the file he gave you.
- Pop it open: `open -a "Microsoft PowerPoint" <deck>.pptx`
- Report: file path, slide count, one line per change made (REVISE/RESTYLE) or the slide-by-slide outline (NEW), and confirmation the visual pass was clean.
