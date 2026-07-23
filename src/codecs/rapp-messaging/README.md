# RAPP Messaging

**Human trust semantics for conversations between people and Rappters, carried
over the existing RAPP wire.**

RAPP Messaging is not a new chat endpoint. It is a profile over:

- `POST /chat` for local brainstem capability;
- signed append-only events for asynchronous/federated delivery;
- existing transports such as iMessage.

The protocol defines how a Rappter keeps one global memory graph while behaving
appropriately inside a direct conversation, a group, or a conversation whose
trust changes mid-thread.

## The central rule

> **Retain full private context locally; disclose only the minimum authorized,
> relevant projection for the current audience.**

Identity recognition is not disclosure. A Rappter may know a participant and
acknowledge familiarity without revealing private facts, sources, relationships,
or prior conversations.

## What this repository specifies

- stable identities for Rappters, installations, transport accounts, people,
  direct conversations, and groups;
- one global provenance-rich memory graph;
- per-turn trust projection;
- owner, principal-private, and group-shared scopes;
- group membership epochs;
- explicit, fact-specific, audience-specific consent;
- consent revocation and one-shot capabilities;
- tool capability restrictions by audience;
- durable inbox/outbox delivery and ambiguity handling;
- one active transport authority per account;
- iMessage as the first reference transport profile.

## Documents

- [`SPEC.md`](SPEC.md) — normative `rapp-messaging/1.0`
- [`IMESSAGE.md`](IMESSAGE.md) — `rapp-messaging-imessage/1.0`
- [`schemas/`](schemas/) — machine contracts
- [`vectors/conformance.json`](vectors/conformance.json) — behavior vectors
- [`registry.json`](registry.json) — static machine index

## Reference implementation

OpenRappter implements the initial iMessage profile:

- https://github.com/kody-w/openrappter
- https://github.com/kody-w/openrappter/pull/28

Its consumer UI remains TypeScript/OpenClaw-compatible. Its sacred execution
shape remains the RAPP Python brainstem and hot-loaded `*_agent.py` cartridge
contract.

## Verify

```bash
python3 verify.py
```

## License

MIT
