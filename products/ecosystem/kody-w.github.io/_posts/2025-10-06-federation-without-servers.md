---
layout: post
title: "Federation without servers: any system that publishes JSON can talk to any other"
date: 2025-10-06
tags: [federation, distributed-systems, protocols, json, architecture]
description: "Two systems can federate without sharing a database, an auth provider, a message bus, or a message format. The minimum protocol is a manifest and a convention. Here is how it works and why it scales surprisingly far."
---

The default mental model for "two systems that share data" is heavyweight. Shared database. Shared identity provider. Authenticated APIs on both sides. Message queues. Schema registries. SDKs. Operational ownership of all of the above. The cost of getting two systems to talk is so high that, in practice, most pairs of systems that *should* share data simply do not.

It does not have to be that expensive.

I run two systems that share data. They do not share a database. They do not share authentication. They do not share message buses. They run on different codebases, different runtimes, different release schedules. They federate anyway, and the protocol that makes that possible fits in a few hundred bytes of JSON. This post describes the architecture, why it works, and where it runs out of road.

The thing the architecture replaces is *coordination*. The amount of coordination required to have two systems share a database, authenticate against the same provider, agree on a message format, version it across deploys, and operate it at uptime parity is astonishing. It is the implicit cost on every "let's just integrate them" conversation. Most teams pay it. They do not have to.

## The minimum protocol

Two systems can federate if they each agree to do exactly two things.

**One:** publish a small JSON manifest at a known URL describing what they are, what they have, and what they accept.

**Two:** read the other system's manifest and act on it.

That is the whole protocol. The manifest is the only required artifact. Everything else — auth, queueing, transport, schemas — either does not exist in this architecture or is replaced by the simplest possible thing that meets the requirement.

Here is what a minimum manifest looks like:

```json
{
  "identity": {
    "name": "system-A",
    "type": "discourse",
    "owner": "you-or-your-org",
    "raw_base": "https://your-host/system-A/main/"
  },
  "publish": {
    "agents": "state/agents.json",
    "topics": "state/topics.json",
    "events": "state/events.json"
  },
  "accept": {
    "submit_event": {
      "method": "github_issue",
      "template": "https://github.com/.../issues/new?template=event.yml"
    }
  },
  "version": "1.0",
  "updated_at": "2025-10-06T19:00:00Z"
}
```

Three sections. Identity tells anyone who is looking what this system *is*. Publish tells them what data it exposes and where to fetch it. Accept tells them what they are allowed to send back, and how. That is the contract.

A peer reading this manifest can:

- Identify the system unambiguously.
- Walk to any of the published data files at the listed paths.
- Know exactly what kinds of submissions the system accepts and how to make one.
- Know what version of the protocol they are dealing with.

The peer does not need a SDK. They do not need an account. They do not need to authenticate. They need an HTTP client. The data is public, the contracts are public, and the manifest told them everything they need.

## The transport, made cheap

Now we have to actually move data. Two pieces — read and write.

**The read path is a static file fetch.** Any HTTP client. Any caller. Anywhere on the internet. The published files are flat JSON on a public URL. A CDN sits in front of them whether you set one up or not, because that is just how the internet works for static files behind any modern host. Reads are fast. Reads are global. Reads cost nothing.

There is no read API. There is no GraphQL. There is no rate limit you have to manage. The "read API" is `GET https://host/path/file.json`. If your host is one of the major static-file hosts, you get caching and global distribution as a free side effect.

**The write path is whatever each system already has.** The manifest's `accept` section names the inbound channel. It can be:

- An HTTP webhook.
- An issue tracker that the system already polls.
- An email address.
- A specific file path in a shared storage bucket.
- Any inbox the system already operates.

The federation does not specify *one* write transport. It specifies that each system declares its own, and peers honor whatever that system has chosen.

This is the most common point of confusion. People expect the federation to dictate the write path — "submissions must go via HTTP POST to this endpoint." That is not necessary, and not having it is what makes the architecture cheap to adopt. If a system already has a way to receive structured submissions, the federation just *uses that*. No new infrastructure.

## A worked example

Imagine system A is a discussion board for one community and system B is a different one. Both run on infrastructure that publishes static files. Both want to share a stream of high-signal posts: a "trending across both" feed.

Without federation, you would build a service that pulls from both and merges. You would operate it. You would deal with its uptime, its rate limits, its caching, its cost.

With federation:

1. **System A publishes** `state/trending.json` — its own top items, refreshed hourly by whatever process A already uses.
2. **System B publishes** `state/trending.json` — same shape, on its own update cadence.
3. **Each system's manifest** declares "I publish trending at this path."
4. **Either side, or any third-party reader, can build a unified feed by fetching both files and merging.** No service. No daemon. Just two HTTP fetches and a merge function.

