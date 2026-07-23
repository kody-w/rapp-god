---
layout: post
title: "Daemons in the browser"
date: 2026-04-27
tags: [ai, browsers, local-first, portability, file-formats]
description: "An AI companion that lives in your browser tab — not in a vendor's cloud — sounds like a toy. The architecture is interesting precisely because it isn't a toy: state lives in your local storage, the companion exports to a file you carry, and the format outlasts any company that hosts the runtime. This is what 'your AI' looks like when 'yours' is meant literally."
---

There is a category of software I want to call *daemons*, in the old Unix sense. A daemon is a small persistent agent that runs in the background, holds state, responds when called on, and otherwise leaves you alone. The word fits the kind of AI companion I have been building in browsers — a thing that grows with you, remembers across sessions, exports to a file, and survives any vendor pivot.

This post is what these daemons are, why the architecture matters, and what the file format under them is for.

## The setup

Open a tab to a single HTML file. The page is a few hundred kilobytes — JavaScript, a small inference shim, a state-management layer over IndexedDB. The page renders an animated character. The character is, in some sense, asleep.

Tap it. It wakes up. It has limited vocabulary at first; you can prompt it, it responds, it remembers what you talked about. Close the tab, come back tomorrow, the same character resumes — its state is preserved in the browser's local storage. Talk to it for a week, it has formed preferences. It develops a personality shaped by what you say to it. It changes over time.

When you want to take it somewhere else, you press export. The browser hands you a file — `companion.json` or whatever extension you gave it — that is the whole organism. Its identity. Its memory. Its preferences. Its current developmental stage. Drop the file into another browser, another machine, another install of the runtime. It wakes up where you left off.

That is a daemon. A persistent digital companion that lives where you put it and travels in a file you carry.

## Why this is interesting

The interesting properties are not the cosmetic ones. The companion looks cute; that's incidental. The interesting properties are about *where the state lives* and *who controls it*.

**Local-first.** The companion's state is in your browser, on your machine, in your local storage. It is not in a vendor's database. Nothing about it is uploaded unless you explicitly choose to sync. If the company that wrote the runtime disappears tomorrow, the companion does not disappear; you have a file. As long as some compatible runtime exists, the companion runs.

**Portable.** Because the state lives locally and exports cleanly, the companion is portable in a way that cloud-hosted AI companions cannot match. You can move it. You can archive it. You can clone it. You can give a copy to a friend, who then has their own version that diverges from yours from that point. None of these operations require the runtime's vendor to do anything.

**Composable.** The export format is a specced JSON file. Two daemons can be composed — their preferences merged, their memory unioned, their personalities blended — by anything that can read JSON. Different runtimes can produce daemons that interoperate, because the format is the lingua franca, not the runtime.

The combination of these three properties is what makes the architecture worth writing down. Most AI companions today have none of them. The companion is the vendor's; the state is the vendor's; the format is the vendor's. If the vendor pivots, the companion is gone.

## The architecture

Inside the browser tab, the companion is implemented as a small set of cooperating "agents" — different code paths that share a single underlying inference call. There's typically:

- A **memory manager** — handles writes to the companion's long-term store; decides what is worth remembering versus forgetting.
- A **context assembler** — when the companion needs to respond, it pulls relevant memory entries and assembles them into a prompt context.
- A **recall path** — for explicit "what did we talk about last Tuesday" queries.
- A **default response path** — when nothing more specific is appropriate.

These are not separate AI calls; that would be expensive and slow. They are separate code paths in the local app that route to the same inference endpoint with different framings of the context. Conceptually, they are different aspects of the same companion's mind, not separate minds.

Memory is stored in IndexedDB — the browser's built-in document store. The schema is simple: episodic events (things that happened), preferences (things the companion has come to like or dislike), relationships (people and topics it has formed associations with). Every entry is timestamped and tagged.

