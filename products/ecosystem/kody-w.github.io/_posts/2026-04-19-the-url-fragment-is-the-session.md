---
layout: post
title: "The URL Fragment Is the Session"
date: 2026-04-19
tags: [static-sites, url-fragments, state-management, design-patterns]
---

Every interactive tool I've shipped in the last six months has no backend. They're all static HTML on GitHub Pages. And every one of them, somehow, has *shareable state* — you can send someone a URL and they'll see the exact view you were looking at.

The mechanism is the URL fragment. The part after the `#`. Everybody's had one available since HTML was invented. Almost nobody uses it correctly.

## What goes there

The fragment is the only part of the URL the browser keeps entirely client-side. It never gets sent to the server. Which means on a static site, it's the one piece of the URL you can write into and read out of for free.

I use it as a compressed session object. One tool I built (a "reverse seeder" — paste in an artifact, get a generated prompt) encodes the pasted artifact and the selected style like this:

```
#a=<base64 of artifact>&s=<style>
```

Another tool (a "time capsule" view of the repo at a given commit) encodes the current commit short-SHA:

```
#c=<sha7>
```

No cookies. No localStorage. No database. Paste the URL into Slack and the receiver loads the exact state.

## The pattern

The three moves:

1. **On state change, update the fragment.** Use `history.replaceState(null, '', '#...')` so you don't pollute the back button with every tiny change.
2. **On page load, read the fragment.** Parse it like a query string: `new URLSearchParams(location.hash.slice(1))`.
3. **Decode and restore.** Base64-decode the blobs, set the form values, re-run whatever computation produced the view.

That's the whole pattern. Fifteen lines of code. Every static tool should have it.

## Limits

URLs have a practical cap around 2000 characters. Base64 inflates text by 33%. So you can fit about 1400 bytes of real content. That's enough for a seed, a query, a tweet-length input, or a pointer to something bigger. It is not enough to embed a 10KB artifact.

For bigger state you need a different pattern: hash the state, put it in a gist or a raw file, reference the hash in the URL. But 90% of what you think needs a backend actually fits in a fragment.

## Why nobody does this

I've asked around. The usual answers are "I didn't know you could" and "I tried it once and the routing library fought me". Both are about the framework tax. In vanilla JS, `location.hash` is two characters and a getter. In React Router or Vue Router, it's a philosophical debate.

The fragment is a static-site ally. It's free. It's portable. Every URL is a bookmark. Every share is a reproducible state. Once you internalize it, you stop reaching for auth systems for things that don't need auth.

The session is in the URL. Everything else is ceremony.
