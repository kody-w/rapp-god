---
name: flex-unbrick
description: Unbrick an Azure Flex Consumption function app after a tenant security-policy sweep silently re-disables storage public network access (app 403/503s, PNA=Disabled). Runs the proven 2026-07-09 runbook — PNA check, SecurityControl=Ignore tag, re-enable PNA, full stop/start, bounded health poll.
disable-model-invocation: true
allowed-tools: Bash(az:*), Bash(curl:*), Bash(bash:*), Read
---

# flex-unbrick — the storage-PNA outage runbook as one verb

Root cause: a management-group policy silently flips the function app's storage
account to `publicNetworkAccess: Disabled`, which kills Flex Consumption apps.
The fix sequence was re-derived by hand once (169 az calls, 573-minute session) —
this skill replays it.

## 1 — Diagnose (read-only, always first)

```
bash ~/.claude/skills/flex-unbrick/scripts/unbrick.sh check <app> <rg> <storage>
```

Prints subscription, storage PNA state, app state, live HTTPS probe, and a
verdict line: `HEALTHY` / `DEGRADED` (classic PNA outage — fix applies) /
`DOWN-OTHER-CAUSE` (probe failed but PNA already Enabled — fix will NOT help).
The live probe is the truth: PNA=Disabled with a healthy probe is the
private-endpoint deployment shape, NOT an outage. If HEALTHY, stop — do not fix.

## 2 — Fix (mutating; only on a DEGRADED verdict)

```
bash ~/.claude/skills/flex-unbrick/scripts/unbrick.sh fix <app> <rg> <storage>
```

Order matters and is encoded in the script:
1. `SecurityControl=Ignore` tag on the storage account (merge, keeps other tags) — without it the policy re-disables PNA again within hours.
2. `--public-network-access Enabled` on the storage account.
3. FULL `az functionapp stop` then `start` — `restart` does NOT re-bind Flex storage.
4. Bounded health poll (20 × 15 s). HTTP 401/404 counts as recovered — an auth layer may 404 without its client-id env var; the metal being up is what we're testing.

## 3 — Aftercare

- If you have alert rules wired on the app (health check, app-down, storage-config-change), check them: a storage-config-change alert firing timestamps the policy sweep.
- If the app is still down after the poll: the problem is NOT this policy — go read Function App logs instead of re-running fix.

## Don'ts

- Don't run `fix` without a `check` first, and never on a HEALTHY verdict.
- Don't substitute `az functionapp restart` for stop/start.
- Don't remove the `SecurityControl=Ignore` tag "to clean up" — it is the thing keeping the app alive.
