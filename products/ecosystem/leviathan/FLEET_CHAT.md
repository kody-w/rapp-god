# RAPP Fleet-Chat — `rapp-fleet-chat/1.0`

**Status:** canonical · stable · public
**Home:** `kody-w/leviathan/FLEET_CHAT.md`
**Spec ID:** `rapp-fleet-chat/1.0`
**Supersedes (as the fleet wire):** the Leviathan SPEC v1.0 transport `POST /api/agent/<AgentName>` (kept LAN-only-legacy, slated for removal — §5)
**Depends on:** `rapp-neighborhood-protocol/1.0` §6 (twin-chat) · `rapp-commons-event/1.0` (signed event wrapper) · `rapp-eternity/1.0` (rappid identity) · `rapp-resident` (cloud relay) · RAPP CONSTITUTION **Article XXV** ("Chat Is The Only Wire")
**Realizes:** rapp-roadmap **Phase 1** — *"Close the RCE, make the fleet sellable"*

> **One mind, many bodies — but the mind now speaks the only wire.**
> A fleet command is a **signed twin-chat event delivered over `POST /chat`**, verified before any agent runs. There is no second wire.

---

## 0. Why this supersedes the `/api/agent` wire

The Leviathan Protocol (SPEC v1.0) drove a fleet of no-LLM bodies over `POST /api/agent/<AgentName>` — one request runs a named agent's `perform()` directly. It is fast and throttle-free, but it has **two fatal defects**:

1. **It is off-canon.** RAPP CONSTITUTION **Article XXV** states *"`/chat` is the universal interface… the brainstem does not know — and must never need to know — which kind of caller is on the other end. One wire. Same shape. Forever."* `/api/agent` is a **second wire** with a different shape. A backup brainstem unearthed in 50 years answers `/chat`; it has no obligation to answer `/api/agent`. The fleet built on `/api/agent` is therefore not time-travel-safe and not part of the contract.
2. **It is unauthenticated remote code execution.** `POST /api/agent/<name>` calls `inst.perform(**body)` with **no auth, no allowlist**. A body that has loaded a shell agent (e.g. `RemoteControl`, which runs `subprocess.run(command, shell=True)`) turns one request into fleet-wide RCE. This is the standing liability rapp-roadmap **Phase 1** exists to close. Even LAN exposure is a liability; the cartridges stay default-OFF until this spec lands.

`rapp-fleet-chat/1.0` closes both at once: the fleet rides **the canonical `/chat` wire**, carrying a **signed twin-chat event** that is **verified and allowlist-gated** before any `perform()` is reached. We do not harden a route that should not exist — we retire it and route fleet messaging the way the rest of the estate already routes social messaging (`rapp-resident` has carried this exact shape live, 67 verified events).

This spec adds **no new brainstem symbols and no kernel edit**. It is PROPOSED (to-build) entirely as a **drop-in, ABI-conformant agent** (the `FleetChat` relay agent) plus a spine profile. The grail (`brainstem.py`) is never touched.

---

## 1. The event — a fleet command is a signed twin-chat message

A fleet command does not invent a new schema. It is a **layering of three existing canonical schemas**, outermost to innermost:

```
rapp-commons-event/1.0          ← signing / relay wrapper (the envelope on the wire)
  └─ body: rapp-twin-chat/1.0   ← the twin-chat envelope (kind = "console")
        └─ payload              ← the fleet directive: { agent, kwargs }
```

### 1.1 The signed wrapper — `rapp-commons-event/1.0`

Per `rapp-neighborhood-protocol/1.0` §6 ("On-relay form"), every twin-chat envelope that crosses a relay rides inside the signed event wrapper:

```json
{
  "schema": "rapp-commons-event/1.0",
  "kind":   "console",
  "from":   "<mind rappid — Eternity form rappid:@<owner>/<slug>:<64hex>>",
  "ts":     "<RFC3339 UTC, no fractional seconds>",
  "body":   { ...a rapp-twin-chat/1.0 envelope (§1.2)... },
  "in_reply_to": null,
  "sig_suite": "none | ecdsa-p256",
  "pub":    "<JWK ECDSA P-256 public key, REQUIRED iff sig_suite = ecdsa-p256, else omitted>",
  "sig":    "<lowercase hex ECDSA P-256 signature over canonical JSON of all fields except sig, REQUIRED iff sig_suite = ecdsa-p256>"
}
```

