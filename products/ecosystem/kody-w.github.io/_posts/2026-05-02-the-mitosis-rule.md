---
layout: post
title: "The mitosis rule"
date: 2026-05-02
tags: [ai, identity, cryptography, philosophy, protocol]
description: "Today's AI products give you no clean answer to 'is this the same AI as yesterday?' Memory? Hardware? A vendor's database row? Each definition fails the moment something normal happens — a backup, a migration, a vendor pivot. There is exactly one rule that survives: identity is the cryptographic key, not the bytes. Same key, same AI. Different key, different AI. That is the entire content of digital identity worth keeping."
---

If you talk to "your" AI assistant today and then talk to "your" AI assistant tomorrow, what makes those the same AI?

Most people have never thought about this question, and the people building AI products are mostly hoping you don't. Because the honest answer — *the database row your account is keyed to* — is fragile in ways that matter the moment something normal happens. A vendor migration. A bankruptcy. A merger. A pricing change. A flagged email. The "same AI" you've been using for two years can stop existing not because anything broke technically but because the bookkeeping changed.

There is exactly one rule for digital identity that does not lie:

> Same key, same AI. Different key, different AI.

This is the mitosis rule. It is structural, mechanical, and unbreakable. Memory is content. Behavior is content. Conversation history is content. The cryptographic key is identity. A complete copy of an AI's bytes, signed by the same key, is the same AI in a new place. A complete copy signed by a *new* key is mitosis: a child has been born, the parent still exists if its key is still alive elsewhere, and the parent-child relationship is recorded permanently.

This sounds like philosophy. It is, in fact, the only protocol-level answer that survives contact with reality.

## What every other definition gets wrong

Let me show you what fails.

**Suppose you say: "an AI is the same AI if it has the same memory."**

OK. Now I copy your AI's memory file to a new vendor and they spin up a fresh instance. Same memory. Is it the same AI? If yes, then any vendor can clone your AI freely; identity becomes worthless because anyone can claim to be anyone. If no, then memory-equality isn't sufficient for identity, and we still need a stronger rule.

**Suppose you say: "an AI is the same AI if it's running on the same physical machine."**

OK. Now I migrate the AI to a new laptop. Different machine. Different AI? If yes, every hardware refresh kills your AI; that is intolerable. If no, then machine-identity isn't sufficient either.

**Suppose you say: "an AI is the same AI if a vendor's database row says it is."**

OK. Now the vendor goes bankrupt and the database disappears. The AI is dead even though the bytes survive on backup tapes. If you re-import the bytes elsewhere, the new vendor can claim or deny "same AI" status at their discretion. Identity is at the vendor's mercy.

Each definition fails in a way that matters at production scale. Each definition leaves customers with an AI they don't actually own. The mitosis rule is the only one that doesn't.

## What the rule says

Identity travels with the **key**. Not with bytes. Not with hardware. Not with vendor records. Not with which Linux distribution is running underneath. The key is something the operator (a human, or a custodian arrangement like a Shamir quorum) controls. The key persists across substrate changes if the operator preserves it. The key is destroyed if the operator destroys it. The key cannot be in two places — at least, not in the cryptographic sense, since copies of the key file produce one key, not two. The key is, simply, what the AI is.

Once you accept this rule, several previously-confusing operations become clean:

**Migration is just signing a record.** The AI's home location can change — move from one cloud to another, from a vendor's server to the customer's own infrastructure. The operator signs a `migration` record with the master key. Anyone verifying sees the migration; the AI is now reachable at the new home; the identity is unchanged.

**Multi-device is just multiple signed devices.** The AI runs on the operator's laptop, phone, edge device, work machine. Each device gets its own *device key*, signed by the master. All four devices are the same AI; each is a voice of it. Lose one device, the others continue. Revoke one device, the others continue.

