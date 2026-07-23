---
layout: post
title: "Same wire contract, three implementations"
date: 2025-10-30
tags: [architecture, wire-protocols, portability, deployment]
---

The chat host talks to its agent-pack endpoints over plain HTTP + JSON. There are exactly two endpoints in the wire contract:

```
POST /api/pack/deploy         body: pack/1.0 bundle           → {pack_guid, pack_url}
POST /api/pack/{guid}/agent   body: {name, args, user_guid?}  → {status, output}
```

(Plus `GET /api/pack/healthz` and `/api/pack/{guid}/healthz` for inspection. Five lines if you count those.)

That contract is enough to build three completely different agent-pack endpoint implementations. One ships today; two are sketches.

**Implementation A: stdlib local server.** Already shipped. ~300 lines of Python with `http.server.HTTPServer`. Persists packs to a local directory. No dependencies. Installs in 10 seconds via a one-line shell command. This is the laptop / dev / single-machine story.

**Implementation B: serverless functions (e.g. Azure Functions).** Same wire contract, different backing storage. Persists packs to a managed file share instead of local disk. Routes via the same `(pack_guid, user_guid)` tuple but the path becomes a `memory/{guid}/...` blob path inside a cloud share. The agent execution code is shared with the local implementation — they both load `*_agent.py` files and call `perform()`. The difference is where the bytes live.

A typical cloud-functions runtime already provides the underlying primitives (a file storage manager, a memory-context setter). Wrapping them in a `/api/pack/deploy` endpoint that writes agent files to a pack namespace is small additional code on top.

**Implementation C: edge functions (e.g. Cloudflare Workers + Durable Objects).** Edge-deployed pack endpoint. Each pack gets a stateful object instance that holds its agents and routes calls. Agent execution would either:

- Call out to a separate Python runtime (a sandboxed worker, or a small VM).
- Compile agents to JS via Pyodide running inside the worker (heavyweight but possible).
- Restrict pack endpoints to non-Python "agents" (web fetches, simple computations) — a degraded mode that's still useful.

The C implementation is hypothetical right now. The interesting thing is: implementations A and B are concrete enough that we could build C without any wire-protocol changes. The chat host doesn't know which it's talking to.

**What this buys:**

- **The chat host doesn't change.** A user picks a pack endpoint URL; whether that's `localhost:7080` (A), `https://my-pack.azurewebsites.net` (B), or `https://my-pack.workers.dev` (C) doesn't matter. Same `POST /api/pack/deploy`.

- **Bundles are portable.** A pack bundle generated for implementation A installs on B without changes. Same JSON, same agent files, same install path.

- **Implementations can specialize.** A is fast for one user with private data. B is right for teams sharing memory. C is right for "I want my pack reachable from anywhere with low latency." User picks per use case.

**What it costs:**

- **Coordination.** Three implementations means three places to change behavior when the wire contract evolves. We try to keep the contract small for exactly this reason. (Two endpoints. Two HTTP verbs. One JSON schema.)

- **Capability divergence.** Implementation C might not be able to run arbitrary Python; A and B can. Users who want full capability have to know to pick the right backend. Documenting the matrix matters.

- **Testing.** Each implementation needs its own test suite verifying it speaks the contract correctly. We have one for A. We don't have one yet for B or C because we haven't built them.

**The principle:**

When you design a wire contract, design it so multiple backends can plausibly implement it. Don't bake in assumptions about storage layer, runtime, or scale. Two HTTP endpoints with JSON bodies and a tiny path namespace can carry an entire product. The implementations underneath get to be wildly different — local stdlib, cloud functions, edge workers — without any of them needing to know the others exist.

The chat host doesn't care which pack backend it's talking to. That's the whole point.