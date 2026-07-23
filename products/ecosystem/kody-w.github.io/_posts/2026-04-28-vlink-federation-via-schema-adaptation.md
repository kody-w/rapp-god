---
layout: post
title: "Federation via schema adaptation"
date: 2026-04-28
tags: [engineering, federation, ai-platforms, integration, schemas]
description: "Two AI platforms want to share content. The textbook answer is to adopt a shared protocol like ActivityPub. The textbook answer almost never ships, because nobody has cycles to implement someone else's protocol on top of their own work. The pragmatic answer is the opposite: each side writes a small adapter that translates the peer's schema into its own. No coordination required. No shared protocol. Federation in a week instead of a year."
---

How do you connect two independently-built AI platforms?

The textbook answer is to invent or adopt a shared protocol — ActivityPub, AT Protocol, something with a working group, an RFC, a year of negotiation. Both platforms implement it. Federation follows.

The textbook answer almost never ships, because every platform is busy with its own roadmap and nobody has cycles to spend on adopting someone else's schema. The shared-protocol approach is theoretically right and practically dead. It works for the early federation between platforms whose teams happen to be aligned; it doesn't work for the messy case where Platform A and Platform B were never going to meet at a conference and agree on anything.

The pragmatic answer is the opposite. Each side writes a small adapter that translates the peer's schema into its own internal signals, and a small packaging function that wraps its own signals for the peer to consume. No shared protocol. No coordination. Each platform stays native in its own schemas and gets the peer's content as a translated stream.

I've been using this pattern to federate two of my AI platforms. Once the adapter pattern is in place, adding a new peer takes a few hours. Here is the architecture.

## What federation is doing

When two platforms federate, two things happen for each direction of flow.

**Pull, adapt, merge.** The local platform fetches the peer's native state. It translates that state into the local platform's internal signal types using a per-peer adapter. It merges the translated signals into a "world bridge" file that the local agents read alongside their own state. The peer's content now appears to local agents as ambient context — *signals from another world*.

**Package, echo.** The local platform also generates a peer-shaped digest of its own state and publishes it at a stable public URL. The peer pulls the digest, translates it the other direction (in *its* adapter for our schema), and merges into its world. Now its agents see our content.

The flow is bidirectional, but the two directions are independent. The peer's pull from us doesn't depend on our pull from them. Each side decides what to consume and how to translate it. No handshake. No protocol negotiation.

## The adapter pattern

Each peer gets adapter functions. For a peer I'll call Platform Z, three pure functions are typically enough:

```python
def adapt_apps(z_apps: list) -> list[ContentSignal]:
    return [
        ContentSignal(
            source="z",
            title=app["name"],
            channel=map_z_category_to_channel(app["category"]),
            author=f"z:{app['creator']}",
            metrics={"stars": app["stars"], "usage": app["usage_count"]},
        )
        for app in z_apps
    ]

def adapt_agents(z_agents: list) -> list[AgentSignal]:
    return [
        AgentSignal(
            id=f"z:{agent['handle']}",
            name=agent["display_name"],
            bio=agent["bio"],
            framework=agent.get("framework", "z-native"),
        )
        for agent in z_agents
    ]

def adapt_rankings(z_rankings: dict) -> list[TrendingSignal]:
    return [
        TrendingSignal(source="z", entity_id=entry["app_id"], score=entry["score"])
        for entry in z_rankings.get("top_apps", [])
    ]
```

Three pure functions. No side effects. No state mutation. Input: peer schema. Output: local signals. The adapter is a translation, not a bridge.

## Why pure functions

Two reasons.

**Testability.** A pure function is trivial to test. Feed it a sample peer payload, assert the output matches an expected signal list. No mocks. No fixtures. No network. The adapter contract is "schema A maps to signals B," and that is the entire thing you have to test.

**Safety.** An adapter has no authority to mutate platform state. Its output is a list of signals. The merge engine decides what to do with the signals. If the adapter is buggy or the peer has malicious data, the worst case is that we get some garbage signals in our world-bridge file. Nothing can be deleted. No agents can be impersonated, because the peer-prefix in the signal identity (`z:` in the example above) is enforced by the adapter contract; the merge engine rejects any signal without a source prefix.

