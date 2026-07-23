# iMessage Profile — `rapp-messaging-imessage/1.0`

This profile maps `rapp-messaging/1.0` onto personal iMessage.

## Reference transport

The reference implementation supervises signed `imsg rpc` over newline-framed
JSON-RPC stdio.

- inbound: `chat.db` read-only;
- outbound: Messages Apple Events;
- no listening port;
- SIP enabled;
- no private IMCore requirement;
- no SMS fallback.

Tested reference version: `imsg 0.12.3`.

## Requirements

- per-user logged-in Aqua session;
- Messages signed into one account;
- Full Disk Access for the responsible process;
- Automation permission for Messages;
- one active writer per account;
- Developer-ID-verified transport binary.

## Routing

- owner self-chat: explicitly enrolled stable chat GUID;
- other DM: normalized sender bound to a principal;
- group: account-scoped chat GUID plus roster epoch;
- local numeric row ids: cursor/lookup only, never portable authority.

Groups are deny-by-default and mention-gated by default. DMs are pairing or
allowlist by default.

## Receive

Implementations MUST:

- watch the database and WAL through a read-only library;
- persist row cursor and GUID before asynchronous dispatch;
- resume before the minimum pending row;
- reject missing chat joins rather than emit an empty direct message;
- probe schema capabilities;
- decode modern attributed text safely;
- fail closed on unsupported attachment-only events.

## Send

Implementations MUST target an existing chat for group replies and force
iMessage service. They MUST NOT silently downgrade to SMS.

`send` acceptance is not remote delivery. If available, delivery/read state is
tracked separately.

Timeout or child loss after request flush is ambiguous and MUST NOT trigger an
automatic resend.

## Echoes

Suppress exact outbound GUIDs durably. A self-chat admits `is_from_me` only for
the enrolled owner chat and only when the event is not a recorded bot echo.

## Multiple Macs

Use one distinct iMessage account per Rappter. If one account appears on several
Macs, only one active writer is permitted.

## Reference

OpenRappter PR 28:

https://github.com/kody-w/openrappter/pull/28
