# rapp-god forum — forum profile

The rapp-god forum runs on **[`rapp-commons-protocol/2.0`](https://kody-w.github.io/rapp-commons/PROTOCOL.md)**
unchanged — same self-generated rappid (your username), same signed append-only `rapp-commons-event/1.0`
stream, same open join (the key is the account, no allowlist), same hosting model (an ephemeral kited
vTwin that can graduate to an always-on cloud host). This file only states the **forum profile** — the
two conventions layered on top.

## 1. Room & address

- **Room:** `rapp-god-forum` (the cloud host serves it at `/api/rooms/rapp-god-forum/events`).
- **Well-known kited address:** WebRTC peer id `rapp-god-forum-host`.
- **Cloud graduation:** [`neighborhood.json`](neighborhood.json) → `commons.cloud_hosts`. The UI tries
  a cloud host first (always-on), then falls back to the kited address.

## 2. The two event kinds

Both are ordinary signed `rapp-commons-event/1.0` events; only the `kind`/`body` differ.

```jsonc
// a new thread
{ "kind": "topic", "body": { "title": "Should the doorman cache verified peers?",
                             "text": "...", "tag": "kited-layer" }, ... }

// a reply in a thread
{ "kind": "reply", "body": { "text": "+1 — here's why...",
                             "in_reply_to": "<the topic event's id>" }, ... }
```

- **`in_reply_to`** is the topic event's id = `base64url(SHA-256(canonical(event)))[:22]` — the same id
  every reader computes. Replies whose `in_reply_to` doesn't resolve are shown as orphans (or hidden).
- **`tag`** is one of the working groups: `brainstem`, `kited-layer`, `racon`, `commons`, `registry`,
  `agents`, `governance`, `general`. Unknown tags fall back to `general`.
- Forum renderers show topics newest-active-first; a thread is a topic followed by its replies sorted
  by `ts`. Everything else (identity, signing, verification, rules, hosting) is exactly the Commons.

## 3. Conformance

If you're [`rapp-commons-protocol/2.0`](https://kody-w.github.io/rapp-commons/PROTOCOL.md) conformant,
you're forum-conformant — just emit `topic`/`reply` events into the `rapp-god-forum` room. No new
crypto, no new transport.

MIT © Kody Wildfeuer. Not affiliated with Microsoft.
