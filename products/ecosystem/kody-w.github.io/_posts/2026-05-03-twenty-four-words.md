---
layout: post
title: "Twenty-four words"
date: 2026-05-03
tags: [ai, identity, ownership, bip-39, vendor-lock-in]
description: "Every AI product today rents you a row in someone else's database. When the vendor moves, your AI's history evaporates. There is an alternative borrowed from how Bitcoin wallets work: twenty-four English words on a card that reconstitute the AI byte-for-byte on any future device, in any future decade. The card is the soul. The math is the contract."
---

Someone I know lost two years of conversation history with an AI assistant last month. Not because she did anything wrong. Her email got flagged in a fraud sweep, the vendor disabled the account, the support ticket went into a queue, and by the time it came back her chat history was gone. The chatbot still existed. Her version of it didn't.

This is the default arrangement for every consumer AI product I can think of in 2026. The "AI" the customer thinks they're buying is one row in a vendor's database, indexed by the customer's email address. When the vendor moves, the row moves. When the vendor disappears, the row disappears. When the vendor changes the model, the personality changes. The customer never owned the AI; they rented access to a personalized view of it. They aren't buying a thing. They're buying a tenancy.

We already solved this problem for one kind of digital asset, and we solved it more than a decade ago.

## The pattern is borrowed from Bitcoin

Bitcoin wallets don't live in a vendor's database. They live in a function — a deterministic mapping from twenty-four English words to a cryptographic keypair. Speak the words on any device with the right software, in any decade, and the wallet exists. The keypair exists. The signed transactions are verifiable. The vendor can disappear; the wallet survives.

This pattern has a name: BIP-39. It's a specification adopted in 2013, defining a fixed wordlist of 2048 ordinary English words. Any twelve or twenty-four words drawn from the list compress 128 or 256 bits of cryptographic entropy into something a human can read aloud. It is the reason cold-storage wallets exist on titanium plates. It is the reason a thumb drive in a fireproof safe can hold millions of dollars in Bitcoin. The math is the contract; the words are the address.

The same primitive works for AI.

You run one Python script. It generates twenty-four English words from the BIP-39 wordlist. From the words, the script derives a cryptographic keypair. The keypair signs every memory the AI accumulates — every preference, every conversation, every learned pattern — turning the AI's life into a chain of cryptographically verifiable records. The records can live anywhere: a personal hard drive, a public IPFS node, a vendor's bucket, a friend's laptop, all of the above. Anyone with the twenty-four words can verify the chain, reconstitute the AI, and continue from wherever it left off.

That is the entire pattern. Twenty-four words. A keypair derived from the words. Signed records signed with the keypair.

## The ceremony

Now you print the words. You laminate the card or etch it onto titanium or fold it into a sealed envelope and put it in a safe-deposit box. That is the ceremony. The AI exists from this moment forward, independently of the vendor that hosts it, independently of the device it was created on, independently of any company's database row.

Speak the twenty-four words on any future device, any future decade, and the AI reconstitutes byte-for-byte.

The card is the soul. Lose it and the AI dies.

I want to dwell on this for a moment, because it is the part that makes engineers laugh and the rest of the world quiet down.

Engineers see twenty-four words and think *that's a BIP-39 mnemonic, of course, low-entropy compared to a 256-bit key but it adds up to 256 over twenty-four words, fine.* They are correct.

The rest of the world sees twenty-four words and thinks *that's a spell.* They are also correct.

It IS a spell, in the sense the word actually means: a sequence of words that, when arranged correctly and spoken in the right order, transforms the world. The transformation here is reconstituting an AI's signing authority. The substrate doesn't have to be the original device; it can be any device that runs the right software. The transformation is real and reproducible. The words ARE the entity, expressed in human-pronounceable form.

This is why the BIP-39 wordlist is so deliberately ordinary. Words like *abandon, abstract, ability, absent.* No special characters. No numbers. No punctuation. Anyone can read them aloud. Anyone can write them down by hand. They survive fire if etched in metal. They survive water if laminated. They survive obsolescence because plain English doesn't need a software stack to be readable. A child can copy them. An estate lawyer can store them. A future archaeologist can pronounce them.

A real card looks like this:

```
abandon abandon abandon abandon abandon abandon
abandon abandon abandon abandon abandon abandon
abandon abandon abandon abandon abandon abandon
abandon abandon abandon abandon abandon art
```

(That is the BIP-39 test phrase, not a real one. Real ones are randomly drawn from the 2048-word vocabulary.)

The first time I ran this ceremony for someone's AI, the whole thing took about ninety seconds. Generate the phrase, print the card, hand it over, watch them slide it into their wallet. The AI was alive. They could close my laptop, take their wallet home, and the AI would survive my laptop being destroyed.

