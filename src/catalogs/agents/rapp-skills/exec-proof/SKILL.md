---
name: exec-proof
description: Pre-demo smoke test — verify the install/demo path works on a machine that is NOT this one, exactly as a first-time user would run it, before anyone runs it live. Use before demos, customer sessions, or offsites; whenever the user says "exec proof this", "will this work on their machine", "smoke test the install", "demo tomorrow", or after any live-demo failure ("it broke in front of..."). The deliverable is a GO / NO-GO verdict with evidence, per platform.
---

# Exec-proof: never break in front of an executive again

This skill exists because the RAPP installer broke live, in front of an executive, on Windows, three separate times. Root cause each time: the flow was only ever tested on Kody's Mac, where everything is pre-installed, pre-authenticated, and already running. The test that matters is the one that simulates the exec's machine, not this one.

## The iron rule

**Test the documented command, copied verbatim from where the user will read it** — the README, the landing page, the slide. Never test the command from memory or from the repo checkout; the exec doesn't have the repo. If the docs say `curl -fsSL https://.../install.sh | bash`, fetch THAT URL and run THAT pipe.

## Step 1 — Enumerate the advertised paths

Scrape the actual user-facing surfaces (landing page, README, deck notes) for every install/run command shown. For each, note the claimed platform. Known live example of the failure class: the rapp-installer page advertises `install.ps1` / `iex` for Windows while that URL 404s — a doc-vs-artifact mismatch invisible from a working machine.

## Step 2 — Verify artifacts exist before verifying they work

For every URL in an advertised command: `curl -fsSL -o /dev/null -w "%{http_code}"` it. A 404 here is an instant NO-GO for that platform — report it before doing anything else.

## Step 3 — Clean-environment run (the platform you're on)

Simulate a fresh user, not a fresh universe:
- Run in a scratch HOME: `env -i HOME=$(mktemp -d) PATH=/usr/bin:/bin:/usr/local/bin bash -c '<documented command>'` — this exposes dependencies on your dotfiles, your `~/.local/bin`, your cached auth tokens, your already-running servers.
- If Docker is available, a bare `ubuntu` or `debian` container is the gold standard for the curl-pipe path.
- Verify the END STATE the demo needs, not just installer exit 0: server answers on its port, page loads, agent responds. Check the port is handled when something already listens on it ("Address already in use" on 7071 was one of the live failures — the installer must either kill/reuse or pick a port, not stack-trace).

## Step 4 — Windows audit (when the demo machine is Windows and you're not)

You can't execute PowerShell here, so audit statically — these are the recurring killers:
- Is there a real PowerShell one-liner (`iwr ... | iex`) and does its URL return 200? `| bash` does not exist in PowerShell; a bash-only installer plus a Windows exec is a guaranteed live failure.
- Scan any .ps1/.cmd for: `python3` (Windows has `py`/`python`), hardcoded `/Users/` or `~` paths, `chmod`, CRLF-sensitive heredocs, `gh`/`git`/`curl` assumed present, execution-policy blocks (needs `-ExecutionPolicy Bypass` in the one-liner).
- If no Windows path exists at all, the verdict is NO-GO for Windows demos and the report says exactly what to build.

## Step 5 — The re-run test

Run the documented command a SECOND time immediately. Execs retry when something looks stuck. Re-running must be idempotent: no port conflict, no "already exists" crash, no duplicate server.

## Step 6 — Report: GO / NO-GO per platform

```
macOS   : GO   — verbatim command verified in clean HOME, server up, re-run idempotent
Windows : NO-GO — install.ps1 404s; page advertises it. Fix: publish install.ps1 or remove the claim.
```
Every NO-GO gets the exact failing command, the exact output, and the one-line fix. If everything passes, say GO plainly — no hedging. If anything is unverifiable from this machine, it is listed as UNVERIFIED, never assumed GO — that assumption is how the exec incident happened.
