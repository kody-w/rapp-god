---
name: demo-ship
description: >
  Deploy the current agents to the cloud function, prove them end-to-end against the
  LIVE endpoint, generate the M365-styled HTML demo page, pop it open, and notify.
  One verb for the whole chain — never hand work back unverified. USE THIS SKILL when
  Kody says anything like: "upload to the function and test", "deploy and give me the
  demo", "push the latest to the function then test", "give me the demo page / test
  script / html walkthrough", "so I can test", "pop open the demo", "run the demo
  script against the cloud", or names a customer demo that needs to be live-testable.
  Also use for the local variant ("pop it up locally so I can test here").
---

# demo-ship — deploy, prove, package, open, notify

The contract: **work is never handed back unverified.** This skill ends with a demo
page open in the browser, an e2e transcript proving the cloud endpoint answered
correctly, and a ding + iMessage. If any stage fails, fix and re-run that stage —
do not present a partially verified demo.

## Stage 1 — Deploy

Target is the shared function app unless another is named:

- Function app: `<function-app>` (sub `<subscription-id>`, RG `<resource-group>`), model `gpt-5.2-chat`.
- Account: your work account (NOT a guest identity, NOT a personal account). Refresh
  with `az login --tenant <tenant-id>` if tokens are stale.
- Deploy: `cd rapp_ai && func azure functionapp publish <function-app> --build remote`
- If the cloud returns 503 after deploy: tenant policy may have flipped storage
  `publicNetworkAccess` off again on the function's storage account — run
  `az storage account update -n <storage-account> -g <resource-group> --public-network-access Enabled`
  and restart the app. Check this FIRST on any 503, before diagnosing code.
- Local variant: `cd rapp_ai && func start` on **port 7072** (7071 is reserved for the
  brainstem). Consumers read `RAPP_AI_PORT` / `RAPP_AI_URL`.

## Stage 2 — Prove it end-to-end (non-negotiable)

Run the demo script / e2e test against the endpoint YOU just deployed (cloud URL for
cloud deploys — never claim cloud readiness from a local run):

- Get the function key yourself (`az functionapp keys list` with the subscription
  pinned); do not ask Kody for creds that are already in `local.settings.json` or az.
- Drive the REAL conversation flow the demo uses, in order, one agent call per turn
  (step-wise demo rule: the orchestrator calls ONE connected agent per turn, verbatim,
  then stops).
- Check `agent_logs` in every response — a plausible `assistant_response` with faked
  tool results is a FAIL (gpt-4.1-class models fabricate tool output).
- If the demo has a reset agent ("reset the demo"), run it first so the run starts
  from a clean state, and run it again at the end so Kody's first take is clean.
- Save the request/response transcript to the project's outputs folder; the final
  summary must quote at least one real response as evidence.

## Stage 3 — The demo page

Generate ONE self-contained HTML demo page (no external deps), following the house
demo pattern:

- M365 Copilot chat look; **up-arrow drives the script** (each press advances to the
  next scripted user turn), plus a per-step **copy-to-clipboard button** (clipboard
  survives Teams formatting; this is why the buttons exist).
- Attach-front / lookup-backend: if the flow involves an uploaded document, the page
  front-stages the artifact (downloadable, correct file type — PDFs stay PDFs, never
  silently converted) and the backend reads its bundled copy by name. Never pretend
  to read from a source the AI wouldn't have access to.
- Endpoint config at the top of the file: `RAPP_AI_URL` default to the deployed
  function, overridable, so the same page drives local and cloud.
- Style: match the demo's real palette. NO emojis anywhere. NO default magenta/purple
  AI gradient. Plain professional Microsoft look.
- Customer-facing hygiene: the page describes the end agents and customer value only —
  no RAPP/build/tooling talk, no other customers' project names.

## Stage 4 — Pop it open

Open the page (`open <file>` or the live URL) so it is on screen when Kody comes back.
If a repo/editor is part of the ask ("so I can demo from there"), open that too.

## Stage 5 — Notify

`afplay /System/Library/Sounds/Glass.aiff` AND iMessage `<your-phone-number>` via
`osascript -e 'tell application "Messages" to send "<one-line status + what to click>" to buddy "<your-phone-number>"'`.
The message states what was deployed, that e2e passed (with the count of turns
verified), and what file/URL is open for him.

## Failure discipline

- A stage that fails gets fixed and re-run; the summary reports what failed and what
  the fix was. Never report "done" with a caveat buried below it.
- If deploy succeeds but e2e fails and the fix isn't obvious within a few attempts,
  STOP, leave the environment as-is, and report exactly which turn failed with the
  raw response — do not paper over it in the demo page.
- Never deploy from a dirty tree without committing locally first (feature branch is
  fine); the deployed artifact must be reproducible from a commit.