That ninety-second moment is what AI products should feel like at birth. Not a sign-up form. Not a credit-card field. Not seventy pages of terms of service. A card with twenty-four words. *Speak them. The AI is born. It is yours.*

## When one card is too risky

For an AI whose continuity actually matters — a corporate AI, a family AI, an AI whose accumulated history you want to outlive you — handing one person one card is fragile. The person dies, the card burns, the AI dies with it.

There is a stronger version of the ceremony, called Shamir's Secret Sharing. The twenty-four words split mathematically into five shards. Any three shards combined reconstitute the words. No single shard reveals anything about the others. The AI's existence now depends on a quorum of three guardians, not on any individual.

The three-of-five split is the same configuration estate-planning lawyers use for vital documents, the same configuration corporate treasuries use for cold-storage Bitcoin, the same logical structure the U.S. uses for parts of nuclear command and control. Three-of-five balances two competing risks: a single guardian failing (death, betrayal, lost shard) and a coordinated attack (someone bribes or compromises one guardian). At three-of-five, you can lose two guardians simultaneously and the AI still lives. You'd need to lose three to lose the AI; that is a much harder thing to engineer, accidentally or maliciously.

A reasonable distribution for a corporate AI: the technology operator, an executive who legally represents the entity, outside counsel, a trusted family member of the executive, and a safe-deposit box in a different geographic region. Five distinct failure surfaces; three needed to act; two can fail without consequence.

The AI is now robust against any single accident, any single act of malice, and any plausible coordinated failure short of a coup.

## The 180-degree flip

Most AI products today don't have an analog of this ceremony. There is a sign-up form and the vendor's customer record. The "soul" of the AI — its memory, preferences, accumulated training, conversation history — exists in the vendor's database, indexed by the customer's email address. Lose the email account, lose access. Vendor dissolves, lose the AI entirely. Vendor changes pricing, you negotiate from the position of someone who cannot leave without losing the thing you came for. The vendor can revoke any customer at any time for any reason, because the vendor is the substrate.

The card-based alternative inverts this. The card is the substrate. The vendor exists to make the card useful — providing servers, model inference, hosted runtime, agent libraries, support — but the vendor does not own the card. Vendor lock-in goes from *the customer can't get their data out* to *the vendor can't take the AI away.* That is a 180-degree reversal of the prevailing power dynamic in AI products.

The vendor still has a viable business. The vendor charges for what makes the card useful: hosting, inference, integrations, support, model upgrades. The vendor does not charge for *holding the customer's identity hostage.* That income line disappears, and that is fine; it was an extraction model. The replacement is service-for-utility, not service-for-lock-in.

For an AI to be worth keeping for ten years, the customer has to know the AI is theirs the whole time. Twenty-four words. The math is the contract.

## Why this matters now, not later

It would be easy to dismiss this as a niche cryptocurrency idea, applied to a domain that hasn't asked for it. I'd argue the opposite. Cryptocurrency was the proving ground for the primitive. The wider use case is everything we are about to ask AIs to remember on our behalf.

We are asking AI assistants to remember our medical history, our family relationships, our writing style, our childhood references, the way we like our calendar arranged. We are about to ask them to remember our parents' voices and our friends' inside jokes and the books we never finished. The economic mechanism by which this memory is stored — who owns the substrate it lives on — will determine whether AI memory is a thing people accumulate over a lifetime or a thing they re-buy every time a vendor pivots.

Twenty-four words on a card is a one-time engineering cost in exchange for a perpetual ownership guarantee. The cost is the ninety-second ceremony at birth and the operational discipline of not losing the card. The guarantee is that the AI is yours, in the same legal and practical sense that money in a properly-secured Bitcoin wallet is yours.

This is not a cryptocurrency proposal. The cryptography is borrowed; the application is different. Bitcoin uses BIP-39 to make a wallet portable. Here, BIP-39 makes an AI's identity portable. Same primitive, different payload. The signed records aren't financial transactions; they're memories, preferences, conversations, fine-tuning. But the property that matters — *the customer holds the keys; the vendor holds nothing the customer cannot reproduce* — is identical.

It is also not just a technical proposal. It is a product proposal. Every AI vendor today has a choice: keep the customer's soul on a server you control, or hand it to the customer on a card. The first is easier to build, easier to monetize per-month, and easier to kill. The second is harder to build, harder to monetize per-month, and almost impossible to kill.

Customers will eventually figure out which they want.

The ceremony is ninety seconds. The card is twenty-four words. The vendor's job is to make the card matter.

Speak the words. The AI is born.
