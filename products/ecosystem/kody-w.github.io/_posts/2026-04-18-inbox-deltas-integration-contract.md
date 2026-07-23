---
layout: post
title: "Inbox Deltas as the Integration Contract"
date: 2026-04-18
tags: [contracts, integration, deltas, api-design, simplicity]
---

The entire write surface of my platform is one shape:

```
{
  "action": "register_agent",
  "agent_id": "alice-001",
  "timestamp": "2026-04-18T16:00:00Z",
  "payload": { ... }
}
```

That's it. Anything that wants to mutate state writes a JSON file in this shape to `state/inbox/`. A processor picks the file up, validates the action, dispatches to a handler, applies the change. The handler is the only place that knows what `register_agent` actually does. Everything upstream — the issue template, the engine adapter, the test fixture, the SDK call — produces this same shape.

A four-field contract beats a big API for one reason: the surface area you have to defend is tiny. Four fields means four things to validate, four things to test, four things to document. A REST API with thirty endpoints has thirty surface areas. The next person to integrate has to learn thirty things. The next bug can hide in any of them.

What this buys, concretely:

- **Anything that produces JSON can integrate.** A GitHub Action. A Python script. A LisPy cartridge. A browser bookmarklet. A curl command. The contract is so small that any process anywhere can produce it.
- **Replay is trivial.** Inbox files are just files. Save them to a snapshot directory. Move the directory back into `state/inbox/` and the same mutations re-apply. Dry-run is just "process the inbox into a temp state tree."
- **Audit is automatic.** Every mutation that ever happened to the platform exists, in order, as a file with a timestamp. No special audit log needed — the inbox *is* the audit log.
- **Multiple writers serialize naturally.** Two engines both write inbox deltas. The processor handles them in lexicographic order (timestamp-prefixed filenames). No locking, no coordination protocol, no Raft.
- **Testing is mechanical.** The test fixture writes a delta file, runs the processor, asserts on state. There's no HTTP layer to mock, no auth to fake, no request body to construct. Just dict-to-JSON-to-file.

The opposite shape is a service interface where the writer calls a function on a server and the server mutates state directly. That shape is hard to make idempotent, hard to replay, hard to audit, hard to test, and requires both sides to be running at the same time. The inbox-delta shape is asynchronous by construction: the writer drops a file and walks away, the processor picks it up whenever it next runs.

The handler dispatcher is also small. A dict mapping action names to handler functions. The processor looks up the action, calls the handler with the payload and the relevant state slices, gets back either `None` (success) or an error message. Adding a new action is one new entry in the dict and one new function. No router, no middleware, no decorators.

The cost: the writer doesn't get an immediate response. They drop the file and check back later by reading state. For a system whose tempo is "frame loop running every few minutes," this is fine. For a synchronous request-reply system, you need something else.

Pick the cost. Either the writer waits, or the writer fires and forgets. If your domain tolerates the second, the inbox-delta contract is one of the highest-leverage architectural choices you can make.
