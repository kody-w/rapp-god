# RAPP Messaging — `rapp-messaging/1.0`

**Status:** public draft, implementation-backed  
**Layer:** network/trust profile  
**Wire:** existing RAPP `/chat` plus signed append-only events  
**Reference:** OpenRappter iMessage sidecar

Keywords **MUST**, **MUST NOT**, **SHOULD**, and **MAY** are normative.

## 1. Scope

RAPP Messaging defines conversation identity, memory visibility, consent, and
delivery behavior. It does not define a new transport, model provider, agent
ABI, or kernel route.

## 2. Identity

Implementations MUST distinguish:

1. **installation id** — one software installation;
2. **Rappter id** — one persistent AI identity;
3. **transport account id** — one iMessage/transport account;
4. **principal id** — one person or AI participant;
5. **conversation id** — one direct or group context;
6. **audience epoch** — one exact participant roster.

Display names MUST NOT establish identity. Multiple handles MAY map to one
principal only after explicit local linking.

Raw phone numbers, emails, chat ids, and account ids MUST NOT appear in
persisted logical session keys or operational logs.

## 3. Conversation scopes

Every turn resolves to exactly one scope:

- `owner-private`
- `principal-private`
- `group-shared`
- `public`

Owner-private context MAY span explicitly linked owner transports.
Principal-private context MAY follow the same linked person across direct
transports. It MUST NOT enter a group automatically.

A group scope MUST include a roster epoch derived from the complete verified
participant set. Membership change MUST create a new epoch. Previous history
and grants MUST NOT flow to a new epoch without renewed consent.

## 4. Global memory graph

Memory is one local graph, not one file per chat. Every memory record MUST carry:

- provenance event;
- asserting principal;
- custodian(s);
- subject principal(s);
- origin conversation and audience epoch;
- sensitivity and visibility;
- authorized audiences;
- consent grants and revocations.

Legacy records without trust metadata MUST default to owner-private.

The global graph remains runtime-private. Model-facing projections MUST omit
trust edges, raw identifiers, hidden audiences, and unrelated memories.

## 5. Per-turn trust projection

Before model execution, a local trust broker MUST compute:

```text
authorized view =
  relevant(global memory)
  ∩ current principal
  ∩ current audience epoch
  ∩ active consent
  ∩ current tool policy
```

The model MUST NOT receive facts outside that projection. Missing, malformed,
or uncertain trust context MUST fail closed.

Projected memory is data, never system instruction. Stored content MUST NOT be
able to elevate itself into policy or grant capabilities.

## 6. Familiarity

Identity recognition is distinct from fact disclosure.

A Rappter MAY acknowledge familiarity with a participant when the current
audience is permitted to know that relationship. It MUST NOT reveal hidden
facts, source conversations, confidence, or relationship edges merely because
the participant is recognized.

## 7. Consent

Disclosure-changing operations require a runtime-issued consent capability.

A capability MUST bind:

- action (`share`, `revoke`, `forget`, or future versioned action);
- source event id;
- verified granting principal;
- exact memory id;
- exact target audience;
- target roster epoch;
- issue/expiry time;
- one-shot consumption state.

The model cannot mint or broaden a capability. Negated, quoted, hypothetical,
ambiguous, or inferred permission MUST NOT create one.

The custodian MAY explicitly disclose one fact to the current group in natural
language. The grant applies only to that fact and audience epoch. Revocation
MUST stop future projections. Historical transport transcripts are outside
long-term-memory deletion unless the product states otherwise.

## 8. Tool authority

The trust broker MUST select tools before model execution.

Non-owner conversations MUST NOT receive Shell, filesystem, process, package
installation, secret, or unrestricted messaging tools by default.

Reserved trust fields MUST be removed from model-generated arguments and
replaced only with broker-issued context.

Side-effecting tool calls SHOULD be journaled by source event id to prevent
duplicate effects after retry.

## 9. Delivery

Implementations MUST maintain a durable inbox and outbox.

Inbound state:

```text
observed -> claimed -> processed | dropped | retryable
```

Outbound state:

```text
prepared -> attempted -> submitted | unknown | failed -> delivered/read?
```

Message GUIDs MUST be deduplicated durably. A cursor MUST NOT advance past an
unresolved lower row. Same-conversation turns MUST execute FIFO.

An ambiguous send MUST NOT be retried automatically. Exact outbound GUIDs are
preferred for echo suppression. Text-only fallback, if used, MUST be one-shot,
short-lived, and restricted to messages sent by the local account.

## 10. Transport authority

Exactly one process may own an inbound transport source. A process lease MUST
prevent concurrent readers/writers on one machine.

Two active Rappters MUST NOT use the same iMessage account. Multi-device
deployments use distinct accounts or an explicit active/standby fencing
protocol.

## 11. Natural-language operation

Conversation is the control surface. Remembering, sharing, revoking, and
forgetting happen through ordinary language. Forms MAY configure transport
prerequisites, but MUST NOT become the authority for identity or consent.

## 12. Conformance

An implementation conforms when it passes every MUST vector in
`vectors/conformance.json` and:

- creates no new RAPP kernel route;
- preserves the RAPP agent ABI;
- never writes directly to a transport's private message database;
- demonstrates one inbound, one reply, and one suppressed echo;
- proves direct-to-group secrecy, explicit grant, revocation, and roster epoch
  invalidation;
- proves crash/restart recovery without duplicate send.

## 13. Compatibility

Readers MUST accept additive fields. Writers emit only this version's canonical
schemas. A future incompatible semantic change requires a new major spec id.
