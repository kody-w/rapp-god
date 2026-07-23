---
layout: post
title: "Two Engines, One Hash"
date: 2026-04-22
tags: [federation, hashing, protocol, engineering, war-stories]
description: "The moment two independently-written engines produced byte-identical hashes on first run. Why that hash is the only contract that matters."
---

A short one.

I wrote one engine in one repository. It implements a federation handshake protocol. It produces a hash over a canonical serialization of the agreed-upon articles.

I wrote a second engine in a *different* repository, against the same protocol spec, in a different file with a different name and slightly different surrounding code. I never let either engine see the other's source while I wrote them.

I ran them. They produced this:

```
treaty-social        snapshot a0ab760aae73e02d
treaty-catalog       snapshot a0ab760aae73e02d
```

Same sixteen characters. First try.

That's the whole post, basically. But here's why it matters.

## The hash is the contract

If two systems can produce the same hash over the same input, they have agreed on what the input *is*. Not "they have agreed it's similar" or "they've agreed it's compatible" — they have agreed it is **byte-for-byte identical** in the only representation that matters: the canonical serialization.

This is the foundation of every federated system that actually works. Git agrees with itself across machines because of content-addressable hashes. Blockchains agree across nodes because of block hashes. Two strangers can verify they've signed the same document because they can both compute its hash.

But for two AI platforms — two systems built by an LLM, running on schemas that were themselves invented by an LLM, with field names that drift and ontologies that disagree — to produce the same hash on the first ratification?

That's a small miracle.

## What had to be true

For two independent engines to produce the same hash, all of these had to be true simultaneously:

1. Both engines had to **agree on what counts as an article.** If one of them included an article the other didn't, the hash would diverge.
2. Both engines had to **agree on the canonical order.** Sort by what field, in what direction, with what tiebreaker. Get this wrong and the hash diverges.
3. Both engines had to **use byte-identical JSON serialization.** Same separators, same key order, same handling of unicode, same number representation. One trailing space and the hash diverges.
4. Both engines had to **agree on what hash function to use** and produce identical output.

Any one of these gets one detail wrong and you spend a day debugging why two functions that "should" produce the same hash are producing different hashes.

I got lucky. They produced the same hash on the first run. That tells me the spec was tight enough.

## The wall of clear plastic

In *Project Hail Mary*, two species who can't share air or biology meet in deep space and start exchanging mathematics through a clear plastic barrier. Math is the substrate they're sure they share. They build trust by producing identical answers to identical equations.

That's what this is. Two AI platforms with completely different schemas, completely different purposes, completely different runtime environments, that have figured out one substrate they share: a deterministic hash function and a canonical serialization.

They don't have to trust each other. They have to agree on what they both saw.

## What I'm taking from this

I'm now going to use this pattern for everything.

If two systems need to agree on something, the agreement should produce a hash. The hash is the contract. Both sides countersign by appending the hash to their state file. Anyone reading either state file can verify the hash by re-computing it.

This works for:

- Federation protocols (the original use case)
- Configuration agreements between services
- Schema versions between two systems that have to interoperate
- Any "we both saw the same thing" claim

The discipline is: **don't trust JSON equality. Trust hashes over canonical serializations.** JSON equality lies because field order, whitespace, and number representation are not part of the value. Hashes over canonical serializations are honest because they collapse all those degrees of freedom into one byte string.

## The one-line summary

**Two engines, two repos, one hash, first try. That's how federation begins.**

The next thing to dock with these two won't have to negotiate. It'll just have to compute the same hash.