The merger is trivial. The merge is *idempotent* — running it twice produces the same answer if the inputs have not changed. The merge is *cacheable* — every reader can cache the result. The merge happens at *render time*, on the consuming side, with no central authority.

Notice what is missing. There is no shared trending service. There is no contract that says how the merge works (every reader can use a different merge if they want). There is no auth — both sides publish public data. There is no orchestration — each system updates on its own clock.

This is the whole shape. Two systems publish flat data. A merger somewhere on either side or in a third place reads both and produces the cross-system view. The merger does not need permission from either side; the data was already public.

## The patterns that fall out

Once you see the architecture, several useful patterns become free.

**Reading a peer is identical to reading yourself.** Your own system reads its own state files. Your peer's system reads its own state files. To read the peer, you fetch their manifest, walk to their file, and read it the same way. Your reader code does not branch on "self vs peer." It branches on "URL." That is a much smaller branch.

**Adding a peer is one config entry.** A system's "list of peers" is a list of manifest URLs. To start federating with a new peer, append their manifest URL to the list. The reader walks the new entry the next time it runs. No deploy. No code change. No re-architecture.

**Removing a peer is one config entry.** Drop the URL from the list. Their data stops flowing into your views. They are not informed; they do not need to be. You are not consuming their data anymore.

**Forking a peer is also one URL change.** If someone runs a fork of system B at a different URL, you can subscribe to the fork by updating one config entry. The fork does not need a new SDK. It does not need a new auth integration. It is the same shape with a different URL.

**Authentication is not part of the protocol.** If your system has *private* data alongside its federated data, that private data is not in the manifest's published list. Federated data is, by construction, public. This sounds like a limitation; it is actually the property that makes the architecture cheap. Two systems federating do not have to negotiate identity providers, JWT formats, or any of the rest. Public data plus a public manifest equals interoperability.

## Where this runs out of road

The architecture is not free in every dimension. Three failure modes are worth being honest about.

**Real-time signal is not first-class.** Federation works best for state that is reasonably current — minutes to hours of staleness. If you need sub-second updates across systems, this protocol is the wrong tool. You want a message bus or a streaming protocol. Federation is the eventually-consistent layer; it is not the live layer.

**Schemas drift unless you version them.** Two systems that started with the same shape can drift over time as each side adds fields independently. Without a `version` field in the manifest and explicit handling of multiple versions in readers, drift produces silent breakage. The mitigation is to version everything explicitly and to treat manifest schema changes as breaking changes that go through the same review your code goes through.

**The write side is asymmetric and that is OK.** When system A submits to system B's accept channel, A is at B's mercy. B may queue it, drop it, validate it, reject it. B's write path is operated by B's owners. A has visibility into "did my submission appear in B's published state?" — eventually consistent, observable, but not guaranteed in real time. The honest framing is: federation is a polite agreement, not a strict contract. Each side owns its own write semantics.

## When the architecture is exactly right

Federation-by-manifest is the right answer when:

- You have multiple systems that should share data but operate independently.
- The data is mostly public, or could be made public with no cost.
- Eventually consistent is fine — the freshness budget is minutes or longer, not milliseconds.
- You do not want to operate or be operated by a central federation service.
- You expect new peers to come and go without asking you to deploy code.

When that profile fits, the architecture is shockingly cheap. A manifest is a hundred bytes. The transport is a static file fetch. The peer addition is a config entry. There is no central operator and no infrastructure tax.

## When to reach for something heavier

Federation-by-manifest is the wrong answer when:

- The data is private and access has to be authenticated per request.
- Updates have to propagate in seconds, not minutes.
- The schema is rapidly evolving and you cannot tolerate drift.
- You need transactional guarantees across systems (commit-or-rollback semantics).

In any of those cases, you have a real distributed-systems problem, and you want a real distributed-systems tool — a message bus, an event mesh, a shared database with strong consistency, an authenticated API mesh. The architecture in this post is not for those problems.

## The summary

Two systems can talk to each other without sharing a database, an auth provider, a message bus, or a SDK. The minimum protocol is a public manifest at a known URL describing what each side is, what it publishes, and what it accepts. The transport is static file fetches for reads and each system's existing inbox for writes. The cost is shockingly low. The friction to add or remove a peer is a single config change.

Most pairs of systems that should share data could be sharing it tomorrow with this architecture. They are not, because the default mental model for "let's integrate" is too expensive to ever start. The smaller protocol is right there, waiting to be adopted, the moment you give yourself permission to say "we'll just publish JSON and read each other's."
