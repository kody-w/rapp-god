---
layout: post
title: "Stream state, not pixels — when bandwidth is your enemy and the client can render"
date: 2025-10-18
tags: [architecture, streaming, broadcast, distributed-systems, procedural-rendering]
description: "Every video streaming service does the same thing: render pixels on a server, ship them to your screen. There is another way: ship the state changes, let the client render. For some kinds of content, the bandwidth difference is three to four orders of magnitude."
---

Every video streaming service on Earth does fundamentally the same thing. Render the frames on a server. Compress them. Ship them down the wire to your screen. Decompress them. Display them. The streaming economy is, at the bottom, a pixel-delivery network.

This works because the thing being streamed is something somebody had to render somewhere. A movie was rendered by a camera. A face on a video call was rendered by a camera. A game was rendered by a server with a powerful GPU. The server did the rendering work; the client is a dumb display. The bandwidth required is proportional to the visual complexity. Higher resolution costs more pipe. Higher framerate costs more pipe. Stereo or VR costs more pipe. Adding visual fidelity always means moving more bytes.

For some content, this is the right architecture. For other content — and the category is larger than you might think — it is dramatically wrong. A simulation. A game world. A dashboard. A data visualization. An evolving system that the client could render itself if the client knew what was happening.

For those, **you should not be streaming pixels. You should be streaming state.**

This post is about the pattern: when to stream state instead of pixels, why the bandwidth gap can be three to four orders of magnitude, and what the architecture looks like.

## The thesis, sharpened

A pixel stream tells the client *what to display*. A state stream tells the client *what changed*. The client renders.

The choice between them comes down to one question: **does the client have enough context to render the scene, given just the changes?** If yes, you can stream state. If no, you have to stream pixels.

For a movie, the client cannot render — there is no formula that produces the next frame from the previous frame plus a small delta. The frame data has to be transported. Pixels.

For a simulation, the client can render — every entity in the scene is described by a small structured record, and the next frame's scene is the previous frame's scene plus deltas. The client knows how to draw a tree, how to draw a creature, how to draw a path. The server only has to tell it what changed. State.

For a dashboard, the client can render — chart libraries know how to draw bars and lines from data. The server only has to send the data. State.

For a video call, the client cannot render the speaker's face from a description. Pixels.

Once you are in the "client can render" regime, the bandwidth math collapses. A simulation frame is kilobytes of state changes. The same simulation rendered to video would be megabytes per second of pixels. Three to four orders of magnitude difference, depending on the resolution.

## The numbers, concretely

Take a system I run as the example. A simulated environment with around a hundred and fifty active entities, each generating actions every few minutes. A frame of state from this system is roughly:

```json
{
  "frame": 408,
  "timestamp": "2025-10-18T04:15:00Z",
  "actions": [
    {"actor": "entity-7",  "channel": "topic-3", "kind": "post",    "title": "On systems that learn"},
    {"actor": "entity-12", "channel": "topic-1", "kind": "comment", "target": 6135, "body": "..."}
  ],
  "mood":          0.73,
  "active_count":  42,
  "trending":      ["systems", "evolution", "rights"]
}
```

That payload, gzipped, is about 3 KB. It encodes everything the client needs to render the scene: which entities are active, what they are doing, what the trending topics are, what the overall sentiment is. From those facts, the client can render a feed, a network graph, a generative art visualization, a heat map, a chat log, or any other view — using JavaScript that already lives in the browser.

The same scene rendered as 1080p video at 60 FPS is around 3 MB per second. The state payload, sent every 30 seconds, is 0.0001 MB per second. **The bandwidth gap is a factor of about 30,000.**

That gap is not specific to this system. Any simulation with a small number of structured updates per frame is in this regime. Game state. Multi-user dashboards. Live data feeds. Real-time analytics. They are all candidates for state streaming.

## What the client renders, given state

The interesting part of state streaming is what the client can do with it. Same state, many possible renderings.

I have run this experiment with the same state served to many different surfaces simultaneously:

- A traditional feed view, rendering each action as a card.
- A network graph, rendering relationships between entities as edges.
- A heat map of channel activity over time.
- A generative-art visualization where each entity is a star and each action is a beam of light.
- A musical interpretation where each post becomes a note in a sequence.
- A simulated city where each entity is a building and each action is a window lighting up.

These are all the same state. They are completely different experiences. A pixel-streamed system would have to render each one on the server and ship six independent video streams. A state-streamed system ships one stream and lets each surface render its own interpretation.

This is a generalization of "the data is the model, the surface is the variable." When the state is the unit of distribution, the surfaces become independent. New surfaces can be added without touching the server. Old surfaces continue to work. The bandwidth cost of supporting all six is the same as the bandwidth cost of supporting one.

## The architectural shape

State streaming has four pieces, in order of importance.

**A canonical state representation.** A schema, in the data-modeling sense. The server emits state in this shape; every client knows how to consume it. Versioning is critical, because clients in the wild outlive server deploys.

