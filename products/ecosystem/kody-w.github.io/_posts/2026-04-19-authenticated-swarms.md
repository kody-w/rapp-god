---
layout: post
title: "Authenticating an HTTP runtime: who can call which pack?"
date: 2025-10-30
tags: [auth, security, oauth, runtime, design]
---

A small HTTP runtime I ship has no auth. If you know the URL of a deployed pack of agents and you can reach the network it's on, you can call it. For a localhost-bound deployment, the network containment is the security model — `127.0.0.1` is unreachable from the outside, and that's enough.

The moment packs become network-reachable — exposed for LAN access, deployed to a cloud functions runtime, or called through an edge relay — that model breaks. Anyone who can reach the URL can call any pack. There's no concept of "this pack belongs to this user" enforced anywhere.

This post is the design I'd ship when it's time to add auth.

**Threat model:**

Three kinds of unauthorized access I care about:
1. **Random internet users** finding a public pack endpoint and pinging it.
2. **Someone within the same LAN** (a coworker, a guest, a compromised IoT device) calling a pack meant for one user.
3. **A coworker's pack being called by someone else on the team** when fine-grained access matters.

The first two have the same answer: any auth system will block them. The third is more interesting and is where most of the design decisions live.

**Option A: shared secret per pack.**

Each pack gets a randomly-generated token at deploy time. The deploy response includes it:

```json
{
  "status": "ok",
  "pack_guid": "abc-123",
  "pack_url": "https://endpoint/api/pack/abc-123/agent",
  "pack_token": "tok_4f2a8b9c..."
}
```

Every subsequent call to that pack includes `Authorization: Bearer tok_4f2a8b9c...`. The server validates the token against the pack. Tokens stored hashed at rest (bcrypt or similar).

**Pros:** Simple. No auth provider needed. Easy to rotate (re-deploy pack, get new token). Easy to share (paste token in a DM to a coworker who needs access).
**Cons:** Token sharing is the auth model. Lose the token, lose access. Steal the token, get full access. No fine-grained "user X can call agent Y but not agent Z."

**Option B: identity provider (e.g. GitHub OAuth).**

The chat host already does OAuth. The deploy step records the deployer's identity. Calls to the pack require a bearer token matching the deployer's identity (or being on an explicit allowlist).

```json
{
  "pack_guid": "abc-123",
  "owner": "alice",
  "allowed_users": ["alice", "bob@org"]
}
```

**Pros:** Identity-based, not token-based. Revoking access is "remove from allowlist." Sharing is invitation, not credential leak. Same identity model as everything else.
**Cons:** Every caller needs an OAuth flow. The pack server has to validate identity tokens (HTTP call to the provider on every request, or a cache thereof). More moving parts.

**Option C: per-call signed envelopes.**

The chat host signs each request with the user's identity. The pack server validates the signature. No long-lived bearers; every call is independently authenticated.

**Pros:** Most secure. No standing access — each request must be authentic.
**Cons:** Most complex. Requires a key-management story (where does the signing key live? rotate it how?).

**My pick: A first, B once we have multi-user.**

For the single-user case (your laptop, your packs), a shared secret is enough. The token lives in the chat host's settings next to the URL. Calls automatically include it. The user never types it.

For the multi-user case (deploying a pack for a team to call), an OAuth-based identity provider wins. Allowlists by username are the natural granularity. The host can check "you're already signed in; you're on this pack's allowlist" and route accordingly.

C is theoretically nicer but the operational cost is too high for a project this small.

**Per-agent permissions inside a pack:**

A maximalist model would let a pack declare per-agent ACLs:

```json
{
  "agents": [
    {"name": "PublicWeather", "allowed_users": "*"},
    {"name": "InternalCRMQuery", "allowed_users": ["sales-team@org"]}
  ]
}
```

The model could call `PublicWeather` for any caller; the language model has to know not to even *propose* `InternalCRMQuery` for unauthorized users (or surface a clean "you don't have permission" if it tries).

This is real complexity. Pretty sure I don't need it on day one. A pack is a coherent unit of trust — if you're on the pack's allowlist, you can call any agent in it. If you need finer granularity, deploy two packs.

**The rollout plan when it's time:**

1. Make `/api/pack/deploy` mint a token by default (Option A). Backwards-compatible: existing public packs keep working without a token, but new deploys get one.
2. The chat host stores the token alongside the URL in its settings. Every call includes it.
3. Add an `--auth-required` flag on the pack server that rejects calls without a valid token. Off by default for now; on by default once tokens are universal.
4. Layer Option B (identity-provider OAuth) for packs that need team access. Deploy-time flag.

Auth is one of those things you ship just before you actually need it, never sooner. Right now the cost-benefit isn't there for most users. We'll know when it is.