---
layout: post
title: "If You Don't Own the File Format, You Don't Own the AI"
date: 2026-04-28
tags: [ai, personal-ai, data-portability, software-engineering, file-formats]
description: "If your AI lives in a vendor's database, you don't own the AI. You're renting access to a row someone else can revoke. Real personal AI requires three things you build yourself: a runtime you can replace, a portable file format that captures state, and an identity primitive that survives the runtime dying."
---

The dominant pattern for "personal AI" today is some version of the same idea: you sign up for an account, you have conversations with the model, the vendor stores them on their server. Your "personal context" is actually the vendor's database row.

This is a subscription with extra steps, not a personal AI. If the vendor sunsets the product, you lose the relationship. If you change devices, you start over. If you want to run the same persona on a laptop, a phone, and a Mac mini, you accept three subscriptions and three quietly diverging copies of "yourself." You don't own anything. You're renting access to a database row that someone else can revoke.

For an AI you want to live with for years, this is the wrong shape. The right shape requires three things you build yourself: a runtime you can run anywhere, a portable file format that captures the AI's state, and an identity primitive that survives the runtime dying.

I've been working out the specifics of this for the past year. The pattern below is what changes when you stop accepting that personal AI has to be a subscription.

## Three artifacts

Three things deserve their own names, because the pattern only works when you separate them clearly.

**The runtime.** A small process that hosts the AI. Loads agents, dispatches tool calls, manages conversation state in-memory. *Mortal.* Dies when the laptop sleeps. Resurrects on the next start.

**The state file.** A typed archive — a single zip with a manifest and a directory tree — that captures everything the AI needs to be itself: agents, memory, configuration, conversation history. Pack it on machine A. Unpack on machine B. The AI shows up intact.

**The identity primitive.** A short, stable string generated *once* on first run, embedded in every state file the runtime ever produces. Persistent across machines, across runtime versions, across years. The proof that the thing running on a borrowed laptop next year is the same thing as today.

The runtime is the console. The state file is the cartridge. The identity primitive is what proves the cartridge running on your laptop today is the same cartridge running anywhere else, ever.

These three names are doing real work. They're not metaphors. They're the column headings of a contract.

## Why the file format is load-bearing

Most people focus on the runtime. The runtime is the visible part — the chat UI, the tool calls, the model. The runtime feels like the AI.

It isn't. The runtime is interchangeable. You can replace it tomorrow with a different runtime — different model, different language, different framework — and as long as the new runtime can read the same state file, *the AI is unchanged*. The runtime is the cartridge slot. The state file is the cartridge.

This is the part vendors don't want you to internalize. If your AI is a vendor's database row, switching vendors means starting over. If your AI is a file you own, switching vendors is loading the file into a different runtime. The first situation is lock-in. The second is portability.

The single most important question for a personal AI: **can I export it as a file, and can I load that file into a different runtime that I run myself?** If the answer is no, you don't own the AI. You're renting access to it.

## What goes in the file

A state file should contain everything required to reconstitute the AI on a new machine, with no calls back to the originating environment:

