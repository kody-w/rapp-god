---
name: mcs-deploy
description: >
  Take a built Copilot Studio solution (or build one from agent.py files first),
  import it with a FRESH version name, publish in the correct order, verify it
  actually answers, and hand back the maker-portal link. Never asks Kody for creds
  that live in local.settings.json. USE THIS SKILL when Kody says: "deploy it to
  copilot studio", "deploy the vN so I can test", "import the solution", "publish
  the bots", "test it over direct line", "make sure this copilot solution actually
  does what it says", or asks for a fresh install of a solution.
---

# mcs-deploy — solution import, publish, and real verification

The contract: the deploy is not done until a bot in the target environment has
answered a real question, or the exact blocker is reported with the raw error.

## Stage 0 — Build (only if no zip was provided)

If Kody points at agent.py files instead of a zip, build via
`connected_agents/build_from_agents.py` (`build_solution_from_dir`) in the RAPP repo.
Validate with `validate_connected_solution` before importing anything.

## Stage 1 — Fresh version naming (always)

Kody iterates by fresh installs. Unless he says otherwise, bump the visible name
with the next suffix (v2, r3, ...) so the new import is unambiguous next to the old
one: check `pac copilot list` / the solution list for the highest existing suffix
first. Never reuse a name and hope the overwrite took.

## Stage 2 — Credentials (never ask)

App-registration creds are in the project's `local.settings.json`:
`DYNAMICS_365_CLIENT_ID`, `DYNAMICS_365_CLIENT_SECRET`, `DYNAMICS_365_TENANT_ID`,
`DYNAMICS_365_RESOURCE`. Use them for Dataverse Web API calls. For `pac`, use the
existing auth profile (`pac auth list`); only ask Kody to run `! pac auth create`
if no profile exists. Do not ask him to paste secrets — that is how seven ended up
in prompt history.

## Stage 3 — Import

- `pac solution import --path <zip> --async --force-overwrite`
- Or Dataverse Web API when pac auth is unavailable. Prefer an **in-place
  botcomponent PATCH** when only bot content changed — it preserves existing
  Direct Line secrets, so channel configs do not need rebinding.
- Connection references must be bound by the maker on first import of a new
  solution — say so in the handoff rather than silently leaving them unbound.

## Stage 4 — Publish (order is load-bearing)

- Publish the SUB-AGENTS FIRST, the ORCHESTRATOR LAST. A connected-agent root
  must have its children published before it, else publish 409s
  (ExternalServiceException).
- `pac copilot publish --bot <GUID>` per bot (GUIDs from `pac copilot list`),
  or PvaPublish via Web API, children first.
- **pac publish is the oracle.** A solution that zips and imports fine can still
  fail publish — most often literal `{braces}` anywhere Power Fx evaluates
  (display names, messages). If publish fails, look for braces first.

## Stage 5 — Verify (the part that gets skipped and then bites)

- Direct Line requires `authenticationmode = 1` (no-auth) on EVERY bot in the
  chain. Flip via Dataverse Web API (PATCH `bots`), then republish children-first.
- Known limit: **agent-to-agent delegation throws AuthenticationNotConfigured over
  anonymous Direct Line.** So: single-bot answers are verified over Direct Line;
  connected/orchestrator flows are verified in the **Test pane** — if you cannot
  drive the Test pane, give Kody the one specific question to type and what the
  correct answer looks like.
- A verification pass = at least one real question, real answer, quoted in the
  summary. "Import succeeded" is not verification.

## Stage 6 — Handoff

Report: solution name + version, environment, bots published (in order), what was
verified and how, and the direct maker link
(`https://make.powerapps.com/environments/<env-id>/bots`). If connection
references need manual binding, that is the first line of the handoff, not a
footnote.
