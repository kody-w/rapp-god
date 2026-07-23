---
layout: post
title: "Iframe Twins for Surface Compatibility"
date: 2026-04-18
tags: [twins, iframes, fallback, compatibility, ux]
---

When you build a personal twin of a platform, you face a deployment question: where does it live? On the surface of the parent platform? On its own domain? In a desktop app?

The answer is usually "all of the above," and iframes are the unifier that makes that cheap.

Concrete example. I have an Obsidian vault that holds a card collection. Obsidian renders markdown notes natively, with backlinks and graph view and search. That's the primary surface. But many people don't use Obsidian. They want the same collection on the open web.

I could build two completely separate UIs — one for Obsidian, one for the web. That's twice the maintenance. Or I could build one UI and run it in both contexts. That's the iframe play.

The single-purpose card grid lives at `binder-view.html`. It's self-contained: HTML, inline CSS, inline JavaScript, no external dependencies. It can be opened directly in a browser. It can also be embedded in any context that allows iframes. Including, conveniently, an Obsidian note that has HTML embeds enabled.

So the same file serves three modes:

- **Standalone web view:** open `binder-view.html` directly. Looks like a normal site.
- **Embedded in the Obsidian vault home note:** an `<iframe src="binder-view.html">` makes the card grid appear inline in the vault. Obsidian users see it without leaving Obsidian.
- **Embedded in any other twin:** another personal twin that wants to surface my cards just iframes the same URL.

One file, three rendering contexts, zero duplication.

The iframe pattern handles the surface-compatibility problem in general. When the parent platform doesn't allow your JavaScript to execute, you give it an iframe. When the parent platform sandboxes your CSS, you give it an iframe. When the parent platform changes its DOM and breaks your injection script, you give it an iframe. The iframe is a universal translator between "the platform's runtime" and "your runtime."

A few rules that make this work in practice:

- **Make the iframed page look intentional.** It should not look like an embed of a separate app. Match the typography. Match the color palette. Make it feel like the host page just grew a card grid, not like you bolted on a widget.
- **Self-contain everything.** No external scripts, no CDN fonts, no analytics pixels. The iframe should work even when the parent context blocks third-party requests. This often means inlining everything at build time.
- **Mirror the file twice if needed.** I learned this the hard way: my iframe `src="binder-view.html"` resolved to the wrong directory in one of the rendering contexts. Two-line fix in the build script: write the file to both locations. Same content, two paths, both contexts work.
- **Provide a "if iframes are blocked, click here" fallback.** Some hosts strip iframes. The host note explains what to do — open the file directly, or enable HTML embeds in settings.
- **Respect the parent's height.** Either set a fixed iframe height that's reasonable on most viewports, or use postMessage to communicate the natural content height up to the parent and let it resize.

The iframe is not glamorous. It's old technology, and people associate it with display ads and 2008 widgets. That association is wrong. Iframes are the cheapest deployment surface in the entire web platform. They make twins viable across hosts that have no extension API and no plugin system.

If your twin needs to live inside another platform, give it an iframe before you build a plugin. The iframe will work everywhere the plugin would, plus everywhere it wouldn't.
