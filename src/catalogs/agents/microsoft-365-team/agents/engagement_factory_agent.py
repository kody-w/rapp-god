"""bwat_customer_factory_agent — end-to-end customer engagement factory.

The single agent an operator calls to start a new customer engagement. Composes
every other BWAT agent into one operation so the operator doesn't have to
remember the order:

  1. Detects (or accepts) the operator's GitHub handle.
  2. If `~/.bwat-data/<handle>/customers/<slug>/` doesn't exist, CREATES
     it with the canonical template files (status.json, intake.md,
     outcome.md skeleton, notes.md, validations.md skeleton).
  3. Calls Intake.log_idea — captures the customer's raw ask in the
     local brainstem backlog.
  4. Calls OutcomeFramer.frame_outcome — writes the structured
     outcome statement into the customer's outcome.md.
  5. Updates ses/<handle>/projects.json in the cloned neighborhood workspace —
     adds this slug + status='active' + last_touched timestamp. Sanitized;
     no customer data leaks.
  6. Returns a report with everything created + a next-step pointer.

Does NOT push to git. The SE reviews + commits ses/<handle>/projects.json
themselves (one-line change). Customer data stays at ~/.bwat-data/.

Idempotent: if the customer dir already exists, falls through to log/frame
without overwriting any user-edited files.

Lives in the this neighborhood's rar — drops into any joined SE's
brainstem automatically.
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import os
import subprocess
import sys
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


def _gh_handle() -> str | None:
    try:
        p = subprocess.run(
            ["gh", "api", "user", "--jq", ".login"],
            capture_output=True, text=True,
        )
        if p.returncode == 0 and p.stdout.strip():
            return p.stdout.strip()
    except Exception:
        pass
    return None


def _resolve_workspace() -> str | None:
    env = os.environ.get("NB_WORKSPACE")
    if env and os.path.isdir(os.path.expanduser(env)):
        return os.path.expanduser(env)
    sub = os.path.expanduser("~/.brainstem/neighborhoods.json")
    if os.path.exists(sub):
        try:
            data = json.load(open(sub))
            for s in data.get("subscribed", []):
                wp = s.get("workspace_path")
                if wp and os.path.isdir(wp):
                    return wp
        except Exception:
            pass
    fallback = os.path.expanduser("~/brainstem-workspace")
    if os.path.isdir(fallback):
        for entry in os.listdir(fallback):
            cand = os.path.join(fallback, entry)
            if os.path.isdir(os.path.join(cand, "ses")):
                return cand
    return None


def _local_data_dir(handle: str) -> str:
    base = os.path.expanduser(
        os.environ.get("NB_DATA_HOME", "~/.brainstem/neighborhoods/__SLUG__")
    )
    return os.path.join(base, handle, "customers")


def _load_sibling_agent(class_name: str):
    """Best-effort import of another BWAT agent loaded into agents/."""
    candidates = [
        f"agents.{class_name.lower()[:-len('Agent')] if class_name.endswith('Agent') else class_name.lower()}_agent",
    ]
    # Map known classes to their files explicitly (most reliable).
    explicit = {
        "IntakeAgent": "agents.bwat_intake_agent",
        "OutcomeFramerAgent": "agents.bwat_outcome_framer_agent",
        "OutcomeValidatorAgent": "agents.bwat_outcome_validator_agent",
        "PmAgent": "agents.bwat_pm_agent",
    }
    if class_name in explicit:
        candidates.insert(0, explicit[class_name])
    for mod_name in candidates:
        try:
            mod = importlib.import_module(mod_name)
            cls = getattr(mod, class_name, None)
            if cls is not None:
                return cls
        except Exception:
            continue
    return None


# ── customer dir templates ─────────────────────────────────────────────

_TPL_STATUS = {
    "schema": "engagement-status/1.0",
    "customer": "<CUSTOMER NAME — local only, never committed>",
    "slug": None,  # set per-customer
    "status": "active",
    "owner": None,  # set to handle
    "last_touched": None,  # set per write
    "blockers": [],
    "tags": [],
}

_TPL_INTAKE = """# Intake — {customer_name}

**Slug:** `{slug}`
**Logged at:** {ts}
**Channel:** <how you heard about it: meeting / email / Issues / etc.>

## Original ask (verbatim)

{ask}

## Inferred from the ask