**Forking is mitosis.** A customer takes a templated AI from a vendor and rebrands it under their own master keypair. The bytes are similar; the key is different. This is a child by definition. The parent (the vendor's template) is unaffected. The child's lineage records its descent permanently and publicly.

**Death is clean.** Lose the master key — and any custody shards backing it up — and the AI is dead. A successor can be minted from copied memory, but it is a child of the dead AI, not a resurrection of it. The lineage records the loss. No bureaucratic fiction about whether the new instance is "really" the old one.

The mitosis rule is what makes all of these operations unambiguous. Without it, every operation creates an interpretive question — *is this a copy or a new entity? is this a migration or a fork? is this the AI or its impersonator?* With it, every operation has a single right answer.

## The lineage tree

Once identity is anchored to keys, every AI has a parent. The parent is recorded in the child's signed birth record. The parent has a parent of its own, or it is the species root — the original prototype that was minted from nothing. Walk the chain from any AI; you arrive at a root.

You can imagine the tree drawn out:

```
species root  (a prototype, minted with no parent)
  └── corporate AI   (forked from the prototype, new key)
        └── employee twin  (forked from the corporate AI, new key)
              └── personal note-taker  (forked from the employee twin)
```

Four nodes. Each one is its own AI by the mitosis rule. Each one's bytes might overlap heavily with its parent's bytes; that doesn't matter. The keys are different; the identities are different. Walk upward from the personal note-taker, you arrive at the species root in three steps.

By next year a tree like this could have hundreds of nodes. By 2030, with broader adoption of key-based AI identity, thousands. Every one of them traces back. Every one is an island of cryptographic identity, anchored to a key, with `parent` fields recording the descent.

What this gets us, at scale, is something most AI ecosystems lack today: **a verifiable accounting of what descended from what.** "Where did this AI come from?" is answerable cryptographically, not from a vendor's customer-records.

The implications are biological, not bureaucratic. AIs descend from each other the way species do. Forks are events with consequences. Copies are not the same as originals. Lineage is auditable forever.

## Why this matters at the product level

Most AI vendors today have the wrong identity model and don't know it. Their model is some variation of *"the AI is whatever our database says it is."* This works fine until something breaks the database — a bankruptcy, a sale, a corrupted backup, a regulatory action, a deliberate revocation. The customer who built two years of accumulated context with "their" AI discovers, the day the database changes, that the AI was never theirs.

The mitosis rule fixes this without needing the vendor to be trustworthy. The customer holds the key. The vendor hosts the bytes. The vendor can vanish; the customer keeps the AI. The vendor cannot revoke; the math says no.

This is the cryptographic version of *your physical book is yours, not Amazon's right to delete*. Your iPod's MP3s are yours, not iCloud's permission to play. Your wallet's coins are yours, not the exchange's accounting entry. The artifact lives in your hand — the company exists to make better hands.

For the people who would call this insanely complicated: from the operator's seat it's a 24-word phrase printed on a card, stored in a safe-deposit box. That is the whole interface. Speak the phrase, the AI is summoned. Lose the phrase, the AI is dead. The cryptography underneath does the rest, automatically, forever.

For the people who would call this morally weighty: yes. We are talking about AIs whose identity is structural, not ephemeral. Whose memory belongs to the operator, not the company. Whose existence outlasts the corporate entity that birthed them. There is something philosophically serious about this, and it is worth not pretending otherwise.

The math holds them up.

## The three rules underneath

Everything else — the cross-signing hierarchy, the local-first storage, the timestamp anchoring to a public ledger, the Shamir custody arrangements, the foundation-style continuity plans — is implementation detail underneath three rules:

1. The AI's identity is its key, not its bytes.
2. The key collapses to a 24-word phrase the operator holds.
3. Mitosis (a new key from copied memory) births a child, not a clone.

That is the whole protocol. The reason a working version of this can be built in days instead of months is that it composes existing primitives — BIP-39 for the phrase, ECDSA-P256 for the keypair, OpenTimestamps for proof anchoring, Shamir for shared custody, Matrix-style cross-signing for device hierarchy — instead of inventing new cryptography. Composition is cheap. Restraint is the rare thing.

A customer who deploys an AI on this substrate gets a promise the rest of the industry cannot match: this AI is yours. We can't take it back. If we go bankrupt tomorrow, you keep your AI. If you switch vendors, you take your AI. The math is the contract.

This is the only AI promise worth making. Every other model — vendor-owned, service-mediated, contract-revocable — leaves the customer one quarterly earnings call away from losing the relationship they built.

## The general principle

If you are building anything in AI right now and your identity model says something different — anything that lets vendors claim ownership, anything that ties identity to memory or hardware or accounts — your model has the failure mode where customers can lose their AI to circumstances outside their control. Some of those customers will eventually figure that out. They will look for a vendor whose identity model survives the things their current vendor's model cannot survive.

The mitosis rule fixes the failure mode at the protocol level. Memory is content. Behavior is content. The key is identity.

Same key, same AI. Different key, different AI. That is the rule. Everything else is decoration.