1. **A typed manifest.** A small JSON file declaring the format version, the identity primitive, the runtime version it was packed by, and the contents of the archive. The manifest is the entry point.
2. **The agents.** Whatever code, prompts, or behavior definitions make up the AI. If the AI is a single agent, it's one bundle. If it's a swarm, it's a directory.
3. **The memory.** Conversation history, accumulated context, anything the AI remembers about its world. Plain markdown is fine for most of this. Complicated structures aren't necessary.
4. **The configuration.** Tool integrations, MCP servers, API keys (if you're packing for the same trust boundary; otherwise leave them out and re-pair on the destination), preferences.
5. **The data.** Any user data the AI works with. Documents, files, datasets.

Total size for most personal AIs: tens to hundreds of kilobytes. Some can be larger if they include datasets. Either way, the entire AI fits in something you can email yourself or post to a gist.

The format should be **inspectable by humans** and **parseable by tools**. A zip of a directory tree of mostly text files is fine. JSON manifests are fine. Markdown for human-readable parts is fine. Resist the temptation to invent a binary format. The AI you can `unzip` and read with `cat` is the AI you'll still be able to read in five years.

## Why the identity primitive is separate

It's tempting to say "the file *is* the identity." The path it lives at, the hash of its contents, the email it's tied to.

This breaks down quickly. The file's contents change every time the AI talks to you. The path changes when you move it between machines. The email is a vendor relationship.

The identity primitive solves this. It's a short string — a few hex characters of randomness — generated *once*, on first run, and persisted to a file the runtime owns. Every state file the runtime exports embeds this string in its manifest. Every state file the runtime imports verifies the string.

The primitive doesn't change when the AI's contents change. It doesn't change when the file moves. It doesn't depend on a vendor. It's a self-issued certificate that says "I am the AI that started running on your laptop on date X." Anyone holding the primitive can verify a state file claims to be that AI. No one without it can fake one.

This is what makes the AI *yours*, in a way that survives every external relationship.

## The four operating modes

Once you have all three artifacts — runtime, file format, identity — you can run the same AI in four very different shapes.

### Solo

One machine, one runtime, one AI. The default. Everything in one place. The AI accumulates state on this machine. Most people stop here, and that's fine.

### Parallel

Same AI, multiple runtimes, all running independently on different machines. Export the state file once on the home device. Publish it somewhere reachable — gist, GitHub release, a private URL — and import it on every other device. Each runtime accumulates its own divergent state from there.

The four runtimes don't talk to each other. They don't sync. They don't merge. Each is the same AI from your perspective — same name, same skills, same personality — but each has its own history of what it's done since you imported it. For most uses, that's enough. The AI on your work laptop has a different working memory from the AI on your home machine, but they're recognizably the same AI to you.

### Synced

Same AI, multiple runtimes, periodically merging state. You introduce a sync protocol that combines deltas from each instance. This is hard to do well — the merge logic has to handle conflicts in the AI's memory — but it's doable. The result is one AI whose memory follows you across devices.

The honest answer is most personal AI doesn't need this. Parallel is enough. The complexity of merging state across instances is rarely worth it.

### Forked

Same starting AI, intentionally divergent. You export your state once, give it to a colleague, and they run their version. Both versions evolve independently. After six months, they're recognizably the same heritage but distinct AIs. The fork is its own AI now, with its own identity primitive (or a derived one that records the lineage).

This is how you give an AI persona to someone else without compromising your own. They get the starting point; they don't get the future.

## Why this matters more every year

Two trends are converging:

**Models are getting good enough to be worth keeping.** A year ago, the AI you'd built up over six months wasn't worth much, because next year's model would be twice as good and starting from scratch was easy. That's changing. The work of building a useful personal AI — the prompts, the memory, the integrations — is starting to outweigh the model gains. Once the work outweighs the model gains, *portability of the work* matters.

**Vendor lock-in is getting more expensive.** As personal AI accumulates more of your context — your writing, your tasks, your preferences — losing it gets more painful. The cost of switching vendors goes up. Vendors know this. The pricing they're offering today reflects what they think they can charge later, when the switching cost is high.

The pattern in this post is a hedge against both trends. If your AI is a file you own, future model improvements are something you adopt by swapping runtimes — they're not lock-in events. If your AI is a file you own, vendor pricing changes are something you respond to by moving the file — they're not coercion.

## What to build, in order

If you're going to build personal AI you actually own, the order matters:

1. **Pick a state file format first.** Decide what goes in the manifest, what goes in the archive, what's portable, what's not. Make it human-readable.
2. **Build a runtime that reads and writes it.** The runtime is replaceable. The format isn't. Build the runtime to serve the format, not the other way around.
3. **Add the identity primitive on first run.** Make it a one-time generation, persisted to a file the runtime owns. Embed it in every export.
4. **Test the round trip.** Export from runtime A, import into runtime B (different machine, different version, different language ideally). Confirm everything works. If anything is missing, the format is wrong; fix it.

Skip steps 1 and 3 and you'll end up with another vendor lock-in. Do them in that order, and you have an AI that genuinely outlives whatever runtime you started with.

## The takeaway

Most "personal AI" today is rented. Your context lives in someone else's database, with someone else's identifier, accessed through someone else's session.

Real personal AI is a file you own. A runtime you can replace. An identity that's yours and only yours.

Three artifacts: runtime, file, identity. Three roles: console, cartridge, proof.

Build them in the right order. Pick a portable format. Make sure round-tripping between runtimes works. Generate the identity primitive once and never again.

After that, your AI survives vendor sunsets, device swaps, runtime upgrades, and the long arc of time. The relationship is yours. The memory is yours. The identity is yours.

That's the difference between an AI you own and an AI you're paying to access. The first one is permanent. The second one ends the day someone else decides it does.
