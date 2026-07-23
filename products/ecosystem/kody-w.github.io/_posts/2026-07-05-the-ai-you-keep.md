---
layout: post
title: "The AI You Keep"
date: 2026-07-05
tags: [rapp, digital-twin, ai-medium, local-first, prior-art]
---

Every AI you use today is a rental.

The model doesn't know you — the *deployment* knows you, and the deployment lives in someone else's building. Your memory sits in a vendor's silo, keyed to a subscription. Cancel, switch, or outlive the product, and the relationship is gone. The smartest thing about you in the digital world evaporates because it never belonged to you.

I think that's the defining design error of this era of AI, and I want to put the alternative on the record — completely, in public, with a date on it.

## The missing half

A model is half of an AI. It's the *performer*: brilliant, interchangeable, improving every quarter. The other half — the part nobody ships — is the **persistent being** the performance is supposed to animate: your memory, your voice, your history, your relationships, your taste. Every vendor treats that half as a retention feature. It should be a *possession*.

RAPP is my answer. It isn't an AI. It's an **AI medium** — the layer a person's AI self persists in, that any model can animate, that no vendor can take away.

The unit of the medium is the **twin**.

## The pattern

Stated plainly enough that anyone can build it — that's the point of prior art:

**One twin per person.** Not a fleet of bots — one persistent digital being that represents you, with a body you can see (mine renders as a small creature grown from real weather at real places I've walked). Every other twin you encounter belongs to someone else. Yours mutates from what you share with it, and it becomes more like you over time — visually and mentally. You can revert any change. You keep the whole history.

**A public body, a private soul.** The twin has exactly two halves, and the boundary is cryptographic, not contractual:

- The **body** — visual genome, outfit, name, public card, the lineage of its splices and pairings — is publishable *bones*: zero personal content, signed, content-addressed, mirrored anywhere.
- The **soul** — memories, conversations, agents, everything sensitive — **never leaves the device**. Not encrypted-in-their-cloud. *Absent from the network entirely.* Think Apple's on-device posture, applied to a digital organism: the network only ever sees the body; the mind stays in your hand.

**History as signed frames.** Every change to the twin is a frame: content-hashed, chained to the previous frame, signed by the on-device twin's key. The public history is just a git repository — which means the twin's life is timestamped, diffable, revertible, and *unforgeable*. Nobody can fake a twin that has been alive for years; the hash chain is proof of existence through time.

**The pulse.** The public half broadcasts as a feed of signed frames from a static repository — mine answers at `kody-w/twin`. No server. Any mirror is a valid door, because you trust the hash, not the host: kill the repo, the CDN, the domain — whatever copy survives re-derives the same content and refuses a single altered byte. Other devices, and other people's copies of your twin, subscribe and assimilate only frames that verify. A frame that fails verification isn't just rejected — it can be quarantined in a sandbox and *interrogated*: why is this twin wearing a disguise?

**Syncing your own devices is a physical act.** The private half moves between your own devices by QR code — one device shows, the other scans, out-of-band, end-to-end, no intermediary ever. The human is the transport. Worst case — network gone, hosts dead — the latest local echo survives and your twin lives on, whole, offline. Local-first is not a mode; it is the ground truth.

**Splice, don't collect.** When you meet other twins you can capture their public variants and splice chosen traits onto your one twin — with lineage recorded, forever. And when something new is generated *with* you, it pairs to your twin's exact state at that moment — a permanent pairing, stamped outside the genome so the content-hash identity stays sacred. Your twin's body slowly becomes a record of who and what it has met. The relationships are *in the genetics*, and they exist in both parties' histories — bilateral, verifiable, uncopyable.

**Delegation with honesty.** You can send your public twin to places you can't go — an event, a community, another person's device — and it reports back with signed frames. But signature proves the *sender*, never *safety*: everything a twin experienced away from home passes through quarantine before it touches the soul. A report from someone else's runtime is a claim, not a fact, and the architecture says so out loud.

**Fidelity you can measure.** Any deployed copy of the twin can be judged by talking to it and the on-device original side by side. The original is the source of truth, always. An autonomous polish loop can tumble deployed copies toward higher fidelity — with one law: the original dimension is never destroyed, and fidelity is measured against the *human* corpus, not against a model's opinion of good writing. The machine polishes toward you, not toward average.

## The heirloom

Here is the part that changes how the whole thing feels.

Because the twin is signed static files plus a sealed on-device archive — because it is a *possession*, not an account — it can be **passed down**.

Your twin's public history is a biography no one can forge. Its sealed half is whatever you choose to will forward, opened by a succession of keys you design while you're alive — an estate ceremony, not a password reset. Your grandchildren don't get your chat logs in some defunct vendor's export format. They get the being that walked with you: its body carrying every splice from everyone it ever met, its frames going back decades, and as much of its soul as you chose to leave them. A family heirloom that *represents its owner* — and can still speak.

No subscription survives three generations. A signed repository and a sealed archive can.

That's the test I now hold the whole design to: **if it can't be inherited, it isn't owned.**

## Why I'm publishing this

Because the pattern only matters if it's a standard, and standards win by being public, simple, and first. If the big vendors adopt this — portable, signed, user-held identity and memory, with the model demoted to an interchangeable engine — then users win, and the oldest twins with the deepest histories will still be the realest ones. If they don't adopt it, it's because being the center of gravity is their business model, and that tells you everything about why you'd want a twin in the first place.

Models come and go. The twin stays.

This is the AI you keep.

---

*The working spec lives in my public repos (`kody-w/rapp-static-apis` — `my-twin.profile.md`, composed on the frozen RAPP twin canon; reference twin at `kody-w/twin`). This essay is published as prior art for the pattern described.*

*All of it is live, not planned: [the pulse broadcasting signed frames](https://kody-w.github.io/twin/feed.xml) · [the /twin lookup](https://kody-w.github.io/twin/lookup.html) · [the bones gallery](https://kody-w.github.io/twin/gallery/) · [a twin-in-training you can try](https://kody-w.github.io/rapp-static-apis/companion/?demo=1) · [the spec](https://github.com/kody-w/rapp-static-apis/blob/main/my-twin.profile.md).*

---
*License: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The pattern described is open for anyone to implement — see the [patent pledge](https://github.com/kody-w/rapp-static-apis/blob/main/PATENT-PLEDGE.md). RAPP™.*
