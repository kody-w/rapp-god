"""ses_workspace_init_agent — mint an operator's per-handle front door + local data dir.

Lives in the this neighborhood's rar/. After the joiner clones the
private repo, the operator runs this once to:

  1. Detect the operator's GitHub handle via `gh api user`.
  2. In the CLONED REPO at <workspace>/ses/<handle>/, create the operator's
     "front door" — front_door.md, projects.json (empty),
     soul_overlay.md. These hold sanitized metadata only (project slugs,
     status enums, sign-of-life). NO customer data.
  3. On the LOCAL DEVICE at ~/.bwat-data/<handle>/customers/, create
     the customer-data dir with a STRONG warning README ("never git add").
  4. Write a .gitignore in the workspace ensuring nothing under
     .bwat-data/ ever gets committed by accident.
  5. Stage the ses/<handle>/ files in git but DON'T commit/push — the operator
     reviews and pushes themselves (operator-mediated; nothing leaks
     without explicit consent).

Boundary: the REPO holds bones (workflow + sanitized project tracking
across the team). The LOCAL ~/.bwat-data/ holds the substance (customer
PII, contracts, financials). The pinger walks both — team-view from the
repo, personal-deep-view from local data.

Single-file agent. Uses `gh` + git via subprocess.
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone

try:
    from agents.basic_agent import BasicAgent
except ImportError:
    from basic_agent import BasicAgent


def _now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _gh(args: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(["gh", *args], capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def _git(args: list[str], cwd: str | None = None) -> tuple[int, str, str]:
    p = subprocess.run(["git", *args], capture_output=True, text=True, cwd=cwd)
    return p.returncode, p.stdout, p.stderr


def _detect_handle() -> str | None:
    rc, out, _ = _gh(["api", "user", "--jq", ".login"])
    if rc == 0 and out.strip():
        return out.strip()
    return None


def _resolve_workspace() -> str | None:
    env = os.environ.get("NB_WORKSPACE")
    if env and os.path.isdir(env):
        return os.path.expanduser(env)
    sub_path = os.path.expanduser("~/.brainstem/neighborhoods.json")
    if os.path.exists(sub_path):
        try:
            data = json.load(open(sub_path))
            for s in data.get("subscribed", []):
                wp = s.get("workspace_path")
                if wp and os.path.isdir(wp):
                    return wp
        except Exception:
            pass
    return None


def _local_data_dir(handle: str) -> str:
    base = os.path.expanduser(
        os.environ.get("NB_DATA_HOME", "~/.brainstem/neighborhoods/__SLUG__")
    )
    return os.path.join(base, handle)


_FRONT_DOOR_MD = """# {handle} — front door

This is {handle}'s personal front door inside the this neighborhood.

## What lives here (in the repo, visible to the team)

- `front_door.md` — this file. Who I am, what I work on at the team level.
- `projects.json` — list of project slugs I'm working on, with sanitized
  status enums + last-touched timestamps. No customer names beyond the
  slug. No customer data.
- `soul_overlay.md` — optional voice/disposition overlay for my Twin.

## What does NOT live here (stays on my device)

- Customer names, contacts, contracts, financials.
- Outcome statements that reveal customer specifics.
- Anything I wouldn't want a future collaborator on this repo to see.

All of that lives at `~/.bwat-data/{handle}/customers/<slug>/` on my
device. The pinger reads my LOCAL deep view; teammates see only the
sanitized projects.json from this front door.

## Onboarded

- Joined the team neighborhood: {joined_at}
- GitHub handle: {handle}
"""

_PROJECTS_JSON_INITIAL = {
    "schema": "se-projects/1.0",
    "_note": (
        "List of project SLUGS this SE is working on. NO customer data. "
        "The slug is a short opaque tag; customer data lives only at "
        "~/.bwat-data/<handle>/customers/<slug>/ on this SE's device."
    ),
    "projects": [],
}

_LOCAL_DATA_README = """# Local-only customer data

This directory holds **YOUR DEVICE'S COPY** of customer data for the neighborhood workflow.

## NEVER `git add` anything in here

This entire directory is excluded from the neighborhood workspace's `.gitignore`. The repo
intentionally does not see customer data. You are the only person who has it.

## Layout

```
~/.bwat-data/<your-handle>/customers/
├── <project-slug>/
│   ├── status.json        ← {{customer, status, owner, last_touched, blockers}}
│   ├── outcome.md         ← OutcomeFramer output, customer-specific
│   ├── intake.md          ← original ask
│   ├── notes.md           ← your working notes
│   └── attachments/       ← any files
```

## What the team sees

- The SLUG of each project (in your `ses/<handle>/projects.json` in the repo).
- The HIGH-LEVEL status enum (active / blocked / awaiting / shipped).
- The LAST-TOUCHED timestamp.

That's it. Customer name, contract value, contact list, technical details — all
of that stays here. The team can't see it; auditors who pull the repo can't
see it; a future collaborator who joins next year can't see it.

## Backup

