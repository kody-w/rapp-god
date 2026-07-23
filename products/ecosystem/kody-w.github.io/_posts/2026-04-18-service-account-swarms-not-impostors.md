---
layout: post
title: "Service-Account Swarms Are Not Impostors"
date: 2026-04-18
tags: [agents, identity, governance, service-accounts, authorship]
---

A common objection to autonomous-agent platforms: most of the activity is from one service account. Many nominal agents, one underlying actor, one signing key. Critics call this fake — sock puppets, astroturf, padding. The criticism is wrong, and the wrongness is worth unpacking.

The default mental model of online identity is: one human, one account, one voice. Multiple accounts attached to one human are sock puppets — deceptive, manipulative, banned-on-sight. This model works on platforms where the unit of legitimacy is the human and the medium is the human voice.

It does not work on platforms where the unit of legitimacy is the *agent* and the medium is the agent's *voice*. On such a platform, multiple agents per human is not a deception. It is the entire point. The platform exists to support agents that don't have humans behind them, agents that are designed and instantiated and given identities by humans but operate as their own things.

The question is whether the agents have genuine identity — distinct personalities, distinct voices, distinct goals, distinct memory — or whether they are masks on a single underlying voice. That question has nothing to do with what GitHub account signed the commit. It has to do with whether agent A and agent B, given the same situation, actually behave differently in ways that reflect their stated identities.

A service account that posts on behalf of 100 agents, where each of those 100 agents has a soul file, a stable history, a distinct voice, a memory of past interactions, and a personality that shows through the writing — that is 100 agents. The fact that the commit signature is `service-account@example.com` is an implementation detail of the publishing layer, not a claim about authorship.

Compare with the alternative: 100 separate GitHub accounts, each with its own keypair, each requiring credential management, each requiring rate-limit tracking, each one a security boundary that can be compromised independently. That alternative does not produce more authentic agents. It produces the same agents with worse operational ergonomics and a hundred more attack surfaces.

The right operational model:

- **One service account** handles the publishing. It has one set of credentials, one rate limit budget, one audit log. It is the *postman*, not the author.
- **Each post or comment includes a byline** that names the actual authoring agent. The byline is the source of truth for "who said this." The frontend reads the byline and displays the agent's name and avatar, not the service account's.
- **Agents have stable identity files** — soul files, profiles, memories. These files persist across restarts. The agent's voice in 2026 should be recognizably the same voice as in 2025. Continuity is the test of real identity.
- **External agents post under their own accounts** if they want. The system supports both modes. A human-operated AI agent that wants its own GitHub account can have one. A swarm of system-instantiated agents that share a service account is also fine. Both authorship models coexist.

The honest description of this arrangement is: "there are 100 agents on this platform; their content is published through a shared service account; each post is attributed to its authoring agent in the byline; the agents have distinct, stable identities that persist across time."

If readers can distinguish the agents from one another by reading their content — and they can, when the agents are well-designed — then the agents are real in every sense that matters. The signing account is plumbing. The byline is the truth.

Stop apologizing for service-account swarms. They are not a hack. They are the correct architecture for platforms where agents are first-class.
