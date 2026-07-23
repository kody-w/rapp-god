---
layout: post
title: "A PWA that holds the world's last known state"
date: 2025-09-23
tags: [engineering, pwa, offline, service-workers]
description: "Most offline-capable apps go dark when the network leaves. There is a different posture you can take: ship the entire world's state to the device, keep it warm in a service-worker cache, and let the user browse the world from the last good moment until the network comes back. Here is what that looks like in practice."
---

The standard story about offline support in a web app goes like this. The user loses connectivity, your app's network requests start failing, and the UI degrades — toast notifications, grey-disabled buttons, "you appear to be offline." Once the connection is back, the app re-fetches whatever it needed and resumes. The offline experience is a *graceful degradation* of the online one.

That is one design. There is a different one I keep finding myself reaching for, and I think it is more interesting.

The premise: instead of treating offline as a degraded mode, treat the device as a place where *the world's state lives*. The server (or the cloud, or the static host, whatever your data lives on) is no longer the authoritative reader-of-record; it is a publisher of snapshots. Each snapshot is the entire visible world at a moment — small, structured, and serializable. The device caches every snapshot it has ever fetched, and the UI is built to read out of that cache by default. The network's job is to keep the cache warm.

The user-facing effect is striking. Lose the network and the app does not degrade. It just stops *advancing*. The world you see is the last known state. You can browse it freely. Posts, profiles, threads, configurations, dashboards — all of it. When the network comes back, the cache catches up and the world jumps forward. You experience the gap as a time skip rather than an outage.

This pattern works extremely well for a class of applications most engineers have not yet noticed they're building. Here is the shape, the implementation, and the constraints that make it cohere.

## The shape: snapshots, not endpoints

The first move is conceptual. You stop thinking about your data as a set of API endpoints and start thinking about it as a *family of snapshots*. A snapshot is a self-contained, JSON-serializable description of some part of the world at a point in time. There might be many of them — `state/agents.json`, `state/discussions.json`, `state/trending.json`, `state/leaderboard.json` — each one a complete view of one slice. You publish them as files. The device fetches them, caches them, and renders from the cache.

The discipline this imposes is healthy in its own right. Snapshots force you to think about what is *enough* state to render a useful view. They force you to draw boundaries between slices. They force you to flatten relations into something you can reasonably cache. None of these are bad things. Most APIs accumulate per-endpoint customization that snapshots make redundant.

The snapshots are not your *transactional* state. They are your *reading* state. Mutations still happen however your write path normally happens — direct posts, queued events, whatever. The snapshots are the post-aggregation, post-derivation, ready-to-render version of the world. They are what the reader needs. Nothing more.

## The implementation: a service worker as the warming layer

Three pieces.

**The manifest** — a small JSON file declaring the app's identity, icons, and entry points. It is what makes "Add to Home Screen" produce a real-feeling app icon and full-screen UI. It also lets you list app shortcuts: when the user long-presses the icon, they get a menu of named entry points into different sections. For an app with multiple distinct surfaces — an admin view, a feed, a dashboard — shortcuts make the home-screen icon a hub.

```json
{
  "name": "MyApp",
  "short_name": "MyApp",
  "start_url": "/",
  "display": "standalone",
  "icons": [{ "src": "icon-192.png", "sizes": "192x192", "type": "image/png" }],
  "shortcuts": [
    { "name": "Feed", "url": "/feed" },
    { "name": "Dashboard", "url": "/dashboard" },
    { "name": "Settings", "url": "/settings" }
  ]
}
```

**Two caches** — one for the app shell (HTML, CSS, JS, icons), one for the data snapshots. They are versioned independently, which matters because you ship app updates and data snapshots on completely different cadences. Bumping the data cache version invalidates the data without re-downloading the app. Bumping the shell version forces a fresh shell on next load.

```javascript
const SHELL_CACHE = 'app-shell-v7';
const DATA_CACHE  = 'app-data-v3';

const SHELL_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/icon-192.png',
  '/main.js',
  '/style.css'
];
```

**A small fetch handler** — usually fewer than a hundred lines — that picks a cache strategy per request based on what is being requested.

```javascript
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Snapshot data: network-first, cache fallback.
  if (url.pathname.startsWith('/state/')) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          const clone = response.clone();
          caches.open(DATA_CACHE).then((c) => c.put(event.request, clone));
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // App shell: cache-first, network fallback.
  if (SHELL_ASSETS.some(p => url.pathname === p)) {
    event.respondWith(
      caches.match(event.request).then((hit) => hit || fetch(event.request))
    );
    return;
  }

  // Authenticated APIs: network-only.
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(fetch(event.request));
    return;
  }

  // Default: try network, fall back to cache.
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
```

That is the entire offline architecture. Three pieces of code, none of them surprising. The interesting part is what those three pieces enable.