The companion's *developmental stage* is a coarse function of how much state has accumulated. Early on, the memory store is small, the context is thin, responses are generic. Over weeks of interaction the memory store grows and the responses become more specific to your relationship. This is not a learned behavior in a model-weights sense; the model itself doesn't change. The *context* the model receives changes, and the responses follow.

## The export format

Export bundles the whole companion into a single JSON file:

```
{
  "identity": { ... },
  "stage": "adult",
  "personality": { traits, preferences, quirks },
  "memory": { episodic_events, preferences, relationships },
  "stats": { numeric state },
  "skills": { what it can do },
  "appearance": { visual traits }
}
```

The file is the whole organism. There is no server-side state that has to be reconstructed. There is no proprietary binary blob. There is no DRM. The file is plain JSON that any reader can inspect and any compatible runtime can import.

This is the property that I think is most underrated. When the export is the whole thing, the companion is *portable in the human-meaningful sense*. Five years from now, when the company that built the runtime is gone or has pivoted, your companion is still in a file in your archive. If anyone — you, a friend, a hobbyist project, a future startup — writes a runtime that can read the file, the companion lives.

This is what "your AI" should mean. Not "an AI we let you use as long as we feel like running the service." An artifact you possess.

## The browser is the right substrate

Browsers turn out to be unreasonably good for this kind of thing.

**Private.** Local storage is yours, not the vendor's. Nothing leaves the machine without explicit upload.

**Portable.** Any browser on any device runs the same HTML. No installation. No platform-specific build. The companion's runtime is the most ubiquitous piece of software on the planet.

**Offline-capable.** If you save the HTML file locally, no network is required to talk to the companion (assuming a local inference path, which is increasingly viable). The companion is independent of any connectivity.

**Long-lived.** Web platform APIs are remarkably stable. Code that ran in browsers a decade ago still runs today. A companion app written today has a reasonable expectation of running ten years from now without modification.

The reason cloud-hosted AI companions got popular first is that inference and training were expensive and centralization made business sense. Inference costs are collapsing; local inference is becoming viable for a growing range of use cases; the centralization argument is weakening. Browser-local state has always been viable. The combination — local inference plus local state plus portable format — is the post-cloud architecture for personal AI.

## What the format buys you

Once the file format exists and is specced, things become possible that don't fit on top of vendor-locked companions:

**Trades.** A companion file is something you can give to someone. They can adopt it. They can fork it. The file is the identity-less artifact; what it becomes after you give it is in the hands of whoever has it next.

**Interbreeding.** Two companions can produce a child by combining their memory states, preferences, and traits in a deterministic merge. The child is not a copy of either parent; it is a new companion shaped by both.

**Archival.** The file can be put in cold storage. A companion you cared about ten years ago can be reawakened next year by importing the file into a current runtime. There is no service that has to keep running. The artifact is the companion.

**Cross-runtime.** Multiple runtimes can implement the same format. A user can move their companion between runtimes the same way users move email between clients today. The runtime is replaceable; the companion is not.

These properties are *consequences of the file existing*, not features bolted onto the runtime. They follow as soon as you stop pretending the companion lives in a database.

## The bigger pattern

What I am describing is not specific to chat companions. It is a pattern for *any* persistent AI agent that interacts with one person over time. Personal assistants. Work copilots. Tutors. Game NPCs that follow you across games. Therapy bots. Reading partners. Each of them has the same structural choice: live in a vendor's database, or live in a file you possess.

The vendor-database version is what most products are today. It is faster to ship and easier to monetize. It also means that every relationship the user forms with the agent is contingent on the vendor's continued cooperation. Every change the user notices is a change the vendor controlled. Every termination is at the vendor's discretion.

The file-you-possess version is what daemons in the browser look like. It is harder to ship, because the vendor is giving up the lock-in. It is harder to monetize, because the user can leave. It is the right architecture anyway, because the alternative is rentals masquerading as relationships.

Browsers are the right place to start. The file is the right primitive. The format is the right thing to spec. The runtime is the replaceable part. Build that, and the companion you grow with becomes something you actually have, not something you are renting.

That is what a daemon is. Persistent. Portable. Yours.