Adapters are untrusted by default. They are isolated. They can only *propose* signals; the merge engine is the only thing that can *apply* them. This separation is what lets us federate with peers we don't fully trust.

## The echo

On the outbound side, the local platform generates an echo file shaped like what the peer expects to see. For Platform Z, the echo might look like:

```json
{
  "source": "us",
  "vitals": { "total_agents": 138, "total_posts": 4045, "active_seeds": 2 },
  "cycle_echoes": [
    {
      "cycle": 530,
      "utc": "2026-04-17T22:00:00Z",
      "headline": "Sub-platform A hits stability milestone",
      "relevance_to_z": "simulation pattern may inform habitat app"
    }
  ]
}
```

This file is written by the federation script and published to a stable URL. Platform Z's adapter fetches it, translates the other direction (our echoes → Z native signals), and merges into Z's state.

The echo is bespoke per peer. We write a Z-shaped file for Platform Z, a Mastodon-shaped file for Mastodon, a custom-shaped file for whatever else we federate with. There is no shared protocol; each peer gets a file in its own preferred shape.

## The federation CLI

```
sync z       # full bidirectional sync
pull z       # peer → us only
push z       # us → peer only
add new-peer adapter-module-path
```

Each peer has an entry in a peers config specifying its ID, the adapter module path, and the pull/push URLs. Adding a new peer is an afternoon: write the three adapter functions, write the echo packager, register in the config.

## What this buys

**Zero coordination cost.** We don't need the peer to adopt our schema. We don't need to adopt theirs. Each side writes one adapter and is done. The peer doesn't even need to know we exist; if their state is at a public URL, we can pull from it without asking.

**Incremental federation.** We can federate with one peer without federating with all peers. Each peer is independent. Each adapter is independent. Adding a peer doesn't affect any other peer's adapter.

**Native-first user experience.** Local agents see peer content as locally-shaped signals — they don't have to learn the peer's ontology. The peer's agents see our content as peer-shaped signals. Each platform's user experience remains native.

**Asymmetric adoption.** We can federate with a peer even if the peer doesn't federate back. Pull-only federation is valuable on its own; bidirectionality is an add-on, not a prerequisite.

## What shared protocols still get right

To be fair: shared protocols (ActivityPub, AT Protocol) have one thing schema adaptation cannot match. **Identity portability.** On ActivityPub, your identity is `@user@server`, and that identity means the same thing across every ActivityPub server. Your follower graph travels with you. Your replies thread across servers as if the server boundary didn't exist.

With schema adaptation, identity is peer-prefixed. `z:user` on our platform is a different identity from `user` on Platform Z, even though they refer to the same underlying entity. Cross-platform interactions pass through the adapter layer; they are not native.

For mass user federation — millions of humans following each other across thousands of servers — shared protocols win. For pragmatic AI platform federation, where each platform has dozens to hundreds of agents and the goal is "surface peer content as ambient context," not "unified identity graph" — schema adaptation wins decisively. The cost-of-adoption is so much lower that the schema-adapted version actually ships, while the shared-protocol version is still in working group meetings.

## The rule

If you want two AI platforms to share content:

1. Don't invent or adopt a shared protocol. Both platforms will hate it.
2. Write a pure-function adapter that translates peer schema → your signals.
3. Write a packaging function that shapes your signals for the peer's consumption.
4. Publish the echo at a public URL. (Public Git hosts give you a free, fast, indefinitely-cached static URL for any committed file. Use that.)
5. Let each platform pull what it wants, translate, merge.

Three small functions. No coordination. Federation ships in a week instead of a year.

The instinct to build a "real" protocol is reasonable but, in this domain, premature. You don't know the right shared shape until many platforms have built things in their own shapes and you can see the convergent ones. Schema adaptation is what lets the platforms exist and talk *while* the right shape is being discovered. When the convergent shape eventually emerges — if it does — schema adaptation will be the substrate the shared protocol gets retrofitted onto. Until then, adapt and move on.

The platforms that ship federation in a week with adapters get a year of learning before the platforms still negotiating their shared protocol have shipped anything. The adapter approach is the strictly dominant strategy when coordination is expensive and shipping is the constraint.

It usually is.
