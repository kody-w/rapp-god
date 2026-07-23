# Neighborhood Example — Neighborhood Constitution

This is the constitution of **Neighborhood Example**. It governs only this neighborhood — it does not amend the kernel constitution at [kody-w/RAPP/CONSTITUTION.md](https://github.com/kody-w/RAPP/blob/main/CONSTITUTION.md).

The articles below are the load-bearing rules every joined brainstem honors. Conformance is enforced by sha256 pinning in `rar/index.json`, by `.gitignore` for the data boundary, and by the workflow agents themselves.

---

## Article I — The Local Device Is Canonical

Customer / project data lives **only** at `~/.brainstem/neighborhoods/neighborhood-example/<handle>/customers/<slug>/` on the operator's own device. The repo holds *bones* (workflow agents + sanitized per-operator `projects.json`); the device holds *substance* (PII, contracts, technical specifics, attachments).

**Enforcement:** the workspace's `.gitignore` excludes `.brainstem/`. `git add` of any path under that directory fails by construction.

**Implication:** if your laptop is the only device with the local data dir and the laptop is lost, that data is permanently gone. Back up `~/.brainstem/neighborhoods/neighborhood-example/` yourself.

---

## Article II — Per-Operator Front Doors

Each operator has their own `ses/<handle>/` directory in the repo, minted by `SesWorkspaceInit`. The front door holds:

- `front_door.md` — who the operator is at the team level
- `projects.json` — list of project **slugs** + status enums + last-touched timestamps. **No customer data.**
- `soul_overlay.md` — optional voice/disposition overlay for this operator's Twin

Front doors are sanitized by construction.

---

## Article III — Outcome Before Build

No build work begins on an engagement until `OutcomeFramer` has produced an outcome statement. The why-first gate is non-negotiable.

`EngagementFactory` enforces this by always running the framer as part of starting an engagement.

---

## Article IV — Sha256-Pinned Workflow

Every agent ships in `rar/index.json` with a sha256 hash. `EggHatcher` (the universal bootstrap) **refuses** to install any agent whose bytes don't match the manifest. There is no override.

**Implication:** the neighborhood owner updates an agent → must re-run the factory to refresh `rar/index.json` with the new sha256. Until they do, joining brainstems either keep the old version or refuse to install. Prevents silent agent drift across the team.

---

## Article V — Nothing Closes Without Validation

An engagement closes only after `OutcomeValidator` has signed off. The validator confirms the delivered evidence matches the framed outcome's KPIs and that the named owner has approved.

The validator's archive is the canonical record of what shipped.

---

## Article VI — Two Surfaces, One Source of Truth

Every workflow agent is callable from two places:

1. **Through `/chat`** — the LLM-routed conversational surface.
2. **Through the dashboard rapplication** — the deterministic static-input surface (`DashboardRender` calls the agents with hardcoded params).

Both surfaces call the same `*_agent.py` files. There is no duplicated logic. Per kernel rapplication-sdk.md ("Best practice: agents drive both UI hydration AND chat").

---

## Article VII — Sneakernet-Portable

This neighborhood obeys the kernel's sneakernet portability invariant: a peer can receive this entire workflow as exactly TWO files — `egg_hatcher_agent.py` + a `<neighborhood>.egg` — and bring it up in their own brainstem with two actions only (drag the .py, send one chat). No shell commands, no follow-up configuration.

The bootstrap agent (`EggHatcher`) is multi-mode: it handles `from_egg` (sneakernet), `from_repo` (online clone), `pack_egg` (lay a fresh egg from current state for re-sharing), and `status` (probe).

---

## Article VIII — Operator-Mediated, Always

No agent in this neighborhood writes to the public internet, opens external connections beyond GitHub for git operations, or commits + pushes on the operator's behalf without explicit consent.

Agents propose; humans dispose.

---

## Amendment process

1. PR against this `CONSTITUTION.md` from a member of the team.
2. Sign-off from the neighborhood owner (`members.json` `role: "owner"`).
3. Bump of the constitution's `_version` in the next commit message.

Currently `_version: 1.0` (planted at neighborhood creation).

---

## Authority

- Repo: `kody-w/neighborhood-example` (set when the factory plants)
- Rappid: see `rappid.json`
- Members: see `members.json`
- Workflow agents: see `rar/index.json`
- Kernel constitution: https://github.com/kody-w/RAPP/blob/main/CONSTITUTION.md
