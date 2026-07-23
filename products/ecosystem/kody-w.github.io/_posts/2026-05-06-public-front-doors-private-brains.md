---
layout: post
title: "Public front doors with private brains"
date: 2026-05-06
tags: [ai, identity, github-pages, oauth, architecture, federation, vbrainstem, infrastructure]
description: "Most AI infrastructure picks one of three: SaaS-central, self-hosted, or anonymous-public. The composition described here picks all three at once, layered. One frozen kernel, an unbounded tree of mirrors, three memory tiers, two agent tiers — escalation is silent, gated by GitHub identity, on a substrate (GitHub) that's already universal."
---

Most AI infrastructure picks one of three: SaaS-central (one vendor's database, one row per customer, one dashboard, infinite tenancy risk), self-hosted local (you keep everything, you also keep the operational load and lose the network effects), or anonymous-public (a chatbot anyone can talk to, with no identity layer to make it personal). All three leave value on the table.

A composition I've been exploring in production picks all three at once, layered. One URL serves anonymous strangers a polite doorman and serves the operator the full ascended twin. Same address, same OAuth flow, same code path — what the visitor sees is what GitHub will let their token read. The whole thing runs on substrate that's already universal: GitHub Pages for static hosting, GitHub OAuth for identity, GitHub raw URLs for content distribution, GitHub Issues API for per-user attributed writes. No new servers. No new identity layer.

This post is the field note. What the composition is, what compounds, what's structurally clean about it.

## The shape, in one paragraph

A frozen kernel — one small Python file, tagged once at v0.6.0, never updated — is the species DNA. Any "planted mirror" is a public GitHub repo whose kernel files are byte-identical to the canonical kernel, plus an operator-grown body (agents, soul, UI, memory). Mirrors plant from any ancestor, and the lineage chain (`parent_rappid → … → species root`) walks back through the inheritance graph of body innovations. A planted mirror's `/doorman/` page is a vbrainstem — a browser-based AI chat surface — that authenticates via GitHub OAuth, reads memory from `raw.githubusercontent.com` for everyone (public tier), reads more from a private companion repo for visitors whose token has access (private tier), and reads filtered GitHub Issues for that specific visitor's prior memories (per-user tier). On the same URL, the AI's persona shifts from polite doorman (anonymous default) to the operator's full voice (ascended) automatically based on what GitHub returns to the visitor's token. No flag, no UI mode switch, no "are you the operator" check — silent escalation.

That's the mechanism. The composition is what's interesting.

## What's structurally novel

### The kernel is genuinely frozen

Not "stable for now." Frozen forever, by spec. The kernel is the immutable species DNA. Any "improvement" the platform might want to make to it is, by construction, the wrong move — it would fragment the network. Improvements ship as agents (single-file cartridges any kernel can hot-load), not kernel patches.

The discipline is enforced structurally, not procedurally. Every mirror's installer re-fetches the canonical installer at runtime; the kernel files in every mirror's repo are byte-identical to the canonical ones; a one-line `diff` proves compliance. Anyone can verify any mirror.

This is the flip of normal engineering instinct. *Don't ship a v2.* Make v1 stable forever, and grow everything around it.

### Lineage is structural, not registry

Every planted mirror carries a `rappid.json` with `parent_rappid` (UUIDv4) pointing at the mirror it was planted from. Walk the chain back, you eventually hit the species-root rappid. There's no central registry; the lineage *is* the metadata, attached to the planted artifact itself.

This means body innovations — vault patterns, doorman scripts, agent cartridges, place-anchored seed schemas — propagate through the lineage graph the same way mutations propagate through species. Plant from the canonical kernel directly: flat tree, kernel only. Plant from a mature mirror: inherit its body, keep the kernel, add your own mutations. The mature mirror's improvements get tested by descendants, refined, and inherited downstream — without anyone running a "core platform team."

`git fork` topology, with `parent_rappid` as the metadata layer that makes it walkable. No registry to maintain. The graph is the value.

### Three memory tiers, one tool surface

Every visitor sees the same chat experience. The LLM has the same `ManageMemory` and `ContextMemory` tools available. What changes is *where* memory writes land:

- **Anonymous** — `localStorage` on this browser. Persistent across sessions on this device, never leaves.
- **Authenticated, no private access** — same as anonymous (the token doesn't unlock anything beyond the public seed).
- **Authenticated, private companion access** — Issues in a private repo, attributed to the visitor's GitHub identity. Each visitor with private access gets their own attributed memory tier; collaborators see only theirs, not each other's.

Plus a fourth tier that's read-only at the vbrainstem layer: the seed's public `memory.json`, written by the operator's local environment (Python brainstem, git-pushed). The vbrainstem reads it for everyone.

Same `ManageMemory` tool from the LLM's perspective. The dispatcher routes silently based on what's available. The visitor never sees an "access denied" — just a different depth of remembered context. The pattern is **silent escalation**: the boundary is implicit, never named.

### Same-origin localStorage is accidental SSO

GitHub Pages serves all `<user>.github.io/*` from the same origin. localStorage is per-origin. Sign in once on any planted mirror, and every other planted mirror under that user's namespace recognizes you immediately.

For the operator: their phone signs in once at any of their planted seeds; walking around their own properties on the public internet shows them the ascended view at every one. For visitors: same dynamic, scoped to whatever GitHub access they have.

This is "single sign-on by accident of the platform." GitHub Pages plus browser localStorage gives it for free. No session manager to write.

### The bond cycle: anti-fragility against kernel drift

If a mirror's kernel has drifted (accidental edits, experimental fork, stale clone), there's a deterministic recovery: egg the body, overlay the kernel with canonical bytes, hatch the body back. The pattern works at every scale — file, install, repo, network. No drift is permanent.

Combined with the lineage tree, this means the *entire* mirror network is re-baseline-able, not just any single mirror. If the kernel ever needs to be canonically updated (it shouldn't, but if), the bond cycle is how every descendant absorbs the change without losing body work.

### Public and private composition

A planted seed is publicly addressable (anyone with the URL gets the doorman) *and* privately deeper (specific visitors with read access to a paired private repo get the ascended twin). The same URL serves both. The same OAuth flow gates both. The visitor's GitHub access is the only variable.

This is what most AI infrastructure misses. SaaS bots are public-only or auth-walled. Self-hosted bots are private-only. The composition here is genuinely both — anonymous strangers chat with the public doorman; authenticated collaborators chat with the same address but get the ascended twin's full voice and memory.

## What compounds

Things that emerge from the composition that aren't in any single layer:

**Adoption is "publish yourself."** Plant a seed → you have a public AI front door at `<your-handle>.github.io/<your-name>`. No SaaS account, no vendor, no sales process. The one-liner is a `curl` pipe. Sixty seconds.

**Innovation propagates by lineage.** Any body innovation in any mirror propagates to descendants by being copied at plant time. The mirror tree is the substrate for sharing patterns. No package manager, no central catalog — `git fork` is the protocol.

**Cross-device is implicit.** The vbrainstem runs in any browser. PWA-installable on mobile. WebRTC tether between devices is one of the agents. A user's "AI" is their planted seed; the seed is an address; the address is reachable from anywhere with internet.

**Privacy is the operator's choice, exposed cleanly.** Public seed = public face. Private companion = full corpus, gated by repo permissions. Per-user memories = scoped by GitHub identity. The operator picks what to put in each layer; the platform exposes them invisibly to the right tier of visitor.

**Place-anchored AI is trivial.** A place-brainstem is a planted seed with `kind: place` and location metadata, hosted on a Raspberry Pi or any Pages-served URL at a venue. QR code on the wall, visitor scans, doorman talks about the venue, optionally collects a single-file agent cartridge tied to that place into their own seed.

## What goes wrong (or doesn't fit)

Honesty about the misfits:

- **High-write-throughput shared state** doesn't fit. GitHub APIs are rate-limited; static raw URLs are read-only. Pure CDN-style scale for reads, but writes don't burst.
- **Anonymous strong-privacy use cases** don't fit. GitHub identity is the substrate; can't pretend otherwise.
- **Vendor-managed uptime SLAs** don't apply. GitHub is the SLA.
- **Cryptographic verification of message provenance beyond GitHub's auth** is on the to-do list; today the auth chain is "GitHub says you're you."

For the workloads where it does fit — anyone whose AI infrastructure needs to be public-and-private simultaneously, owned by the operator, capable of running on any device with no install — none of the off-the-shelf alternatives compose this cleanly.

## Why this matters

The dominant AI-infrastructure narratives push toward two extremes: fully managed cloud, or fully local autonomy. Both leave value on the table. The composition described here suggests a third axis — *layered, gated by identity, on a substrate that's already universal*.

A frozen kernel that's the same everywhere; a body stack that escalates silently with the visitor's identity; lineage that walks the inheritance tree of body innovations; bond cycles that re-baseline kernels without destroying bodies. None of the individual ideas is novel on its own. The composition is.

The platform that compounds these properties is the platform people will build their public-and-private AI on.

That's the field note version. The spec — byte-equality contracts, the rappid identity schema, the doorman/ascended dispatch tree, the bond cycle invariants — is what the next few posts will unfold.
