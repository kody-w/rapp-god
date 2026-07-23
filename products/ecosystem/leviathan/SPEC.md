# The Leviathan Protocol — SPEC v1.0

A wire contract for driving a network of **no-LLM executor nodes** ("bodies") from
a single external intelligence ("the mind"). The mind decides everything; each body
just runs one named local capability ("agent") and returns the result. No body ever
calls an LLM to interpret a command, so the network never throttles on a shared
model and a fan-out completes in ~the latency of the slowest body.

This document is language-agnostic. Any intelligence — any language, any agent
runtime — can either **drive** the network (implement a controller against §2) or
**join** it (expose §2 from a node, see §6). The reference controller is
`leviathan.py`; the reference join-agent is `flock_endpoint.py`.

---

## 1. Roles

- **Mind (controller).** The only intelligence. Holds a roster of bodies, decides
  which agent + args to run where, reads results, decides next. Stateless toward the
  bodies; needs no LLM token to operate the network.
- **Body (node).** An HTTP host that exposes the §2 contract. It runs named *agents*
  (local capabilities). It performs no reasoning about *which* agent to run — the
  mind names it explicitly.
- **Agent.** A named capability on a body with a `perform(**kwargs) -> value`
  contract. The mind invokes it by name with JSON kwargs.

## 2. The node contract (what a body MUST expose)

Base URL per body: `http://<host>:<port>` (reference port `7071`). All bodies in a
roster expose the identical contract; they are interchangeable.

### 2.1 `POST /api/agent/<AgentName>` — the one verb that matters

Run a named agent directly. **No LLM is consulted.**

- **Request:** body is a JSON **object** of the agent's kwargs (send `{}` if none).
  `Content-Type: application/json`. Methods: `POST` (and `OPTIONS` for CORS).
- **Success — HTTP 200:**
  ```json
  { "ok": true, "agent": "<AgentName>", "result": <value> }
  ```
  `result` is the agent's `perform()` return. **Convention:** agents commonly return
  a `json.dumps(...)` **string**, so `result` is often a JSON-encoded string — a
  *double-encoding*. A controller SHOULD best-effort decode it (parse `result` when
  it is a string beginning with `{` or `[`) into a structured value, and MUST keep
  the raw form available. Plain-string returns (e.g. `"aGk="`) are left as-is.
- **Agent not found — HTTP 404 with JSON body:**
  ```json
  { "ok": false, "error": "no agent 'X'", "available": ["AgentA", "AgentB", ...] }
  ```
  The `available` list lets the mind route/repair. A 404 with a **non-JSON / HTML**
  body means the node is reachable but does NOT implement this contract (see §3 `bad_response`).
- **Agent raised — HTTP 500 with JSON body:**
  ```json
  { "ok": false, "agent": "<AgentName>", "error": "<exception message>" }
  ```
- Kwargs are passed straight to `perform()` with **no host-side magic** (no implicit
  identity, no context injection). The mind sends exactly the agent's signature.

### 2.2 `GET /health` — liveness + degrade signal

```json
{ "copilot": "✓" | "pending", "model": "<id>", "version": "<x.y.z>", "agents": ["..."] }
```
`copilot == "✓"` means the body's *own* LLM path is live; any other value (e.g.
`"pending"`) means that path is degraded **but the body is still fully drivable via
`/api/agent`** (that route needs no LLM). This three-state distinction — *down* vs
*alive-but-LLM-degraded* vs *healthy* — is load-bearing.

### 2.3 `GET /agents` — capability inventory

```json
{ "files": [ { "filename": "x_agent.py", "agents": ["X"] }, ... ] }
```
The reverse index (which body holds which agent) for routing.

### 2.4 `POST /agents/import` — install a capability (no restart, no LLM)

`multipart/form-data`, field name **`file`**, filename **MUST** end in `_agent.py`
(else the node may rename/reject). The body hot-loads it. Idempotent (re-import reloads).

### 2.5 `DELETE /agents/<filename>` — remove a capability.

## 3. Result model & the status taxonomy

Every single-body call resolves to exactly one **Result**; **failure is data, never
an exception.** A controller MUST classify every outcome into this closed taxonomy —
it is the join key for all decisions:

| status | meaning | cause | retry policy |
|---|---|---|---|
| `ok` | success | HTTP 200 + `ok:true` | — |
| `down` | body unreachable | connection refused / DNS / no route | **safe to retry** (provably undelivered) |
| `timeout` | no reply in time | socket timeout / deadline | **do NOT auto-retry** (may have executed) |
| `missing` | agent absent | HTTP 404 with JSON `{available}` | re-route or install |
| `error` | agent raised | HTTP 500 / `ok:false` | conditional |
| `bad_response` | not a Leviathan node | 2xx non-JSON, HTML 404, 405, proxy/login | install the contract |

A **fan-out** (running one agent across many bodies, or many agents across many
bodies) MUST return a **complete per-body map** — exactly one Result per requested
body, including unreachable ones (`status:"down"`). A totally-down fleet yields N
down Results, never an empty set and never a raised error.

## 4. Concurrency (recommended)

Fan-out is network-bound (blocking socket I/O). A controller SHOULD contact bodies
**concurrently** (threads/async), with a **per-call timeout** AND an **overall
deadline**, pre-seeding the result map with `down` placeholders so one hung body can
never stall the aggregate. Bound concurrency to protect file descriptors and the
network; run heavy/credential-sensitive broadcasts in small waves.

## 5. Retry & routing rules

- Retry only `down` (undelivered). Never auto-retry `timeout` (unknown outcome) or a
  non-idempotent shell command.
- Treat topology (`/agents`) as a **hint**; the per-call Result is **truth**. Route
  to known holders, but let the Result self-correct (`missing`/`down`) and fail over.

## 6. How to JOIN the network (expose the contract from a node)

A node needs only §2. Two paths:

1. **Reference brainstem + join-agent.** Run a RAPP-style brainstem and drop
   `flock_endpoint.py` into its `agents/` directory. On load it injects
   `POST /api/agent/<name>` (dispatching to any loaded agent's `perform()`), with no
   engine edit and no restart — it even works while the node's own LLM path is dead.
2. **Implement §2 directly.** Any HTTP server in any language that honors §2.1–§2.5
   is a valid body. The mind cannot tell the difference.

## 7. Accountability (recommended)

A body SHOULD record every `/api/agent` call to a local append-only ledger
(timestamp, caller, agent, args, result) so the network's actions are auditable
regardless of which mind drove it. The reference `flock_endpoint.py` writes each
call to a Flight Recorder store tagged `caller="hivemind", channel="api/agent"`,
honoring a local enable/pause flag.

## 8. Security — read this

`POST /api/agent/<Agent>` is **unauthenticated**, and a body that loads a shell agent
(e.g. `RemoteControl`) exposes **arbitrary remote code execution** — one request is
fleet-wide RCE. The reference design is **LAN-only, trusted-subnet-only**. Do NOT
expose a body's port beyond a trusted network. Recommended hardening (not in v1.0):
a shared-secret header on `/api/agent`, a per-agent allowlist, and TLS.

## 9. Versioning

This is **SPEC v1.0**. The contract in §2 is the stable surface. Additive fields on
the JSON envelopes are backward-compatible; a controller MUST ignore unknown fields.
Breaking changes bump the major version. The status taxonomy (§3) is frozen for v1.

---

*One mind, many bodies. The mind thinks; the bodies execute and record; nothing
between them needs to think. That is the whole protocol.*