This directory is your responsibility. Time Machine, Backblaze, an external
drive — pick one. The repo will not back this up.
"""


class SesWorkspaceInitAgent(BasicAgent):
    metadata = {
        "name": "SesWorkspaceInit",
        "description": (
            "One-shot setup for a operator's per-handle BWAT "
            "workspace. Detects the operator's GitHub handle, mints their "
            "front door in the cloned repo at ses/<handle>/ (sanitized "
            "metadata only), and creates the LOCAL-ONLY customer data "
            "directory at ~/.bwat-data/<handle>/customers/ (with a "
            "README warning that data here never enters the repo). "
            "Run once, right after Joiner."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "handle": {
                    "type": "string",
                    "description": (
                        "Override the auto-detected GitHub handle. Useful "
                        "if the brainstem's gh auth is a service account."
                    ),
                },
                "auto_stage": {
                    "type": "boolean",
                    "default": True,
                    "description": (
                        "If true, runs `git add ses/<handle>/` in the "
                        "workspace so the operator just needs to commit + push."
                    ),
                },
            },
            "required": [],
        },
    }

    def __init__(self):
        self.name = "SesWorkspaceInit"

    def perform(self, **kwargs) -> str:
        handle = (kwargs.get("handle") or "").strip() or _detect_handle()
        auto_stage = bool(kwargs.get("auto_stage", True))

        if not handle:
            return json.dumps({
                "ok": False,
                "error": (
                    "Couldn't detect your GitHub handle. Run `gh auth login` "
                    "first, OR pass handle='your-github-username' explicitly."
                ),
            })

        ws = _resolve_workspace()
        if not ws:
            return json.dumps({
                "ok": False,
                "error": (
                    "No neighborhood workspace found. Run Joiner first to "
                    "clone the team's private repo."
                ),
            })

        # 1. Repo-side: ses/<handle>/
        ses_dir = os.path.join(ws, "ses", handle)
        if os.path.isdir(ses_dir):
            repo_status = "already-exists"
        else:
            os.makedirs(ses_dir, exist_ok=True)
            repo_status = "created"
            with open(os.path.join(ses_dir, "front_door.md"), "w") as f:
                f.write(_FRONT_DOOR_MD.format(
                    handle=handle, joined_at=_now_iso(),
                ))
            with open(os.path.join(ses_dir, "projects.json"), "w") as f:
                json.dump(_PROJECTS_JSON_INITIAL, f, indent=2)
                f.write("\n")
            with open(os.path.join(ses_dir, "soul_overlay.md"), "w") as f:
                f.write(
                    f"# {handle} — soul overlay (optional)\n\n"
                    "Anything you want Twin to know about your voice, "
                    "your specialties, or your customer-facing tone. Loaded "
                    "automatically by Twin when the operator handle "
                    f"matches `{handle}`. Leave empty if you want the default.\n"
                )

        # 2. .gitignore in workspace ensuring local data never sneaks in
        gi_path = os.path.join(ws, ".gitignore")
        gi_existing = ""
        if os.path.isfile(gi_path):
            gi_existing = open(gi_path).read()
        marker = "# bwat: never commit local customer data"
        if marker not in gi_existing:
            with open(gi_path, "a") as f:
                if gi_existing and not gi_existing.endswith("\n"):
                    f.write("\n")
                f.write(f"\n{marker}\n.bwat-data/\n")
            gitignore_status = "appended"
        else:
            gitignore_status = "already-set"

        # 3. Local-side: ~/.bwat-data/<handle>/customers/
        data_dir = _local_data_dir(handle)
        customers_dir = os.path.join(data_dir, "customers")
        if os.path.isdir(customers_dir):
            local_status = "already-exists"
        else:
            os.makedirs(customers_dir, exist_ok=True)
            local_status = "created"
            with open(os.path.join(data_dir, "README.md"), "w") as f:
                f.write(_LOCAL_DATA_README)
            # .gitkeep so the dir survives even if no projects yet
            open(os.path.join(customers_dir, ".gitkeep"), "w").close()

        # 4. Stage the ses/<handle>/ files
        stage_status = "skipped"
        if auto_stage and repo_status == "created":
            rc, _, err = _git(
                ["add", os.path.join("ses", handle)], cwd=ws,
            )
            stage_status = "staged" if rc == 0 else f"git-add-failed: {err.strip()}"

        next_step = (
            f"Your front door is at {ses_dir} (repo). Your customer data "
            f"directory is at {data_dir} (LOCAL ONLY, NEVER pushed). "
            f"To complete onboarding: cd {ws} && git commit -m "
            f"'add {handle} front door' && git push. Then start a customer "
            f"project: mkdir {customers_dir}/<slug>/ and run Intake "
            f"log_idea on the customer's ask."
        )

        return json.dumps({
            "schema": "ses-init-result/1.0",
            "ok": True,
            "handle": handle,
            "workspace": ws,
            "front_door_dir": ses_dir,
            "front_door_status": repo_status,
            "local_data_dir": data_dir,
            "local_data_status": local_status,
            "gitignore_status": gitignore_status,
            "stage_status": stage_status,
            "next_step": next_step,
        }, indent=2)
