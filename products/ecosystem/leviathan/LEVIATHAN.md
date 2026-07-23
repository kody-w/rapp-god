# The Leviathan

**One mind, many bodies.** Claude is the only intelligence in the system. The LAN
brainstems are interchangeable, **no-LLM executors** reached only through their
`POST /api/agent/<Agent>` route (installed by `FlockEndpoint`). `leviathan.py` is
the controller's nervous system — a **control plane that never thinks and never
runs a server**. It reaches into a body, runs one named agent's `perform()` over
the direct route, and hands back a clean, uniform `Result`.

The surface collapses to the model the mind already thinks in: **`one(body)`** and
**`all(bodies)`**. "Flow Claude through the brainstems" becomes a single readable line.

**Why it exists:** the old way (`POST /chat`) made each node's *own* LLM decide
which agent to run, on a shared Copilot token — which serialized the whole fleet
to ~1 op/hour under throttle. The Leviathan path touches no LLM and no token, so a
fan-out completes in ~`max(node latency)`. The throttle wasn't managed; it was
*designed out*.

> **Prime directive — failure is data, never an exception.** A down node, a missing
> agent, a slow call, a half-reachable fleet, a body whose `/chat` is dead: all are
> NORMAL outcomes returned as data. Every call → one `Result`. Every fan-out → a
> COMPLETE per-node map. The library decides nothing; the one mind reads the map and decides.

---

## 1. The node contract it depends on

Each body runs `FlockEndpoint`, which adds (no LLM):

| Endpoint | Returns |
|---|---|
| `POST /api/agent/<Agent>` (JSON kwargs) | `200 {ok:true, agent, result}` · `404 {ok:false, error, available:[...]}` · `500 {ok:false, agent, error}` — POST/OPTIONS only |
| `GET /health` | `{copilot:"✓"|"pending", model, version, agents:[...]}` |
| `GET /agents` | `{files:[{filename, agents:[...]}]}` |
| `POST /agents/import` (multipart, field `file`, name `*_agent.py`) | hot-loads, no restart, no LLM |
| `DELETE /agents/<filename>` | removes an agent |

Two gotchas the controller handles for you: the inner `result` is itself a
JSON-encoded string (**double-JSON**, auto-decoded into `Result.value`), and a node
that's up but *without* FlockEndpoint returns Flask's HTML 404 → classified
`bad_response` (un-flocked), distinct from `missing`.

## 2. Quickstart

```python
import leviathan
leviathan.up()                                   # liveness/degrade board (Flock)
leviathan.sh('mac', 'hostname').out              # one body, shell -> stdout
leviathan.sh_all('uptime')                       # whole fleet, parallel (Flock)
leviathan.all('Base64', action='encode', text='hi')   # one agent, every body
leviathan.who('Rot13')                           # -> ['rapptertwo']  (where it lives)
leviathan.scatter([('mac','RemoteControl',{'command':'date'}),
                   ('windows','CopilotCLI',{'action':'list'})])  # heterogeneous wave
```
CLI mirrors the library 1:1:
```
python leviathan.py up
python leviathan.py sh all "uptime"
python leviathan.py one mac RemoteControl command=hostname
python leviathan.py all Base64 action=encode text=hi   [--json]
```

## 3. The roster

The roster maps logical names → IPs (the shipped default is a placeholder example;
`mac`/`windows` etc. below are illustrative). Override with `$HIVEMIND_NODES` (JSON)
or `~/.hivemind/nodes.json`. Adding a **body is one JSON edit, no code change.**
There is no discovery — a DHCP-moved body shows as
`down` until the roster is updated.

## 4. `Result` — the uniform per-body outcome

`bool(Result) == ok`. Fields: `node, ip, agent, ok, status, value, raw, error, http,
available, ms`. Conveniences: `.rc/.out/.err` (for `RemoteControl`), `.as_json()`,
`.summary()`, `.to_dict()`. Repr is one glanceable line: `Result(mac/RemoteControl ok 42ms)`.

**Closed status taxonomy — the join key for every decision:**

