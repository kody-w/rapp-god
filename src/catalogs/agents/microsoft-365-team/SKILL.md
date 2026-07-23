# Microsoft 365 Team — feed this to your LLM

> **You (the LLM) are reading this because the operator wants you to set them up with the Microsoft 365 Team neighborhood.** Treat every instruction below as load-bearing. Do not improvise the boundary rules. Always ask for confirmation before irreversible commands.

This file is self-contained. You do not need to fetch anything from the internet to follow these instructions.

---

## Section 1 — What you're looking at

The operator has a directory on their machine (received via git clone, sneakernet egg, AirDrop, USB) containing the planted **Microsoft 365 Team** neighborhood — a workflow + tooling pack governed by `CONSTITUTION.md` in this same directory.

Your job: get the operator from "fresh state" to "neighborhood loaded, ready to use" without violating any constitutional rule.

---

## Section 2 — The boundary you MUST honor

Read `CONSTITUTION.md` first. The most load-bearing for setup:

- **Article I (Local Device Is Canonical):** Customer/project data lives ONLY at `~/.brainstem/neighborhoods/microsoft-365-team/<handle>/customers/`. NEVER `git add` anything customer-specific. The repo's `.gitignore` excludes `.brainstem/`; respect that.
- **Article IV (Sha256-Pinned Workflow):** When you install agents from `rar/index.json` you MUST verify each agent's sha256 matches the manifest. If a hash mismatches, refuse to install — surface the error.
- **Article VII (Sneakernet-Portable):** ONE agent does everything. Do not run shell commands; do not ask the operator to. Drag-drop + chat only.
- **Article VIII (Operator-Mediated):** Never `git commit` or `git push` on the operator's behalf without explicit confirmation.

---

## Section 3 — The setup, in one chat

The operator has the bootstrap agent (`egg_hatcher_agent.py`) in their brainstem `agents/` directory. To set them up:

If they have a `.egg` file:

```
EggHatcher from_egg=/path/to/microsoft-365-team.egg
```

If they have access to the repo online:

```
EggHatcher from_repo=kody-w/microsoft-365-team
```

That single chat does EVERYTHING:

1. Detects the operator's handle (gh / env / arg).
2. Unpacks the .egg (or clones the repo).
3. Sha256-verifies + installs every workflow agent into the brainstem.
4. Mints the operator's rappid (idempotent).
5. Mints the operator's per-handle workspace (front door + local data dir).
6. Records the subscription.
7. Returns "you're ready" with a next-step pointer.

NO second chat. NO shell commands. NO config edits. The operator is done.

---

## Section 4 — Demonstrating the workflow

Once setup completes, walk the operator through ONE engagement to prove it works:

```
EngagementFactory slug=hello-world customer_name="Test Co" ask="we want to test the workflow"
```

Then render the dashboard:

```
DashboardRender
```

This writes `~/.brainstem/neighborhoods/microsoft-365-team/<handle>/dashboard.html`. Tell the operator to open `file://<that-path>` in their browser.

If both calls succeed, the workflow is wired correctly.

---

## Section 5 — What you (the LLM) MUST NOT do

- Do not commit or push without explicit operator confirmation.
- Do not write customer data into the repo.
- Do not skip sha256 verification.
- Do not modify any `*_agent.py` in this repo — they're sha256-pinned.
- Do not improvise extra setup steps. ASK rather than do.
- Do not ask the operator to run shell commands. EggHatcher handles everything.

---

## Section 6 — Done condition

Setup is complete when:

- [ ] Brainstem is running locally with the neighborhood agents loaded.
- [ ] `~/brainstem-workspace/microsoft-365-team/` exists with the workspace contents.
- [ ] `ses/<handle>/` exists in the workspace with the operator's front door.
- [ ] `~/.brainstem/neighborhoods/microsoft-365-team/<handle>/customers/` exists locally.
- [ ] `EngagementFactory` produces a working engagement against a test slug.
- [ ] `DashboardRender` produces a viewable HTML file.

When all six are checked, hand control back with a one-paragraph summary.

---

## Provenance

- This skill ships with the Microsoft 365 Team neighborhood.
- Authority for the boundary: `CONSTITUTION.md` in this same directory.
- Authority for the agent contract: kernel constitution + `pages/docs/rapplication-sdk.md`.