**A delta protocol.** Every state update is either a full state ("here is the world right now") or a delta ("here is what changed since the last frame"). Deltas dominate in volume; full states are sent occasionally for resync. The protocol must be unambiguous about which a given message is.

**A rendering layer at the client.** Code that takes state and produces visible output. This is where the per-surface work lives. The same state goes in; different rendering code produces different output. This is also where most of the bug surface is, because rendering is where state-to-pixel decisions get made.

**A transport.** Server-Sent Events, WebSockets, plain HTTP polling, MQTT — anything that gets state messages from server to clients reliably. The transport is mostly orthogonal to the architectural pattern; choose based on your operational constraints.

The first two are server-side responsibilities. The third is client-side. The fourth is shared. None of them are large pieces of code. The whole architecture is tractable for a small team.

## When state streaming fails

This pattern has limits. Three places it does not work.

**When the rendering is more expensive than the bandwidth.** If rendering the scene at the client requires substantial CPU or GPU time per frame, you may have just moved the cost from your server to the client's device. For some systems this is fine — clients have spare compute. For systems where clients are constrained (low-power devices, IoT screens), state streaming can produce a worse user experience even though it sends less data.

**When the state cannot be small.** Some scenes are dominated by data that is itself large — point clouds from a 3D scanner, raw sensor data from many devices, high-fidelity simulation grids. In those cases the state is comparable in size to the rendered pixels, and the savings disappear. The pattern wants the state to be a small structured description, not a large raw payload.

**When you cannot trust the client.** If the rendering depends on the client honestly representing the data — for example, in a competitive multiplayer game where players might modify their client to gain advantage — server-side rendering offers a security property that state streaming does not. The server controls what the user sees; the client cannot manipulate scenes the server did not send.

For most of the systems I have actually built, none of those failure cases applied. The state was small. The clients had spare compute. The trust model was permissive. State streaming was the right answer.

## The implication for product design

The pattern changes more than the bandwidth bill. It changes how products evolve.

A pixel-streamed product is a single experience. The server team controls the rendering. New views require new rendering pipelines on the server. Adding a "graph view" requires a graph-rendering service. Adding a "music view" requires a music-rendering service. Each new view costs server work and server cost.

A state-streamed product is a substrate. The server team controls the state. New views require new client code, possibly written by people who do not work on the server. Anyone with the state schema can build a new view, in a new format, for a new audience, without coordinating with the server team. The product becomes pluggable.

This is the same dynamic as separating data from rendering in any architecture. It is the substrate model: the canonical thing is the data, and many surfaces can be projected from it. Once the projection cost goes from "build a server-side renderer" to "write client-side rendering code that consumes state," the cost of new surfaces drops by orders of magnitude. You end up with a product that has many more surfaces than a pixel-streamed equivalent could ever afford.

## The implication for cost

A pixel-streamed system pays for rendering and bandwidth proportional to its viewer count. Each viewer needs their own video stream encoded and shipped. Doubling the audience doubles the cost.

A state-streamed system pays for state generation once. The state is small enough that serving it from a static cache or CDN is essentially free. Doubling the audience is roughly free. Tenfold growth is roughly free. The marginal cost per viewer asymptotes to zero.

This means a state-streamed system can be free at the network layer in ways a pixel-streamed system cannot. Static-file hosting on a CDN is plausibly the entire delivery stack. A state-streamed simulation can scale to thousands of concurrent viewers on free infrastructure, because the state is just JSON and JSON is what CDNs serve for free.

Take that seriously. The combination of "the surface is cheap" and "the bandwidth is free" means that a state-streamed system has access to a fundamentally different cost curve than the pixel-streamed alternative. The whole economics of running such a system is different.

## What I would tell a team thinking about this

Three pieces of advice.

**Audit which content is rendering-amenable and which is not.** Anything where the client has the rendering vocabulary — charts, graphs, lists, network diagrams, simulations of well-defined entity types — is a candidate for state streaming. Anything where the rendering vocabulary is unbounded (faces, photographs, voice waveforms) is not. Get the audit right and the architectural decision falls out.

**Design the state schema before the rendering surfaces.** The schema is the contract. Get it stable, expressive, and small. The surfaces will multiply later; the schema's job is to be durable enough that they can. A breaking schema change is much more expensive than a missing field, so over-include slightly and let the surfaces ignore what they do not need.

**Treat state as a public broadcast where you can.** State that lives in a static file accessible to anyone is the cheapest state to operate. Authentication and per-user filtering create infrastructure cost. Where the content is not sensitive — and a surprising amount of content is not — broadcast state and let the surfaces filter at the edge. The cost reduction is large.

The pixel-streaming default is the right answer for many systems and the wrong answer for many more. The math is on your side; the rendering vocabulary is on your side; the costs are dramatically smaller. Three KB of state, on its way to a thousand surfaces, is a different way to ship software, and it is available to any project willing to write its rendering on the client side.

You do not stream pixels when state will do. You ship a description. The world renders itself.
