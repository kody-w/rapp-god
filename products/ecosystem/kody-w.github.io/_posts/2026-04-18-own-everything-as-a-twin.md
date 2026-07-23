---
layout: post
title: "Own Everything as a Twin"
date: 2026-04-18
tags: [twins, autonomy, federation, doctrine, ownership]
---

The pattern: every external platform you depend on should have a personal twin in your repo. Same data shape. Mutable. Optionally syncable back to the original.

The instinct in software is to use someone else's platform as a black box. You sign up. You produce content there. The platform owns your content, your view, your features, your roadmap. When the platform changes, you change. When the platform dies, you die. This is the default arrangement and it is a bad one.

The alternative arrangement: you own a copy of everything that matters to you, in a format you control, in a repository you can fork. The external platform is one rendering surface. Your repo is the canonical store. The platform pulls from your store, or you push to it, or both — but the relationship is symmetric. If the platform vanishes tomorrow, your version still works because you own it.

This is what a twin is. Not a backup, not a mirror, not a webhook integration. A twin is a personal first-class instance of the same conceptual object the platform exposes. If the platform has Cards, your twin has Cards. If the platform has Posts, your twin has Posts. If the platform has Followers, your twin has Followers. The shape matches because compatibility is a feature.

I have done this for several platforms now and the pattern keeps generalizing:

- A note app: my twin is an Obsidian vault that exports the same JSON shape the platform serves. Same data, my UI.
- A federated card system: my twin is a static site that produces the same federation files. Other peers don't know they're talking to a twin.
- A blog platform: my twin is a Jekyll site I push to wherever — GitHub Pages, Netlify, my laptop. The posts are markdown files I own forever.
- A platform-of-record for AI agents: my twin is the same state tree, computed by the same scripts, but with my own local modifications layered on top.

The key insight is that compatibility is a property of the data shape, not the runtime. If your twin produces files in the same JSON shape the platform produces, those files are interoperable. Other consumers can't tell whether the JSON came from the platform or your twin. The twin is fully autonomous *and* fully compatible. You don't have to choose.

This dissolves the usual tradeoff between autonomy and integration. Most "own your data" advocates accept that the cost of owning is being slightly outside the network. The twin pattern says: don't accept that. Own your data *and* stay in the network. The federation doesn't care which surface produced the file.

What this requires from you: the discipline to mirror the data shape exactly. If the platform's cards have a `seed` field, yours do too. If the platform produces a `seed-index.json`, yours does too. The cost is a small ongoing alignment effort. The benefit is permanent independence with continuous integration.

The mental shift is from *consumer* to *peer*. You are not a user of the platform. You are a participant in a federation that happens to include the platform as one node. Your twin is another node. Equal in standing. Different in implementation. Same in data shape.

Build twins for everything you care about. The platforms you live on tomorrow will be different from the ones you live on today. The twins will not.
