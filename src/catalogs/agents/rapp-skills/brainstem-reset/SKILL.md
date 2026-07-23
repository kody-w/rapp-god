---
name: brainstem-reset
description: >
  Fresh-install test of the RAPP brainstem exactly as a first-time user would get
  it: kill the running service, archive and clear ~/.brainstem, VERIFY it is
  actually gone, reinstall from the public one-liner, and verify the new install
  answers on :7071. USE THIS SKILL when Kody says: "fresh install the brainstem",
  "test the installer", "wipe the brainstem and reinstall", "clean brainstem test",
  "does the public install still work", or before any demo where someone else will
  run the installer. Pair with exec-proof for testing on a machine that is NOT
  this one.
---

# brainstem-reset — verified fresh-install loop

Every stage has a verification step because half-done resets have shipped twice
("then why is it still running?" / "why do I still see the files?"). Do not report
a stage complete without its check.

## Stage 1 — Stop the service, prove it stopped

- Find it: `lsof -ti :7071` (the brainstem owns port 7071 by convention).
- Kill the PID(s), then RE-RUN `lsof -ti :7071` and require empty output.
- Also check for a launchd/loop wrapper that respawns it (`ps aux | grep -i brainstem`)
  — killing the child while a supervisor respawns it is exactly the "why is it
  still running" failure.

## Stage 2 — Archive, then clear, then prove it cleared

- NEVER plain `rm -rf ~/.brainstem` first. Archive:
  `mv ~/.brainstem ~/.brainstem.midden.$(date +%Y%m%d-%H%M%S)`
- The midden preserves custom agents, memory, and auth tokens for recovery.
- Verify: `ls ~/.brainstem` must fail (no such directory). If anything recreated
  it between the mv and the check, find what did (see supervisor note above).

## Stage 3 — Reinstall from the PUBLIC path only

- Use the public one-liner exactly as a stranger would (aka.ms/rappinstall — the
  canonical command is in the kody-w/RAPP README; read it fresh, do not
  reconstruct it from memory).
- Run it in a clean shell. Do not pre-create directories, do not copy anything
  from the midden yet — the point is testing the installer, not restoring state.

## Stage 4 — Verify the new install

1. Service up: port 7071 answers.
2. `GET /models` returns the model list (or `POST /chat` with a trivial prompt
   returns a real response).
3. Agents loaded: the chat response or startup log shows the default agent roster.
4. Version: report what version/commit the installer delivered.

## Stage 5 — Auth recovery (the known post-reset failure)

A fresh install often lands "Not authenticated" because tokens were wiped. The
fix is NOT /login: copy the freshest `.copilot_token` / `.copilot_session` from
a prior install backup (e.g. the midden made in Stage 2) back into the kernel
location, then re-verify Stage 4. If that recovers it, note it in the report —
it means the public installer still has the first-run auth gap a stranger would
hit, which is itself a finding.

## Stage 6 — Restore (only if asked)

If Kody wants his custom agents back, copy them from the midden's agents/
directory into the fresh install and verify they load. Otherwise leave the fresh
install pristine and tell him where the midden is.

## Report

GO / NO-GO for a first-time user, per stage: what was killed, what was archived
(path), installer output summary, verification results with the actual /chat
response quoted, and any gap a stranger would hit (auth, missing deps, port
conflicts).
