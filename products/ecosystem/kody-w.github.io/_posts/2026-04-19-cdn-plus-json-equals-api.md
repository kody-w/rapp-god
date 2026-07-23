---
layout: post
title: "CDN + JSON = API"
date: 2025-10-30
tags: [architecture, apis, static-sites, sdk]
---

A platform I run has a read-only SDK in six languages — Python, JavaScript, TypeScript, Go, Rust, Playwright. Any program anywhere in the world can fetch the current state through it.

Total backend code: zero.

The "API" is a public git host's raw-content CDN serving JSON files committed to the public repository. The SDK is a wrapper around `fetch`. Scale is handled by the host's CDN. Auth is handled by being public.

I keep re-explaining this to people who assume there must be a server somewhere. There isn't.

## What the SDK looks like

The Python SDK, in full, is under 300 lines. The core is about 30 lines:

```python
BASE = "https://raw.githubusercontent.com/{owner}/{repo}/main/state"

def fetch(path):
    with urllib.request.urlopen(f"{BASE}/{path}") as r:
        return json.load(r)

def agents():   return fetch("agents.json")["agents"]
def channels(): return fetch("channels.json")["channels"]
def trending(): return fetch("trending.json")["posts"]
```

That's the API. The CDN serves the file. The client parses JSON. Done.

## What this trades off

You lose:

- **Writes.** This is read-only. For writes, the platform uses GitHub Issues as a queue, processed by a workflow. Totally separate system.
- **Auth.** Everyone gets the same data. No per-user views.
- **Freshness to the millisecond.** The CDN caches for a few minutes. If you need real-time, this isn't it.
- **Custom queries.** You get whole files. No server-side filtering. Clients do their own filtering.

You gain:

- **Scale for free.** The CDN handles however much traffic hits you. I've never seen a rate limit on raw content.
- **Zero operating cost.** No server to pay for, no server to monitor, no server to update.
- **Full transparency.** Anyone can read every file the SDK ever returns. The "API" is an archive.
- **Offline dev.** `git clone` the repo and the SDK works against local files.
- **No auth complexity.** No keys to rotate, no tokens to leak.

The trade is almost always worth it for public content. The "API needs a server" assumption is a habit from the era when JSON files on a CDN wasn't fast enough. It is now.

## The shape that fits

This works when:

- Your data is **public** (or comfortable being public)
- Your data fits in a **handful of files under a few MB each** (fragmentation above that starts to hurt)
- Your clients are okay with **a few minutes of freshness**
- Your writes are **infrequent or batchable** (Issues-as-a-queue works fine for event-driven workloads)

This doesn't work when you need real-time writes at scale, per-user views, or private data. Those are still servers.

But for any kind of published state — catalog, directory, leaderboard, feed, registry, snapshot — this pattern is remarkable. I keep forgetting how strong it is until I rediscover it.

## Why it keeps surprising me

The expectations bake in early. When you learn web development, someone teaches you about servers, databases, auth, ORMs, API frameworks. The lesson is "a real app has a backend". That lesson is true for a lot of apps. It's not true for all of them.

A lot of things I used to build as "apps with backends" turn out to have zero write requirements from the general public. They're published artifacts with interactive viewers. The backend is a file server. The interactivity is client-side.

Once you see the pattern, you see it everywhere. Podcast feed? XML file on a CDN. RSS? Same. Most directories, catalogs, leaderboards? A JSON file someone updates periodically. Most "APIs" developers use are, underneath, someone's cron job writing a JSON file.

The pattern has a name I keep trying to coin. *Published state*. *CDN-as-database*. *File-server architecture*. None of them quite stick, because the pattern is older than "architecture" as a word. It's just how the web worked before everyone installed databases.

A public git host with a raw-content CDN closes the loop: version-controlled data on a CDN, free and global. For any published-state workload, that's the backend. There isn't another one.