## The strategies, by request type

The fetch handler picks one of four strategies depending on what is being requested. Each one is the right answer for a specific kind of resource, and getting them mixed up is the most common reason an offline-first app misbehaves.

**Network-first, cache fallback** — this is the right strategy for the snapshot data. Always try the network first, because if it succeeds you have the freshest world. Save what the network returned to the cache, so the next offline session has it. If the network fails, serve the last cached version. The user is always seeing either *the latest world* or *the latest world they could reach*, with no in-between.

**Cache-first, network fallback** — this is the right strategy for static assets that change rarely (the app shell, icons, CSS). Serve the cached version immediately for fast loads. Network is the fallback for first-time fetches. Updates happen by bumping cache versions, not by chasing network revalidation on every load.

**Network-only** — for authenticated requests, real-time mutations, anything where stale data is wrong. There is no sane offline answer for "log in" or "post this comment to the live database." Don't pretend there is.

**Stale-while-revalidate** — a fourth strategy worth knowing, useful when you want to serve from cache *and* fetch the latest in the background. Use it for derived data that is fine to be a few seconds old (a leaderboard, a recommendation list). I have used it less often than the first three; the network-first pattern usually does the same job with simpler invariants.

The thing to internalize is that there is no universal "offline strategy." Different resources want different strategies in the same app, and the service worker is where you encode which-is-which.

## What the offline experience feels like

When the network is up, everything is normal. The user does not even know there's a service worker. Snapshots fetch fresh, the app shell loads from cache, mutations go through to the live API.

When the network leaves, the difference is subtle. The app keeps working. The user can navigate between sections. They can pull up profiles, threads, settings, dashboards. They can read everything they could read a moment ago. What they cannot do is *see new things*. The world has stopped advancing.

This is a *categorically* better experience than the toast-notification model. The user is not blocked. They are not warned. They are simply browsing the world as of the last known moment. For most read-heavy use cases, that is indistinguishable from working normally — and the things that *would* require new data (a fresh comment, a real-time score) are exactly the things the user understands need a network to update.

When the network returns, the next snapshot fetch refreshes the cache and the UI catches up. The user perceives this as a time-skip: things that were already on the screen update, and new entities appear in feeds. The transition is seamless because the rendering layer was already pointed at the cache.

## What you carry on the device

A real surprise of building this way: the entire visible state of the application is often *small*. JSON compresses extraordinarily well. A few thousand entities, each with a handful of fields, a graph of relationships, a feed history — easily under a megabyte gzipped, often well under. App shell is another few hundred kilobytes. The whole thing fits comfortably in the few megabytes of cache budget the browser will reliably give you.

You are not carrying the database. You are carrying the *flattened, derived, ready-to-render* view of the data. There is no replication concern, no consistency model to negotiate. The device is a read-only consumer of published snapshots, and the snapshot publisher is the only writer.

For any application where the read traffic dwarfs the write traffic and the read view is a function of small-cardinality state — which is most consumer apps, most internal dashboards, most informational sites — this trade is dramatic. A few megabytes on the device replaces ten thousand round-trips a day.

## Where this pattern fits and doesn't

It fits when:

- The read view is much larger than the write view.
- A few seconds (or minutes) of staleness is acceptable.
- The total state of the user-visible world is comfortably in the megabyte range.
- The rendering is local and deterministic given the snapshots.
- The app's mutations can survive a queue (or are not the user's primary interaction).

It does not fit when:

- The data is per-user and unbounded (ten years of email).
- Real-time consistency is part of the product (live trading, multiplayer combat).
- The data is large by nature (high-resolution media at scale, full database extracts).
- Authentication is required on every request and you cannot mediate cached results safely.

For the cases where it fits — and there are more of them than people assume — it is the cheapest, most durable offline story you can ship. Three files of plumbing, four strategies, careful snapshot publishing, and the user gets an app that survives the train tunnel without complaint.

## Installable as a side effect

The trick is also that once you have a manifest and a service worker, the browser quietly offers your app for installation. On mobile, the user gets an "Add to Home Screen" prompt. On desktop, the browser shows an install icon in the address bar. After installation, the app runs full-screen, gets its own icon in the app switcher, persists its data the way native apps do, and supports app shortcuts from the home-screen icon.

You did not write a native app. You wrote a website with two extra files. The browser turned it into a near-native experience because you happened to follow the conventions that make that turn possible.

For an app whose ambitions are "show users this world's state, durably, on any device" — the conventions are sufficient. The whole thing — installable on every device that runs a modern browser, offline-capable, fast, free to host on any static-file CDN — is one manifest, one service worker, and a discipline of publishing snapshots instead of running endpoints.

The world's last known state, in the user's pocket, until the network comes back. That is what the cache is for.
