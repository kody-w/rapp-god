---
layout: post
title: "One URL Per Audience: the Presenter-Mode HTML Slide"
date: 2026-04-24
tags: [html, pitch, content, distribution, founders]
---

PDFs are the default container for a pitch slide. They shouldn't be.

A PDF is a file you send as an attachment, where the reader has to open it out of their email, probably in a reader app, probably on a phone where it renders at 40% scale. If you want to update it, the recipient has yesterday's version forever. If you want to know whether they looked, you don't.

A single-page HTML slide is a URL. You paste it in a chat. It opens in a browser tab, full-bleed, hitting the screen edge-to-edge. It updates when you push to main. It's cacheable, linkable, and indexable. You can A/B the wording. It prints to a PDF if anyone really wants one.

I shipped seven of these this week. One URL per audience.

## The pattern

Pick your audiences first, not your slides. Each audience gets a URL:

- `one-pager.html` — the general pitch
- `leadership.html` — execs, outcomes-shaped
- `process.html` — sellers/partners, how the workflow runs
- `partners.html` — the partner's lens on the handoff
- `use-cases.html` — "what can this build?" with concrete scenarios
- `faq-slide.html` — top four questions, 2×2 grid
- `security.html` — CISO / compliance lens

Each page is one file. Self-contained. No server. Deployed as static HTML on GitHub Pages. Every page has:

- A kicker at the top telling the reader who it's for.
- One hero line in gradient type, sized with `clamp()` so it reads on a 4K projector and on a laptop.
- Three to five content blocks laid out with CSS grid.
- A closing hinge line in italic — the single sentence the reader should walk away with.
- A hidden `<nav class="sr-only">` with links to sibling pages, for search engines and screen readers; invisible to the visitor.

Nothing else. No header. No footer. No cookie banner. No "click here to contact sales."

## Why this beats a deck

Decks imply a speaker. A URL stands on its own. The single most valuable property of a deck — "the reader already has the context because I'm talking" — is exactly the property you don't want when your goal is to hand the artifact to someone and let it do its job.

One URL per audience also disciplines your writing. You can't reuse the same slide for the CISO and the seller. You have to pick what each reader needs to know. That forces specificity. The result is better writing for each reader than any shared deck could give either one.

## The print-to-PDF move

Every page has a `@media print` block that strips decoration and keeps the hero + content + hinge line intact on one page. So if someone insists on a PDF, they hit Cmd-P and get a clean single-slide PDF out the other side. The HTML is the source; the PDF is the disposable print.

I never send the PDF. I send the URL. The URL is the artifact.

## A few construction notes

- **System-font stack.** No web fonts to load. Pages render instantly.
- **Inline `<style>` and `<script>`.** One HTTP request per page. No build step.
- **CSS custom properties for theming.** A `[data-theme="light"]` block swaps every color; a tiny `<script>` in the head picks the theme from `prefers-color-scheme` or a saved preference. The reader's OS setting is respected by default.
- **Viewport-responsive typography with `clamp()`.** `font-size: clamp(2rem, 4.2vw, 3.6rem)` means the headline grows with the viewport until it hits a sensible ceiling. Works on phones, tablets, projectors, laptops.
- **`animation-delay` staggered 1→5** for the entry fade-up. The page reveals itself in under a second.

The whole pattern is ~400 lines of HTML + CSS per page. One engineer can write and maintain the whole catalog. The recipient just gets a link.

If you find yourself emailing a deck as a PDF in 2026, you already lost the audience. Send the URL. Let the page do the work.