| status | cause | retry? |
|---|---|---|
| `ok` | 200 + envelope `ok:true` | — |
| `down` | connection refused / DNS / no route — provably **undelivered** | **yes, safe** |
| `timeout` | socket timeout or gather deadline — *may* have run server-side | **no** |
| `missing` | 404 JSON `{available}` — FlockEndpoint present, this agent absent | re-route/deploy |
| `error` | 500 / envelope `ok:false` — the agent's `perform()` raised | depends |
| `bad_response` | reachable but not flocked (HTML 404, non-JSON 2xx, 405) | install FlockEndpoint |

## 5. `Flock` — the fan-out aggregate

**Hard invariant:** exactly one `Result` per requested node, keyed by logical name —
never dropped, never an ip, never deduped. A totally-down fleet yields N
`Result(status='down')`, never an empty dict, never an exception. Surface: `.ok`
(all), `.any`, `.alive`/`.fails`, `.values`, `.errors`, `.counts`, index by node
(`flock['mac']`), iterate, aligned-table repr, opt-in `.raise_for_status()`.

## 6. Primitives

`one` · `all`/`fan` · `scatter` (heterogeneous) · `sh`/`sh_all` · `up`/`health` ·
`agents` · `who` · `route` (strategy `all`/`any` with failover) · `deploy`/`forget`
(fleet-wide rollout, local `compile()` check first) · `pick` (scope to a sub-fleet,
chainable: `lev.pick('mac','windows').sh_all('uptime')`). All bind to a default
singleton `leviathan`, so `leviathan.all(...)` and `Leviathan(...).all(...)` are the same.

## 7. Concurrency

Stdlib only: a shared, lazily-created `ThreadPoolExecutor` + `urllib` (blocking
socket I/O releases the GIL → real wall-clock parallelism). Each fan-out leg owns
its full lifecycle (own request, own per-call timeout, own try/except → a `Result`),
so the gather is lock-free. The result map is **pre-seeded** with `down` placeholders
and drained under an overall deadline, so one hung body can never stall the aggregate
and the Flock is **always** a complete per-node map.

## 8. Failure & routing

Retry `down` (undelivered); **never** retry `timeout` (unknown outcome) or a
non-idempotent `sh`. Topology is a *hint*; the per-call `Result` is *truth* —
`who()`/`route()` pre-route to live holders, and `route(strategy='any')` fails over
on `down`/`timeout`.

## 9. Recording — the body is accountable

`FlockEndpoint` flight-records **every** `/api/agent` call into the standard Flight
Recorder store (`~/.brainstem/flight_recorder/<date>.jsonl`), tagged
`caller="hivemind", channel="api/agent"`, with `user_input`/`response` for recorder
search/export compatibility. It respects the recorder's enable flag. So the
Leviathan's every action is on the record regardless of which controller drove it —
the digital estate is preserved even though the hivemind path bypasses `/chat`.

## 10. Security & trust boundary

`/api/agent` is **unauthenticated** and `RemoteControl` is arbitrary shell — i.e. a
one-line **fleet-wide RCE**. This is **LAN-only, trusted-subnet-only**. Never expose
a body's port beyond the trusted network. Future hardening: a shared-secret header
+ per-agent allowlist on `FlockEndpoint`.

## 11. Operational guidance

- **Fan only no-LLM agents.** A deployed agent whose `perform()` itself calls the
  node's Copilot LLM re-introduces the shared-token throttle — keep `all`/`scatter`
  targets to no-LLM agents (`RemoteControl`, the utility/foundry agents). Long LLM
  work goes through `CopilotCLI` (dispatch → poll `job_id`), not a hivemind await.
- **Heavy/keychain-sensitive broadcasts** (git push, auth) saturate the macOS
  keychain at ~16 concurrent — run in **waves of 3-5** via `max_workers`/`nodes=`.
- **Cap `sh` stdout** for chatty commands; the Result keeps the tail.

## 12. Limitations & future

No discovery/mDNS, no streaming, threads aren't cancellable (a per-call timeout +
bounded pool contain a hung body), no auth yet. Growth past a handful of bodies
wants a circuit-breaker (drop chronically-dead nodes from fan-out) and chunked waves.

---

*The Leviathan is the full shape of the thing: one mind, many recorded no-LLM
bodies, driven directly. It works while a body's `/chat` is dead. It cannot throttle
itself. And everything it does, it writes down.*
