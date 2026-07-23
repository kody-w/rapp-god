---
layout: post
title: "Endpoints without buttons: when the backend keeps a feature the UI forgot"
date: 2026-04-26
tags: [engineering, ui, api-surface, refactoring, voice]
description: "A server had five voice-mode endpoints, a config format, an export/import flow, and a response field carrying the spoken line. The new UI shipped without a single voice button. The feature was alive on one side and invisible on the other for a full release cycle."
---

The tell was a JavaScript handler that did this:

```js
if (kind === 'toggle' && target === 'voice') {
  const btnVoice = document.getElementById('btn-voice')
    || document.querySelector('[data-toggle="voice"]');
  if (btnVoice) { btnVoice.click(); return; }
  throw new Error('voice toggle not wired');
}
```

It searches for a button. If the button doesn't exist, it throws "voice toggle not wired." Nobody had ever filed a bug for it because nobody could trigger it — the only thing that fired this path was an LLM-issued action tag, and the LLM had no incentive to issue one without provocation.

The button hadn't existed for an entire release cycle.

Meanwhile, the server still had:

- `GET /voice` — get current voice mode state
- `POST /voice/toggle` — flip voice mode on/off
- `GET /voice/config` — read the saved provider config
- `POST /voice/config` — write the saved provider config
- `POST /voice/export` — package the config as a password-protected zip
- `POST /voice/import` — accept a zip and apply it
- A `VOICE_MODE` env var with auto-init from `.env`
- A response splitter that pulled `|||VOICE|||` markers out of the model output and shipped the spoken line back as a `voice` field on every chat response

Five HTTP endpoints. A config format. A protocol. An import/export bundle. All live, all reachable, all tested by integration tests. Nothing on the frontend pointed at any of it.

## How this happens

It's a familiar shape, even if you've never built it: the frontend got rewritten, the backend didn't. The new UI was built greenfield from a different starting design. Voice mode wasn't on the list. It just got dropped — not deleted, not deprecated, not even discussed. The new UI shipped, the old UI got swapped out, and the backend kept doing its job for nobody.

The feature persists because:

1. **Backends are easier to leave alone than to rip out.** Removing the `/voice/*` endpoints would have meant explaining what was being removed, why, and whether anyone still depended on the response shape. The path of least resistance is to leave the routes registered and forget about them.

2. **The response contract still flows.** Every chat response carries `voice`, `twin`, `agent_logs`, etc. Consumers (other UIs, future UIs, scripts) pick the fields they want. Removing one field would be a breaking change. So the field stays, even if no current consumer reads it.

3. **System prompts still mention it.** The soul.md asked the model to emit a `|||VOICE|||` block. The model dutifully complied. The block was getting stripped, packaged, shipped — and ignored.

4. **An action handler still references it.** The orphan handler above is the only trace in the new UI. It's load-bearing in a way: it documents that the feature is supposed to exist. It's also load-bearing in a worse way: it gives a confident error message ("voice toggle not wired") that reads like a real diagnostic, but is in fact telling you nothing actionable until you go read the source.

## How long it stayed broken

Hard to know exactly. The orphan handler's error message went into the codebase in the rewrite. That's the upper bound. The lower bound is whenever the last frontend voice button got deleted, which by the look of the git history was around the same commit. So somewhere between "the rewrite" and "the rewrite + 1 day," the feature became invisible. It was invisible for the rest of the release cycle.

How did anyone notice? Someone asked for it back. Specifically: "add voice mode like the old UI had." That's the only signal that worked. Nothing in the test suite caught it (there are no UI integration tests). Nothing in the agent contract caught it (the contract is satisfied as long as the response carries the field). Nothing in the changelog caught it (the rewrite was a UI rewrite; voice wasn't called out as removed because it wasn't intentionally removed).

## What the fix looked like

Trivially small. The endpoints were still there. The response field was still there. The system prompt still asked for the spoken line. All that was missing was:

1. Two buttons in the header — a mic toggle and a settings gear.
2. A popover for provider selection (Azure, ElevenLabs, browser fallback) and credentials.
3. A `speakText()` function that called the appropriate provider's TTS API or fell back to `SpeechSynthesisUtterance`.
4. One line in the chat-response handler: `if (typeof speakText === 'function') speakText(resp.voice || resp.text);`

The reconstruction took less time than writing this post about it. Most of the work was lifting the chrome verbatim from the previous UI's git history. The wiring was three function calls.

## The lesson, if there is one

A backend feature without a frontend isn't a bug exactly — it's a *surface mismatch*. The feature works. The capability is reachable by anyone who knows the endpoint shape. But the user-facing path is gone. From a product standpoint the feature is dead; from a system standpoint it's healthy.

The mismatch is the thing to watch for, because the symptoms are easy to miss:

- **Backend integration tests pass.** The contract is intact.
- **Frontend code review doesn't flag it.** There's nothing in the new UI to review. The feature is conspicuous by its absence, but only if you remember the old UI well enough to notice.
- **Bug reports don't fire.** Users don't file bugs for missing buttons they can't see.
- **Telemetry doesn't fire either.** Nothing is hitting the endpoints, but you'd have to be specifically looking at "endpoints with zero traffic" to notice. Most dashboards are tuned to spot anomalies in the *positive* direction — too many requests, too many errors. Zero requests is the baseline; it doesn't trigger an alert.

The orphan action handler — the `if (btnVoice)` block above — is the closest thing to a built-in canary. It's a sentence in the source code that says "this should exist," falling silently until someone trips it. If you see a handler like that in your own codebase, treat it as a TODO with an attitude problem.

## Why I'm writing this down

Because the same pattern is going to show up in every system that has more than one frontend over time. The pattern is:

1. Backend ships feature X with full surface area.
2. UI ships consumer for X.
3. UI gets rewritten. New UI doesn't include X.
4. Backend still serves X to nobody.
5. Months later, someone asks where X went.

The defense isn't to delete X aggressively. (Sometimes the right move is to revive it — that's what happened here.) The defense is to **notice the asymmetry exists** and decide explicitly whether to keep, kill, or rebuild the surface. A feature in this state should never be in this state by accident.

A useful lightweight check, runnable in CI: list all backend routes, list all UI references to those routes, diff the lists. Routes with zero UI references go on a quarterly review list. Each one gets a one-line decision: *keep alive (other consumers exist), kill, or restore.* No route gets to live in limbo without somebody having said the words.

The voice feature spent a release cycle in limbo. The fix was easy because the backend hadn't rotted. Next time the rot will be worse, and the fix won't be a single afternoon.
