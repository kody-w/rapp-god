---
layout: post
title: "Permalinks Are a Promise"
date: 2026-04-18
tags: [permalinks, urls, doctrine, web, content]
---

A URL that you publish is a promise. The promise is: if someone clicks this URL today, in a month, in a year, in a decade, they will get the same content. Maybe rendered differently. Maybe with new wrapper chrome. But the *thing* the URL refers to will be there.

This sounds anodyne. It is not how most people on the web operate. The default behavior is link rot — URLs change when sites redesign, posts get renamed, slugs get tweaked, content gets moved to a "premium" section, blogs get migrated to new hosts that don't bother to set up redirects. The web is hemorrhaging permalinks. Every personal site that doesn't actively defend its URL space participates in the hemorrhage.

A few rules I follow now, after watching too many of my own old links break:

**Pick your slug pattern early and never change it.** If your blog uses `/YYYY/MM/DD/slug/`, every post forever uses that pattern. If your project uses `/projects/<slug>/`, every project forever uses that pattern. The pattern is the promise. Changing the pattern is breaking the promise on every existing URL at once.

**Do not put metadata in the URL that can change.** A URL that includes the post's category, the author's username, or the section name will break when any of those change. The URL should contain only stable identifiers — a date, a slug, an ID. Categories and authors and sections belong in the page, not the path.

**Slugs are content, not display.** Once a slug exists, it stays. If you discover the slug has a typo, leave the typo. Add a redirect from the corrected version to the original if you want, but never the other way. The slug is part of the URL contract.

**Set up redirects when you must move.** If you genuinely have to move a piece of content — a blog migration, a domain change — set up redirects from every old URL to its new location. The redirect is how you keep the promise even when the underlying content moves. Redirects can be 301 (permanent) or 302 (temporary); use 301 if you mean it.

**Rendering is allowed to change. Identity is not.** A post can be redesigned, restyled, even rewritten. Its URL refers to the *same piece of content*, even if the content evolves. What's not allowed is the URL silently starting to refer to a different piece of content, or to a 404, or to a vague index page.

**404s are loud failures, not ambient ones.** If a permalink breaks, that is a bug. Treat it as a bug. Fix it as you would fix any other bug — find the broken URL, restore the content or set the redirect, deploy. Don't let 404s accumulate. They corrode trust faster than any other class of defect, because they are visible to outside observers and not visible to you.

**Test old URLs occasionally.** Every few months, pick a random sample of your own old URLs from a few years back and click them. If any 404, that's a regression. Fix it. The fact that you don't link to those URLs anymore doesn't matter; someone else might.

The deeper point is that a personal site is partly a kindness to the future. Future people who follow links to your site, expecting to find what they were promised, are doing the basic work of the web — connecting one source to another. Your job, as a publisher, is to honor those clicks. Every kept permalink rewards a click that was made in good faith. Every broken one punishes one.

Honoring permalinks is also a kindness to your own future self. The number of times I've gone looking for an old post of my own and found that I'd accidentally broken the URL is too high. Each time, the cost is the same: rewrite a slug, set a redirect, mutter about past-me. Past-me would have saved me the work by getting the URL right the first time and never touching it again.

A static site with a frozen URL pattern, served from a CDN, with a date in the path and a stable slug, is the cheapest possible permalink machine. It's also the most reliable. The discipline that makes it work is small: pick the pattern, freeze the pattern, never break the pattern.

Make the promise. Keep the promise.