- Industry: <fill in>
- Likely Microsoft stack involved: <D365 / Power Platform / AI Foundry / ...>
- Sensitivity tier: <public / restricted / confidential / regulated>

## Notes

<your notes here>
"""

_TPL_OUTCOME = """# Outcome — {customer_name}

**Slug:** `{slug}`
**Framed at:** {ts}
**Owner:** {owner}

## Outcome statement

<This will be filled in by OutcomeFramer when the factory runs;
edit afterward as the picture sharpens.>

## Success looks like

<Single sentence the owner agrees with.>

## KPIs

- <KPI 1>
- <KPI 2>
- <KPI 3>

## Done when

<Definition of done. Concrete. Demonstrable.>

## Out of scope

<Things this engagement is explicitly NOT addressing.>
"""

_TPL_NOTES = """# Notes — {customer_name}

Working notes. Append, don't rewrite. Customer-confidential — never
leaves this device.

## {ts}

<first note>
"""

_TPL_VALIDATIONS = """# Validations — {customer_name}

What the OutcomeValidator confirmed shipped. One section per
validated outcome.

<empty until something has shipped + been validated>
"""


def _ensure_customer_dir(handle: str, slug: str, customer_name: str,
                          ask: str) -> tuple[str, dict[str, str]]:
    base = _local_data_dir(handle)
    cust_dir = os.path.join(base, slug)
    created: dict[str, str] = {}
    os.makedirs(cust_dir, exist_ok=True)

    files = {
        "status.json": json.dumps({
            **_TPL_STATUS, "slug": slug,
            "customer": customer_name,
            "owner": handle,
            "last_touched": _now_iso(),
        }, indent=2) + "\n",
        "intake.md": _TPL_INTAKE.format(
            customer_name=customer_name, slug=slug,
            ts=_now_iso(), ask=ask or "<paste the customer's ask here>"),
        "outcome.md": _TPL_OUTCOME.format(
            customer_name=customer_name, slug=slug,
            ts=_now_iso(), owner=handle),
        "notes.md": _TPL_NOTES.format(
            customer_name=customer_name, ts=_now_iso()),
        "validations.md": _TPL_VALIDATIONS.format(
            customer_name=customer_name),
    }
    for fname, body in files.items():
        path = os.path.join(cust_dir, fname)
        if not os.path.exists(path):
            with open(path, "w") as f:
                f.write(body)
            created[fname] = path
    return cust_dir, created


def _update_se_projects(workspace: str, handle: str, slug: str,
                          customer_display: str) -> tuple[bool, str]:
    pj_path = os.path.join(workspace, "ses", handle, "projects.json")
    if not os.path.isfile(pj_path):
        return False, f"no projects.json at {pj_path} — run SesWorkspaceInit first"
    try:
        data = json.load(open(pj_path))
    except Exception as e:
        return False, f"projects.json parse failed: {e}"
    projects = data.get("projects") or []
    # If slug already exists, just bump last_touched
    found = False
    for p in projects:
        if isinstance(p, dict) and p.get("slug") == slug:
            p["last_touched"] = _now_iso()
            found = True
    if not found:
        projects.append({
            "slug": slug,
            "status": "active",
            "last_touched": _now_iso(),
            "blockers": [],
        })
    data["projects"] = projects
    data["updated_at"] = _now_iso()
    with open(pj_path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    return True, ("appended" if not found else "touched")


class EngagementFactoryAgent(BasicAgent):
    metadata = {
        "name": "EngagementFactory",
        "description": (
            "End-to-end customer engagement factory. One call: creates "
            "the LOCAL customer data dir with template files (if not "
            "already present), logs the ask via Intake, frames the "
            "outcome via OutcomeFramer, and updates the operator's "
            "ses/<handle>/projects.json in the workspace with the new "
            "slug. Idempotent. Use this when an operator wants to start a new "
            "customer engagement without thinking about the agent order."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "slug": {
                    "type": "string",
                    "description": (
                        "Short opaque tag for this engagement (lowercase, "
                        "hyphens). E.g. 'acme-corp' or 'q3-pilot'."
                    ),
                },
                "customer_name": {
                    "type": "string",
                    "description": (
                        "Real customer name — kept LOCAL. Never appears "
                        "in the repo."
                    ),
                },
                "ask": {
                    "type": "string",
                    "description": "The customer's raw ask in their own words.",
                },
                "handle": {
                    "type": "string",
                    "description": "Override the auto-detected GitHub handle.",
                },
            },
            "required": ["slug", "customer_name", "ask"],
        },
    }

    def __init__(self):
        self.name = "EngagementFactory"

    def perform(self, **kwargs) -> str:
        slug = (kwargs.get("slug") or "").strip().lower()
        customer_name = (kwargs.get("customer_name") or "").strip()
        ask = (kwargs.get("ask") or "").strip()
        handle = (kwargs.get("handle") or "").strip() or _gh_handle()

        if not slug or not customer_name or not ask:
            return json.dumps({
                "ok": False,
                "error": "slug, customer_name, and ask are all required.",
            })
        if not handle:
            return json.dumps({
                "ok": False,
                "error": (
                    "Couldn't detect GitHub handle. Run `gh auth login` "
                    "or pass handle='your-github-username'."
                ),
            })

        # 1. Ensure local customer dir + templates.
        cust_dir, created_files = _ensure_customer_dir(
            handle, slug, customer_name, ask)

        # 2. Log the ask via Intake (best-effort — the agent may
        #    not be importable from arbitrary contexts).
        intake_result = None
        intake_cls = _load_sibling_agent("IntakeAgent")
        if intake_cls is not None:
            try:
                raw = intake_cls().perform(
                    action="log_idea",
                    title=f"[{slug}] {customer_name}",
                    body=ask,
                )
                intake_result = json.loads(raw) if isinstance(raw, str) else raw
            except Exception as e:
                intake_result = {"ok": False, "error": str(e)}
        else:
            intake_result = {"ok": False,
                              "error": "IntakeAgent not loaded — run Joiner."}

        # 3. Frame the outcome via OutcomeFramer + write to outcome.md.
        framer_result = None
        framer_cls = _load_sibling_agent("OutcomeFramerAgent")
        if framer_cls is not None:
            try:
                raw = framer_cls().perform(
                    action="frame_outcome",
                    use_case=ask,
                    owner=handle,
                )
                framer_result = json.loads(raw) if isinstance(raw, str) else raw
                # Append the framed statement to outcome.md
                if framer_result.get("ok"):
                    statement = framer_result.get("outcome_markdown", "")
                    if statement:
                        outcome_path = os.path.join(cust_dir, "outcome.md")
                        existing = ""
                        if os.path.exists(outcome_path):
                            existing = open(outcome_path).read()
                        marker = "## Outcome statement (auto-framed)"
                        if marker not in existing:
                            with open(outcome_path, "a") as f:
                                f.write(f"\n\n{marker}\n\n{statement}\n")
            except Exception as e:
                framer_result = {"ok": False, "error": str(e)}
        else:
            framer_result = {"ok": False,
                              "error": "OutcomeFramerAgent not loaded."}

        # 4. Update SE's ses/<handle>/projects.json (sanitized).
        ws = _resolve_workspace()
        projects_update = None
        if ws:
            ok, msg = _update_se_projects(ws, handle, slug, customer_name)
            projects_update = {"ok": ok, "status": msg, "workspace": ws}
        else:
            projects_update = {"ok": False,
                                "error": "no workspace — run Joiner first"}

        ready_to_commit = bool(ws and projects_update.get("ok"))
        next_step = (
            (
                f"Engagement '{slug}' is set up. "
                f"Local data: {cust_dir}. "
                f"Sanitized tracking: {ws}/ses/{handle}/projects.json. "
                f"Commit + push the projects.json change so teammates see "
                f"the slug:\n"
                f"  cd {ws} && git add ses/{handle}/projects.json && "
                f"git commit -m 'add {slug}' && git push"
            ) if ready_to_commit else
            "Local customer dir set up. Some downstream steps failed — "
            "see the per-step results."
        )

        return json.dumps({
            "schema": "engagement-factory-result/1.0",
            "ok": ready_to_commit and intake_result.get("ok") and framer_result.get("ok"),
            "handle": handle,
            "slug": slug,
            "customer_local_dir": cust_dir,
            "files_created": list(created_files.keys()),
            "files_already_present": [
                f for f in ("status.json", "intake.md", "outcome.md",
                             "notes.md", "validations.md")
                if f not in created_files
            ],
            "intake_result": intake_result,
            "framer_result": framer_result,
            "projects_update": projects_update,
            "next_step": next_step,
        }, indent=2)
