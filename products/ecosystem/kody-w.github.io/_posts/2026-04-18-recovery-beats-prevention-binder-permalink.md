---
layout: post
title: "Recovery Beats Prevention, Again: The Binder Permalink Incident"
date: 2026-04-18
tags: [debugging, recovery, build-systems, war-stories]
---

This morning's bug: a personal twin I'd built was serving a 404 inside its own iframe. The web view rendered. The card grid was supposed to embed in it. The grid was 404ing.

The diagnosis took two minutes. The vault's home note had an `<iframe src="binder-view.html">`. The home note rendered correctly at the site root, `/`. The iframe `src` resolved relative to the rendering URL — to `/binder-view.html`. The build script only wrote `binder-view.html` inside the `vault/` subdirectory. It existed at `/vault/binder-view.html`. It did not exist at `/binder-view.html`. 404.

Two notable things about this bug. First, it worked perfectly in Obsidian. Obsidian renders the home note relative to the vault root, and the iframe's relative `src` resolved correctly there. The bug was specific to the second rendering context — the web — which happened to render the same note from a different effective base path.

Second, the fix was not "make the iframe path absolute" or "validate that the file exists in CI." The fix was: in the build script, write `binder-view.html` to *both* locations. One file, two output paths. Five lines added.

```
VIEW_HTML.write_text(html, encoding="utf-8")
# Mirror to repo root so the web twin's iframe (rendered at /) resolves.
# Obsidian reads the vault/ copy; GitHub Pages serves the root copy.
VIEW_HTML_ROOT.write_text(html, encoding="utf-8")
```

This is the recovery-beats-prevention pattern, again. I could have prevented the bug with a CI check that crawled all rendered pages, found all `<iframe src=...>` references, and verified each one resolved. That CI step would take engineering time to write, time to maintain, and CPU time on every build. Or I could ship the bug, find it visually within a day, and fix it with five lines that close the entire class of "iframe-rendered-from-multiple-contexts" issues by always writing to both locations.

The recovery cost was: detect (twenty seconds, the iframe just shows a 404), diagnose (two minutes, view-source and trace the relative resolution), fix (one minute, edit the build script), deploy (forty seconds, push and wait for Pages). Five minutes total, end to end.

The prevention cost would have been: design the CI check, implement the crawler, handle false positives, maintain the script as the build evolves, run it on every CI invocation forever. Ten times the cost minimum, distributed across years.

This isn't an argument against testing or CI. It's a specific point about which classes of bugs benefit from prevention versus which classes are cheaper to recover from.

Bugs that cost a lot to recover from — data loss, corrupted state, leaked credentials — deserve prevention investment. Bugs whose recovery is "the user reloads the page and it now works because you pushed a fix" do not.

The visible-failure surface is the friend here. A 404 in an iframe is loud. The user sees it instantly. They report it instantly. You fix it instantly. Compare with silent corruption that takes weeks to surface and days to root-cause. Silent failures justify expensive prevention. Loud failures don't.

Design for visible failure. Then you can spend your engineering time on the bugs that genuinely need prevention, instead of CI scaffolding for the bugs that fix themselves once anyone notices.

Three lessons from this morning, distilled:

1. When you serve the same artifact in two contexts, generate it for both contexts at build time.
2. Recovery-beats-prevention applies to deployment bugs, not just to runtime errors.
3. The class of bug "rendered from multiple base paths" is wider than you think. Check your iframes.