- `kind` is `"console"` for a fleet command (it operates a neighbor's runtime — `rapp-neighborhood-protocol` §6b reserves `console` for exactly this, "operate a neighbor's runtime").
- `sig_suite` is the **trust selector** (§3). `"none"` ⇒ gh-collaborator authorization (default); `"ecdsa-p256"` ⇒ optional keypair signature.
- This is the schema `rapp-vneighborhood/1.0` front-door conformance already requires on a relay. The fleet adds nothing to it.

### 1.2 The twin-chat envelope — `rapp-twin-chat/1.0` (the `body`)

```json
{
  "schema": "rapp-twin-chat/1.0",
  "from_rappid": "<mind rappid — same as wrapper.from>",
  "to_rappid":   "<body's door rappid — Eternity form, addresses the target brainstem>",
  "utc":   "<RFC3339 UTC — MUST equal wrapper.ts>",
  "nonce": "<128-bit random hex — the correlation id for the reply>",
  "kind":  "console",
  "payload": {
    "agent":  "<AgentName>",
    "kwargs": { ...JSON object of the agent's perform() kwargs; {} if none... },
    "deadline_ms": 30000
  },
  "facets": []
}
```

- `to_rappid` is the **addressing field** — it names which body in the fleet this command is for, by its **Eternity door rappid** (`rappid:@<owner>/<slug>:<64hex>`, sha256 content-address, per `rapp-eternity/1.0`). A relay fans one wrapper to the body whose door rappid it equals.
- `payload.agent` + `payload.kwargs` ARE the Leviathan invocation: they carry exactly what `POST /api/agent/<name>` carried (`<name>` and the JSON kwargs body) — **same semantics, new envelope**. Kwargs pass straight to `perform()` with no host-side magic, exactly as in Leviathan SPEC §2.1.
- `nonce` is the correlation key. The reply (§4.3) echoes it.

### 1.3 The reply — `rapp-twin-chat-response/1.0`

The body answers with the §6e response shape, carrying the agent's result:

```json
{
  "schema": "rapp-twin-chat-response/1.0",
  "channel": "fleet-chat",
  "envelope": { ...the request twin-chat envelope, echoed... },
  "status": 200,
  "response": {
    "ok": true,
    "agent": "<AgentName>",
    "result": <the agent's perform() return — see §4.2 double-encoding>,
    "fleet_status": "ok",
    "event_id": "sha256:<hex of the request wrapper>"
  }
}
```

`fleet_status` is the closed Leviathan status taxonomy (§4.4), surfaced inside the canonical reply so a controller keeps the same decision model it had over `/api/agent`.

---

## 2. Transport — `POST /chat` only

A fleet command is PROPOSED (to-build) by **`POST /chat`** and nothing else. The brainstem `/chat` request envelope (Article XXV) is fixed and additive-only; the fleet uses its existing string field, so **any brainstem of any vintage accepts it without a code change**:

```http
POST /chat  HTTP/1.1
Content-Type: application/json

{ "user_input": "<canonical JSON of the rapp-commons-event/1.0 wrapper (§1.1)>",
  "session_id": "<optional per-conversation GUID>", }
```

- The wrapper is serialized as **canonical JSON** (§3.3) and placed verbatim in `user_input`. No new request fields are introduced — Article XXV's envelope is untouched.
- The brainstem returns its standard `/chat` response envelope; the `rapp-twin-chat-response/1.0` object (§1.3) is carried in the kernel's **`response`** field — the kernel's reply field on the success envelope {response, session_id, agent_logs, voice_mode, model, requested_model} the kernel emits (alongside `session_id`). Correlate to the request by `session_id` and the echoed `nonce` / `event_id`.

### 2.1 The interpreter is a drop-in agent, not a new route

A `rapp-fleet-chat/1.0`-conformant body loads a fleet-chat relay agent — the **`FleetChat`** pattern (**to be built**; not yet a published agent). It is an ordinary `BasicAgent` (frozen ABI: `metadata` + `perform(**kwargs) -> str`, auto-discovered from `agents/`), and is the **only** thing that interprets a fleet event. It MUST NOT add a REST route, MUST NOT patch `brainstem.py`, and MUST NOT introduce a new brainstem symbol. It is byte-portable to any unmodified brainstem.

The `FleetChat` pattern does four things, in order, on every event (§4.1): **verify → allowlist → dispatch → record+respond**.

### 2.2 Deterministic recognition (canon-preserving, no throttle)

The Leviathan no-LLM fast path is preserved without a second wire. The `FleetChat` pattern contributes a `system_context()` whose single instruction is: *"If `user_input` parses as a `rapp-commons-event/1.0` wrapper with `kind:"console"`, route it to the fleet-chat relay agent verbatim and do not reason about its content."* Recognition is by **envelope shape**, not semantics, so the routing turn is trivial and deterministic — the body never spends a model on *deciding which agent to run* (the `payload.agent` already names it). This keeps fan-outs fast and off the shared Copilot token while staying 100 % on the `/chat` wire. The fast path is an optimization of *routing*, never a bypass of *verification* — §4.1 runs unconditionally.

---

## 3. Signing & trust

Trust is the RAPP estate's standard two-mode model: **gh-collaborator by default, optional keypair sovereignty**. No component ever *requires* a keypair (consistent with `rapp-eternity/1.0`: identity is PKI-free sha256; keypair binding is opt-in, never mandatory).

### 3.1 Mode A — gh-collaborator (default, `sig_suite: "none"`)

The wrapper carries `sig_suite:"none"` and **no `sig`/`pub`**. Authorization is proven by the **transport/relay**, not by a signature on the event:

- The relay is **`rapp-resident`** (the cloud relay) or a kited host. The relay authenticates the poster as a **GitHub collaborator** of the body's door repo (`@<owner>/<slug>` from `to_rappid`) before it forwards the event to `/chat`. Holding push access to the door repo *is* the authorization — the same default as `rapp-eternity/1.0` ownership and the rappid-eternity keypair-OPTIONAL resolution.
- A body that trusts its relay (the common single-operator and same-org fleet case) accepts `sig_suite:"none"` events that arrive via that relay. A body MAY pin the set of relays it trusts.

### 3.2 Mode B — optional keypair (`sig_suite: "ecdsa-p256"`)

For a self-locating, relay-independent, takedown-survivable command (e.g. a cross-org fleet where no single relay is mutually trusted), the mind binds the event to a keypair per `rapp-eternity/1.0` optional sovereignty:

- `pub` = the mind's JWK ECDSA P-256 public key.
- `sig` = ECDSA P-256 signature over the **canonical JSON** (§3.3) of the wrapper with `sig` omitted.
- The body verifies `sig` against `pub`, and verifies that `pub`'s sha256 fingerprint is bound to `from`'s rappid (per `rapp-eternity/1.0`). A valid signature authorizes regardless of which relay delivered it — the relay is never trusted (`rapp-neighborhood-protocol` §6/§8).

**Neither mode is privileged by the spec.** A body declares which mode(s) it accepts in its `fleet-auth` spine profile (§3.4). A body MAY require Mode B for sensitive allowlisted agents while accepting Mode A for read-only ones. **No component may require a keypair as the only option** — Mode A must always be an available path, so identity stays PKI-free.

### 3.3 Canonical JSON

For both signing and the `event_id` (§4.5): UTF-8, object keys **recursively sorted**, **no insignificant whitespace**, `sig` (and, when signing, `sig` only) omitted from the signed bytes. This is the identical canonicalization rule `rapp-commons-event/1.0` verification rule 4 already mandates — fleet-chat reuses it unchanged.

### 3.4 The auth slot (forward to Entra)

The wrapper reserves room for an additive bearer credential without a schema break: a body MAY require an **HMAC shared-secret bearer** (`BRAINSTEM_FLOCK_SECRET`, nonce + timestamp replay window) carried in the `/chat` request, validated by the fleet-chat relay agent before dispatch. This slot is **designed to later accept Entra Agent ID claims** (rapp-roadmap Phase 1) with no change to this spec — the token is additive to Mode A/B, never a replacement for them.

---

## 4. Async semantics & the dispatch gate

### 4.1 The four-step gate (runs on every event, unconditionally)

```
1. VERIFY     parse wrapper; check schema/kind; enforce trust mode (§3); reject expired/replayed (§4.5)
2. ALLOWLIST  payload.agent MUST be in the body's DEFAULT-DENY allowlist (§4.6); else refuse
3. DISPATCH   run agents[payload.agent].perform(**payload.kwargs), bounded by payload.deadline_ms
4. RECORD     append the call + outcome to the flight recorder; return rapp-twin-chat-response/1.0
```

There is **no path to `perform()` that skips steps 1–2.** That is the whole point: this closes the RCE.

### 4.2 Result encoding

`perform()` returns are surfaced in `response.result` exactly as Leviathan SPEC §2.1: agents commonly return a `json.dumps(...)` string (double-encoding). A controller SHOULD best-effort decode a string `result` that begins with `{`/`[` while keeping the raw form available; plain strings pass through as-is.

### 4.3 At-least-once, idempotent, UTC-first

- **Append-only event log.** Every accepted event is appended to the body's local relay log under the `rapp-commons-event/1.0` filename convention (`<from-fingerprint>-<ts>.json`). Nothing is ever mutated (the commons merge rule: `(from, ts)` is the universal key; offline clones union deterministically).
- **At-least-once delivery.** A relay may redeliver. Bodies MUST be idempotent on redelivery via `event_id` (§4.5). A controller retries only the `down` status (provably undelivered); never auto-retries `timeout` (may have executed) or a non-idempotent agent — identical to Leviathan SPEC §5.
- **UTC-first ordering.** `utc`/`ts` are RFC3339 UTC with no fractional seconds. Per-`from` timestamps are **monotonically non-decreasing**; a body rejects an event whose `ts` predates that mind's latest accepted event (backdating defense, `rapp-commons-event/1.0` rule 5).

### 4.4 Status taxonomy (frozen, inherited)

`response.fleet_status` ∈ `{ ok, down, timeout, missing, error, bad_response, refused }` — the Leviathan SPEC §3 closed taxonomy, plus **`refused`** (new in fleet-chat): the gate rejected the event at step 1 (bad signature / untrusted relay / expired) or step 2 (agent not on the allowlist). **Failure is data, never an exception.** A fan-out returns a complete per-body map, one Result per addressed body.

### 4.5 Idempotency key

`event_id = "sha256:" + hex(sha256(canonical_json(wrapper)))` over the **full signed wrapper** (sig included). A body keeps a bounded seen-set of `event_id`s; a repeat is acknowledged with the prior result and **not re-dispatched**. `nonce` correlates the reply; `event_id` dedups the delivery.

### 4.6 Default-deny allowlist

A body ships with an **empty or read-only-only** allowlist. An agent runs via fleet-chat **only if explicitly allowlisted** in the `fleet-auth` spine profile. `RemoteControl` and every shell/exec agent are **OUT of the default** — enforced and tested, not theater (rapp-roadmap Phase 1 exit criterion). Every gated call **and every denial** is recorded append-only by the flight recorder, caller-attributed (`from` rappid).

### 4.7 Offline-degrade

When no relay is reachable, the local relay is **a file on disk** (`local ≡ kited ≡ cloud`, byte-identical, `rapp-neighborhood-protocol` §6). A mind may append events to its outbound lane; the body's relay log unions them on the next beat (`rapp-commons-event/1.0` replay semantics). A whole fleet runs fully offline and re-converges by import — losing not a step. UTC-first ordering makes the merge deterministic regardless of the order events are seen.

---

## 5. Backward-compat & deprecation

`POST /api/agent/<AgentName>` is **deprecated** and reclassified **LAN-only-legacy**:

- A `rapp-fleet-chat/1.0`-conformant body, **in production (non-LAN)**, MUST refuse `/api/agent` for cross-host callers — disable the route, or default-deny it identically to §4.6. The unauthenticated route MUST NOT reach any `perform()` from off-LAN. (`FlockEndpoint` is GATED and default-OFF until it enforces this.)
- The route MAY remain available **on a trusted subnet** for legacy controllers during migration, but it is slated for **removal**; new fleets MUST NOT depend on it.

### 5.1 Migration map (Leviathan `/api/agent` → fleet-chat over `/chat`)

| Leviathan SPEC v1.0 (`/api/agent`) | `rapp-fleet-chat/1.0` (over `/chat`) |
|---|---|
| `POST http://body:7071/api/agent/<Name>` | `POST http://body:7071/chat`, `user_input` = signed wrapper |
| URL path segment `<Name>` | `body.payload.agent` |
| JSON request body (the kwargs) | `body.payload.kwargs` |
| (none — unauthenticated) | wrapper `sig_suite` + relay gh-collaborator / optional `sig` (§3) |
| HTTP 200 `{ok, agent, result}` | `response.{ok, agent, result}` inside `rapp-twin-chat-response/1.0` |
| HTTP 404 `{ok:false, available}` | `fleet_status:"missing"`, `available` echoed |
| HTTP 500 `{ok:false, error}` | `fleet_status:"error"`, `error` echoed |
| controller verbs `one` / `all` / `scatter` | N signed events (one per addressed `to_rappid`), fanned by the relay/controller |
| Flight Recorder `channel:"api/agent"` | Flight Recorder `channel:"fleet-chat"` (caller = `from` rappid) |

The reference controller `leviathan.py` (verbs `one/all/scatter/route/deploy`) keeps its surface; only its transport changes — it emits signed wrappers to `/chat` instead of raw kwargs to `/api/agent`.

---

## 6. How it composes with the estate

- **Article XXV** ("Chat Is The Only Wire"): satisfied. The fleet is now a Layer-2 caller of `/chat` carrying the §6 envelope — *"it is not a new unit or taxonomy,"* and a backup brainstem of any vintage answers it.
- **`rapp-neighborhood-protocol/1.0` §6**: a fleet command is a twin-chat `console` event; the fleet is just an **app** (a channel + a kind) on the twin-chat base layer, exactly like the commons, rappterbook, and the forum. The relay is interchangeable (`local ≡ kited ≡ cloud`).
- **`rapp-commons-event/1.0`**: the wire wrapper, verification rules, canonical JSON, append-only merge `(from, ts)`, and per-from monotonic ts are reused unchanged.
- **`rapp-eternity/1.0`**: addressing (`to_rappid`) and identity (`from`) are Eternity rappids — sha256 content-addresses, PKI-free; the optional `sig` is the opt-in sovereignty path, never required.
- **`rapp-resident`**: the cloud relay that authenticates collaborators and forwards to `/chat` — the component that already proved this shape live (67 verified events).
- **`rapp-spine`**: a `fleet-auth` profile declares accepted trust modes, the allowlist, and the optional HMAC/Entra slot — landed **identically in T1 (brainstem) and T2 (function_app)**, per the stem/function_app parity invariant.
- **Flight Recorder**: every gated call and denial is recorded append-only, caller-attributed — the accountability substrate Phase 1 maps to a Purview-shaped schema.
- **Leviathan**: this IS the fleet's wire now; SPEC v1.0 §2 (`/api/agent`) becomes the legacy LAN transport behind it.

---

## 7. Conformance

A body is **`rapp-fleet-chat/1.0`-conformant** iff **all** hold:

1. It **accepts a signed fleet event over `POST /chat`** (a `rapp-commons-event/1.0` wrapper, `kind:"console"`, carrying a `rapp-twin-chat/1.0` body) and answers with a `rapp-twin-chat-response/1.0` carrying `fleet_status`.
2. It runs the **four-step gate** (§4.1) on every event — verify, default-deny allowlist, dispatch, record — with **no path to `perform()` that skips verify+allowlist**.
3. It enforces the trust model (§3): accepts `sig_suite:"none"` only via a trusted relay; verifies `sig_suite:"ecdsa-p256"` against the rappid-bound key; **never requires a keypair** as the only path.
4. Its **default allowlist excludes every shell/exec agent** (`RemoteControl` et al.), enforced and tested.
5. It is **idempotent** on redelivery by `event_id` and **rejects backdated** events (per-from monotonic `ts`).
6. **In production it refuses unsigned cross-host `POST /api/agent/<name>`** — the legacy route does not reach any `perform()` from off-LAN.
7. It adds **no new brainstem symbol, no REST route, and no kernel edit** — the interpreter is a drop-in `BasicAgent` only.

A controller is conformant iff it delivers fleet commands **only** over `/chat` as signed wrappers, classifies every outcome into the §4.4 taxonomy, and retries only `down`.

---

## 8. Worked example

**Scenario.** The mind (`rappid:@kody-w/leviathan-control:9f...e1`) drives a 2-body fleet. It runs the read-only `Health` agent on body A (allowlisted) and attempts `RemoteControl` on body B (default-deny). Body A trusts its `rapp-resident` relay, so the command uses Mode A (`sig_suite:"none"`).

**8.1 — Command to body A, on the wire (`POST http://body-a:7071/chat`):**

```json
{
  "user_input": "{\"schema\":\"rapp-commons-event/1.0\",\"kind\":\"console\",\"from\":\"rappid:@kody-w/leviathan-control:9f3c...e1\",\"ts\":\"2026-06-28T17:04:12Z\",\"body\":{\"schema\":\"rapp-twin-chat/1.0\",\"from_rappid\":\"rappid:@kody-w/leviathan-control:9f3c...e1\",\"to_rappid\":\"rappid:@kody-w/body-a-door:7a11...0c\",\"utc\":\"2026-06-28T17:04:12Z\",\"nonce\":\"3b9a2f7c1e8d4a60b5c2d9e0f1a2b3c4\",\"kind\":\"console\",\"payload\":{\"agent\":\"Health\",\"kwargs\":{},\"deadline_ms\":30000},\"facets\":[]},\"in_reply_to\":null,\"sig_suite\":\"none\"}"
}
```

**8.2 — Body A reply (`200 OK`, in the kernel's `response` field):**

```json
{
  "schema": "rapp-twin-chat-response/1.0",
  "channel": "fleet-chat",
  "envelope": { "...": "the request twin-chat envelope, echoed (nonce 3b9a...c4)" },
  "status": 200,
  "response": {
    "ok": true,
    "agent": "Health",
    "result": "{\"copilot\":\"✓\",\"model\":\"claude-sonnet\",\"version\":\"0.4.0\"}",
    "fleet_status": "ok",
    "event_id": "sha256:11d4...aa"
  }
}
```

Flight recorder appends: `{caller:"rappid:@kody-w/leviathan-control:9f3c...e1", channel:"fleet-chat", agent:"Health", outcome:"ok"}`.

**8.3 — Command to body B attempting `RemoteControl` — refused at the gate (step 2):**

```json
{
  "schema": "rapp-twin-chat-response/1.0",
  "channel": "fleet-chat",
  "envelope": { "...": "echoed; payload.agent was RemoteControl" },
  "status": 403,
  "response": {
    "ok": false,
    "agent": "RemoteControl",
    "error": "agent 'RemoteControl' is not on this body's fleet-chat allowlist (default-deny)",
    "fleet_status": "refused",
    "event_id": "sha256:42bc...e7"
  }
}
```

The denial is recorded append-only, caller-attributed. **No `perform()` ran.** Under the old `/api/agent` wire this same call would have been unauthenticated fleet-wide RCE; under `rapp-fleet-chat/1.0` it is `refused` data, the way it must be.

**8.4 — Cross-org variant (Mode B).** Were body B in another org with no mutually trusted relay, the mind would set `sig_suite:"ecdsa-p256"`, attach `pub` + `sig` over the canonical wrapper, and body B would verify the signature against the mind's rappid-bound key before the same gate ran — relay untrusted, command still authorized. The allowlist decision is identical; only the *authorization* path differs. A keypair is used here **because the operator opted into it**, never because the spec demands one.

---

*One mind, many bodies — every command signed, every command verified, every command on the one wire. The mind thinks; the bodies verify, execute, and record. Nothing reaches a `perform()` ungated, and there is no second wire. That is the whole protocol.*