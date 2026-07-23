# rapp-burrow/1.0 — the Organ-Rapplication pattern (burrow + control room)

> An **organ-rapplication**: a drop-in RAPP brainstem organ that PULLS a PWA from a global repo and
> serves it LOCALLY, giving the operator visibility + control. This repo is the global home of the
> Burrow rapplication's PWA; the organ (`burrow_agent.py`) lives in any brainstem's `agents/`.

| field | value |
|---|---|
| spec_id | `rapp-burrow/1.0` |
| layer | distribution |
| home | [kody-w/rapp-burrow](https://github.com/kody-w/rapp-burrow) |
| organ | `burrow_agent.py` (drop-in `*_agent.py`) |
| depends on | `rapp-agent/1.0` (kernel), `rapp-static-api/1.0` (the repo-IS-the-API convention) |

## The pattern (three layers)
1. **Burrow (persistence).** The organ installs a launchd LaunchAgent — `RunAtLoad` + `KeepAlive{SuccessfulExit:false}` + `LimitLoadToSessionType=Aqua` (GUI session, for Messages/FDA) + the **exact interpreter binary** (FDA pins to the binary, not the script). Burrowing the brainstem persists EVERY organ in `agents/` with it.
2. **Rapplication (UI).** The organ pulls `burrow.html` (+ `manifest.json`/`sw.js`) from this repo and serves it on a local port; an installable PWA.
3. **Control Room.** The organ aggregates sibling organs over the brainstem's own `/api/agent` route into ONE PWA control surface — live status + enable/disable + observe/live toggles.

## macOS deployment notes (hard-won)
- FDA is granted to the **binary**, not the plist/script; a Homebrew python upgrade silently breaks it.
- "Local Network" privacy can block LAN inbound to a launchd-spawned process even when localhost works.
- Sleep is the #1 cause of a missed channel; `setsid` does not exist on macOS (use a LaunchAgent).

## Compliance (RAPP canon)
Drop-in `*_agent.py`; **zero kernel edits**; capabilities ride `/chat` + `/api/agent` (Art. XXV — chat is the only wire); runtime state in `.brainstem/`. The local control surface binds the LAN — gate it behind the Phase-1 fleet-auth before any off-LAN exposure (`rapp-roadmap`).
