"""egg_hatcher_agent — the universal entry point for any neighborhood operation.

═════════════════════════════════════════════════════════════════════════════
YOU RECEIVED TWO FILES — this `egg_hatcher_agent.py` and a `<name>.egg`.
This docstring IS the README. There is no separate readme file. Read it
yourself, OR show this file to your LLM (Claude, GPT, Copilot, Gemini,
local Ollama — any of them) and the LLM will drive the setup.
═════════════════════════════════════════════════════════════════════════════

WHAT TO DO (human or LLM, same two steps):

  1. Move `egg_hatcher_agent.py` into your brainstem's agents/ directory.
     File browser drag-and-drop is fine. Most installs: `~/.brainstem/agents/`.
     The brainstem hot-reloads on the next chat request — no restart.

  2. In your brainstem chat, just say what you want — plain English.
     Examples that work:

         "hatch the egg"
         "hatch the egg I just downloaded"
         "set me up from the neighborhood egg"
         "I got a new neighborhood, open it"
         "install the workflow from agent-team-starter-kit.egg"

     The brainstem's LLM picks this agent based on the description,
     auto-discovers the most recent .egg in your Downloads / Desktop /
     Documents / AirDrop folders if you didn't name a path, and runs
     the install. You don't need to know the agent name, the parameter
     names, or where the egg is — just ask.

That's it. The agent does everything else in one shot. No follow-up
chats. No shell commands. No config edits.

═════════════════════════════════════════════════════════════════════════════
WHAT IT DOES (so you know what to expect)

The single chat above triggers all of this:

  · Verifies the .egg is a real RAPP neighborhood (looks for neighborhood.json
    + rar/index.json inside).
  · Unpacks the .egg into ~/brainstem-workspace/<name>/.
  · Reads rar/index.json — the workflow manifest with sha256s.
  · For each agent listed: reads from disk, sha256-verifies against the
    manifest, copies into your local brainstem agents/ directory.
    REFUSES to install on hash mismatch (no override).
  · Mints your operator rappid at ~/.brainstem/rappid.json (idempotent).
  · Mints your per-handle workspace:
       - ses/<your-handle>/ in the workspace (sanitized front door — visible
         to teammates if/when you push the workspace back to a remote)
       - ~/.brainstem/neighborhoods/<name>/<your-handle>/customers/ on this
         device (LOCAL ONLY, never enters the repo, gitignored)
  · Records the subscription at ~/.brainstem/neighborhoods.json.
  · Returns a result with `next_step` telling you what to try first.

═════════════════════════════════════════════════════════════════════════════
ALL THE MODES (one agent, four shapes — describe what you want, let the LLM route)

  Hatching from a local egg (sneakernet flow)
        Operator says: "hatch the egg" / "open this egg" / "I downloaded
        a neighborhood." Agent auto-discovers the .egg in their drop
        folders and unpacks it. No internet required.

  Hatching from an online repo
        Operator says: "join the <owner>/<name> neighborhood" / "clone
        and set up the <name> repo." Agent calls `gh repo clone`, then
        installs from the clone. Requires `gh auth` for private repos.

  Packing the current workspace (lay a new egg)
        Operator says: "pack my workspace into an egg" / "make me a
        sneakernet pack of this neighborhood." Agent zips the workspace
        into ~/brainstem-eggs/<name>-<ts>.egg. Operator can then share
        that .egg + this agent file to anyone.

  Status probe
        Operator says: "what's set up?" / "show me my neighborhoods" /
        "what eggs am I subscribed to?" Returns current subscriptions
        and operator rappid.

═════════════════════════════════════════════════════════════════════════════
INSTRUCTIONS FOR THE LLM (if you were shown this file by a human)

You (the LLM) are reading this because the operator wants you to set
them up with this neighborhood. Treat every instruction below as
load-bearing. Do not improvise the boundary rules. Always ask for
confirmation before irreversible commands.

Required steps, in order:

  Step 1. Confirm the operator has a brainstem running.
          Check for ~/.brainstem/ directory. If absent, walk them through:
            curl -fsSL https://kody-w.github.io/RAPP/installer/install.sh | bash
          (online) OR they need a local copy of kody-w/RAPP source on disk
          to run brainstem.py from (offline). Do not skip this — without
          a brainstem, none of the rest works.

  Step 2. Confirm this file is in their brainstem agents/ directory.
          Tell them to drag it via file browser (NO terminal commands —
          if you ask them to `cp` you've violated the sneakernet rule).
          Path is typically ~/.brainstem/agents/.

  Step 3. Have them say (in their brainstem chat) something natural:
            "hatch the egg I just downloaded"
          OR if they explicitly mention a path:
            "hatch the egg at <path>"
          You (the LLM) tool-call EggHatcher with the appropriate
          arguments. If the operator did NOT name a path, call with NO
          from_egg argument — the agent will auto-discover. Do NOT
          ask the operator to type the agent name or parameter names.

  Step 4. Watch for the result. Confirm:
            ok=true, agents_installed > 0, agents_errors=[]
          If sha256 mismatches appear, STOP and surface the error —
          do not skip past it.

  Step 5. The agent's `next_step` field will tell the operator what to
          try first (e.g. `Twin intro`). Relay that.

WHAT YOU MUST NOT DO:
  · Do not commit or push to git on the operator's behalf without
    explicit confirmation.
  · Do not write customer data into the workspace repo. Customer data
    lives ONLY at ~/.brainstem/neighborhoods/<name>/<handle>/customers/.
  · Do not skip sha256 verification.
  · Do not modify any *_agent.py file in the egg or workspace — they
    are sha256-pinned in rar/index.json.
  · Do not improvise extra setup steps. The five steps above ARE the
    setup. Anything else, ask the operator first.
  · Do not ask the operator to run shell commands. The single
    EggHatcher chat does the entire setup.

═════════════════════════════════════════════════════════════════════════════
THE SNEAKERNET PORTABILITY INVARIANT (kernel rule)

Per kody-w/RAPP/pages/docs/rapplication-sdk.md, a portable artifact
shared between operators consists of EXACTLY two files: one agent.py
and one .egg. The receiver MUST be able to use it with two actions
only — drag + chat. Anything that requires shell commands, config
edits, restarts, or follow-up chats fails the portability requirement.

This file (egg_hatcher_agent.py) is the bootstrap that honors that
rule. Its docstring (this thing you are reading) IS the readme. There
is no separate README.md or README.txt in the payload by design —
adding one would expand the file count past two, breaking the
invariant.

═════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import zipfile
from datetime import datetime, timezone

try:
    from agents.basic_agent import BasicAgent
except ImportError:
    from basic_agent import BasicAgent


# ─── helpers ───────────────────────────────────────────────────────────

def _now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _agents_dir() -> str:
    explicit = os.environ.get("AGENTS_PATH")
    if explicit:
        return explicit
    return os.path.dirname(os.path.abspath(__file__))


def _brainstem_home() -> str:
    return os.path.expanduser(os.environ.get("BRAINSTEM_HOME", "~/.brainstem"))


def _workspace_root() -> str:
    return os.path.expanduser(
        os.environ.get("NB_WORKSPACE_ROOT", "~/brainstem-workspace")
    )


def _local_data_dir(handle: str, nb_slug: str) -> str:
    base = os.path.expanduser(
        os.environ.get("NB_DATA_HOME", "~/.brainstem/neighborhoods")
    )
    return os.path.join(base, nb_slug, handle, "customers")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _gh(args: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(["gh", *args], capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def _detect_handle() -> str | None:
    """Best-effort handle detection. Returns None if no source available."""
    rc, out, _ = _gh(["api", "user", "--jq", ".login"])
    if rc == 0 and out.strip():
        return out.strip()
    # Fallback to local user
    return os.environ.get("USER") or None


def _discover_eggs() -> list[str]:
    """Find .egg files in common drop-zone directories, newest first."""
    locations = [
        "~/Downloads", "~/Desktop", "~/Documents",
        "~/AirDrop", "~/Sneakernet", "~/brainstem-eggs",
    ]
    candidates: list[tuple[str, float]] = []
    for loc in locations:
        d = os.path.expanduser(loc)
        if not os.path.isdir(d):
            continue
        try:
            for fname in os.listdir(d):
                if fname.endswith(".egg"):
                    full = os.path.join(d, fname)
                    if os.path.isfile(full):
                        candidates.append((full, os.path.getmtime(full)))
        except OSError:
            pass
    candidates.sort(key=lambda x: -x[1])
    return [c[0] for c in candidates]


def _mint_rappid(home: str) -> str:
    """Idempotent rappid mint. Returns the (existing or fresh) rappid."""
    os.makedirs(home, exist_ok=True)
    path = os.path.join(home, "rappid.json")
    if os.path.exists(path):
        try:
            existing = json.load(open(path))
            if existing.get("rappid"):
                return existing["rappid"]
        except Exception:
            pass
    try:
        from utils.bond import mint_rappid as kernel_mint  # type: ignore
        return kernel_mint(home).get("rappid", "")
    except Exception:
        pass
    # Fully-airgapped fallback
    import platform, uuid
    host = platform.node().lower().replace(".", "-")[:32] or "device"
    rappid = (
        f"rappid:v2:hatched:@local/{host}-brainstem:"
        f"{uuid.uuid4().hex}@github.com/local/{host}-brainstem"
    )
    with open(path, "w") as f:
        json.dump({
            "schema": "rapp-rappid/2.0",
            "rappid": rappid, "kind": "hatched",
            "born_at": _now_iso(),
            "_minted_by": "bootstrap_agent (airgapped fallback)",
        }, f, indent=2)
    return rappid


def _record_subscription(home: str, gate_repo: str, nb_rappid: str,
                          display: str, workspace_path: str) -> None:
    os.makedirs(home, exist_ok=True)
    path = os.path.join(home, "neighborhoods.json")
    data: dict = {"schema": "rapp-neighborhood-subscriptions/1.0",
                  "subscribed": []}
    if os.path.exists(path):
        try:
            data = json.load(open(path))
        except Exception:
            pass
    subs = [s for s in data.get("subscribed", [])
            if s.get("gate_repo") != gate_repo]
    subs.append({
        "gate_repo": gate_repo,
        "neighborhood_rappid": nb_rappid,
        "display_name": display,
        "workspace_path": workspace_path,
        "joined_at": _now_iso(),
    })
    data["subscribed"] = subs
    data["updated_at"] = _now_iso()
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


# ─── workspace minting (internal — no second chat needed) ──────────────

_FRONT_DOOR_MD = """# {handle} — front door

This is {handle}'s personal front door inside this neighborhood.

## What lives here (in the repo, visible to the team)

- `front_door.md` — this file.
- `projects.json` — list of project slugs, status enums, last-touched.
  No customer data.
- `soul_overlay.md` — optional voice overlay for the Twin agent.

## What does NOT live here (stays on this device)

Customer names, contracts, contacts, financials, working notes — all
live ONLY at `~/.brainstem/neighborhoods/{nb_slug}/{handle}/customers/`
on this device.

## Onboarded

- Joined: {joined_at}
- Handle: {handle}
"""

_PROJECTS_JSON = {
    "schema": "se-projects/1.0",
    "_note": "Project slugs only. Customer data lives on-device, never here.",
    "projects": [],
}

_LOCAL_DATA_README = """# Local-only customer data

This directory holds YOUR DEVICE's copy of customer data for this
neighborhood. NEVER `git add` anything here — the workspace's
`.gitignore` excludes this path by construction.

Layout:

```
~/.brainstem/neighborhoods/{nb_slug}/{handle}/customers/
├── <project-slug>/
│   ├── status.json
│   ├── outcome.md
│   ├── intake.md
│   ├── notes.md
│   └── attachments/
```

Backups are your responsibility. Time Machine, Backblaze, encrypted
external drive — pick one. The repo will not back this up.
"""


def _mint_workspace(workspace_path: str, handle: str, nb_slug: str) -> dict:
    """Mint per-handle front door (in repo) + local data dir.

    Internal — called automatically by from_egg / from_repo so the user
    doesn't need a second chat.
    """
    result = {"handle": handle, "front_door_status": "unchanged",
              "local_data_status": "unchanged", "gitignore_status": "unchanged"}

    # 1. ses/<handle>/ in the workspace
    ses_dir = os.path.join(workspace_path, "ses", handle)
    if not os.path.isdir(ses_dir):
        os.makedirs(ses_dir, exist_ok=True)
        with open(os.path.join(ses_dir, "front_door.md"), "w") as f:
            f.write(_FRONT_DOOR_MD.format(
                handle=handle, joined_at=_now_iso(), nb_slug=nb_slug))
        with open(os.path.join(ses_dir, "projects.json"), "w") as f:
            json.dump(_PROJECTS_JSON, f, indent=2)
            f.write("\n")
        with open(os.path.join(ses_dir, "soul_overlay.md"), "w") as f:
            f.write(
                f"# {handle} — soul overlay (optional)\n\n"
                "Anything you want the Twin agent to know about your "
                "voice or specialties. Empty = use the neighborhood default.\n"
            )
        result["front_door_status"] = "created"

    # 2. Workspace .gitignore
    gi = os.path.join(workspace_path, ".gitignore")
    existing = open(gi).read() if os.path.isfile(gi) else ""
    marker = "# bootstrap: never commit local customer data"
    if marker not in existing:
        with open(gi, "a") as f:
            if existing and not existing.endswith("\n"):
                f.write("\n")
            f.write(f"\n{marker}\n.brainstem/\n.bwat-data/\n")
        result["gitignore_status"] = "appended"

    # 3. Local data dir
    data_dir = _local_data_dir(handle, nb_slug)
    if not os.path.isdir(data_dir):
        os.makedirs(data_dir, exist_ok=True)
        parent = os.path.dirname(data_dir)
        with open(os.path.join(parent, "README.md"), "w") as f:
            f.write(_LOCAL_DATA_README.format(handle=handle, nb_slug=nb_slug))
        open(os.path.join(data_dir, ".gitkeep"), "w").close()
        result["local_data_status"] = "created"

    result["front_door_dir"] = ses_dir
    result["local_data_dir"] = data_dir
    return result


# ─── manifest verification ─────────────────────────────────────────────

def _install_from_disk(rar: dict, source_root: str,
                        target_dir: str) -> tuple[list, list]:
    installed, errors = [], []
    for item in rar.get("required_for_participation") or []:
        rel = item.get("file") or ""
        expected = (item.get("sha256") or "").lower()
        if not rel or not expected:
            errors.append({"item": item.get("name"),
                           "error": "manifest missing file or sha256"})
            continue
        src = os.path.join(source_root, rel)
        if not os.path.isfile(src):
            errors.append({"item": rel, "error": f"file missing: {src}"})
            continue
        body = open(src, "rb").read()
        actual = _sha256(body)
        if actual != expected:
            errors.append({"item": rel,
                           "error": f"sha256 mismatch (manifest {expected[:12]}…, got {actual[:12]}…)"})
            continue
        try:
            shutil.copyfile(src, os.path.join(target_dir, os.path.basename(rel)))
            installed.append({"name": item.get("name"), "file": os.path.basename(rel),
                              "sha256": actual, "size": len(body)})
        except Exception as e:
            errors.append({"item": rel, "error": f"copy failed: {e}"})
    return installed, errors


# ─── the agent ─────────────────────────────────────────────────────────

class EggHatcherAgent(BasicAgent):
    metadata = {
        "name": "EggHatcher",
        "description": (
            "Hatches a RAPP neighborhood egg into the local brainstem. "
            "USE THIS WHEN THE OPERATOR SAYS ANY OF: 'hatch the egg', "
            "'hatch this egg', 'set me up from the egg', 'open this "
            "neighborhood', 'install this workflow', 'I just downloaded "
            "a neighborhood', 'I got an egg', 'unpack this egg', "
            "'bring up the neighborhood from my downloads', or anytime "
            "they mention a `.egg` file they received. Auto-discovers "
            "the most recent .egg in ~/Downloads/, ~/Desktop/, "
            "~/Documents/, ~/AirDrop/ if no path given. ONE call does "
            "everything: unpacks, sha256-verifies + installs all workflow "
            "agents, mints the operator's rappid + per-handle workspace + "
            "local data dir. No follow-up chats needed. Also handles: "
            "joining an online repo (`from_repo`), packing the current "
            "workspace into a fresh egg for sharing (`pack_egg`), and "
            "status probes."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "from_egg": {
                    "type": "string",
                    "description": (
                        "Path to a local .egg file. OPTIONAL — if omitted, "
                        "auto-discovers the most recent .egg in the "
                        "operator's Downloads/Desktop/Documents/AirDrop "
                        "folders. Only set this if the operator explicitly "
                        "named a path or named a file the LLM should look up."
                    ),
                },
                "from_repo": {
                    "type": "string",
                    "description": "owner/name of a GitHub repo to clone. Triggers the online flow.",
                },
                "pack_egg": {
                    "type": "boolean",
                    "description": "Pack current workspace into a new .egg for sharing.",
                },
                "output_path": {
                    "type": "string",
                    "description": "Where to write the new .egg (for pack_egg). Defaults to ~/brainstem-eggs/<name>-<ts>.egg.",
                },
                "workspace": {
                    "type": "string",
                    "description": "Workspace path. Auto-discovered if omitted.",
                },
                "handle": {
                    "type": "string",
                    "description": "Override the auto-detected operator handle.",
                },
                "force": {
                    "type": "boolean", "default": False,
                    "description": "Allow overwriting an existing workspace.",
                },
            },
            "required": [],
        },
    }

    def __init__(self):
        self.name = "EggHatcher"

    def perform(self, **kwargs) -> str:
        # Mode dispatch
        if kwargs.get("from_egg"):
            return self._from_egg(**kwargs)
        if kwargs.get("from_repo"):
            return self._from_repo(**kwargs)
        if kwargs.get("pack_egg"):
            return self._pack_egg(**kwargs)
        return self._status()

    # ─── from_egg: full sneakernet bootstrap ──────────────────────────

    def _from_egg(self, **kwargs) -> str:
        egg_path = os.path.expanduser(kwargs.get("from_egg") or "")
        force = bool(kwargs.get("force", False))
        handle = (kwargs.get("handle") or "").strip() or _detect_handle()

        if not egg_path:
            # Auto-discover: scan common drop zones for .egg files (newest first)
            discovered = _discover_eggs()
            if not discovered:
                return json.dumps({
                    "ok": False,
                    "error": (
                        "No egg path given and no .egg file found in "
                        "~/Downloads/, ~/Desktop/, ~/Documents/, ~/AirDrop/, "
                        "or ~/brainstem-eggs/. Tell the operator: 'I don't "
                        "see a neighborhood egg in your usual download "
                        "locations — where did you save it?'"
                    ),
                })
            egg_path = discovered[0]
        elif not os.path.isfile(egg_path):
            return json.dumps({"ok": False,
                                "error": f"egg not readable: {egg_path!r}"})
        if not handle:
            return json.dumps({"ok": False,
                                "error": "couldn't detect handle; pass handle=<your-name>"})

        try:
            zf = zipfile.ZipFile(egg_path, "r")
        except Exception as e:
            return json.dumps({"ok": False, "error": f"egg not a valid zip: {e}"})

        names = set(zf.namelist())
        prefix = ""
        if "neighborhood.json" not in names:
            cands = [n for n in names
                     if n.endswith("/neighborhood.json") and n.count("/") == 1]
            if not cands:
                zf.close()
                return json.dumps({"ok": False,
                                    "error": "no neighborhood.json in egg"})
            prefix = cands[0][: -len("neighborhood.json")]

        try:
            nb_meta = json.loads(zf.read(prefix + "neighborhood.json").decode())
            rar = json.loads(zf.read(prefix + "rar/index.json").decode())
        except Exception as e:
            zf.close()
            return json.dumps({"ok": False, "error": f"egg metadata unparseable: {e}"})

        nb_slug = nb_meta.get("name") or "unnamed"
        nb_display = nb_meta.get("display_name") or nb_slug
        nb_rappid = nb_meta.get("neighborhood_rappid") or nb_meta.get("rappid") or ""
        gate_repo = nb_meta.get("gate_repo") or "(local-only)"

        ws_root = kwargs.get("workspace") or _workspace_root()
        ws_root = os.path.expanduser(ws_root)
        os.makedirs(ws_root, exist_ok=True)
        ws_path = os.path.join(ws_root, nb_slug)

        if os.path.isdir(ws_path) and not force:
            zf.close()
            return json.dumps({
                "ok": False,
                "error": (f"workspace already at {ws_path}; pass force=true to overwrite, "
                           "OR use the existing workspace as-is."),
                "existing_workspace": ws_path,
            })
        if force and os.path.isdir(ws_path):
            shutil.rmtree(ws_path)

        # Extract
        os.makedirs(ws_path, exist_ok=True)
        ws_real = os.path.realpath(ws_path)
        for info in zf.infolist():
            if prefix and not info.filename.startswith(prefix):
                continue
            rel = info.filename[len(prefix):] if prefix else info.filename
            if not rel:
                continue
            target = os.path.realpath(os.path.join(ws_path, rel))
            if not target.startswith(ws_real + os.sep):
                zf.close()
                return json.dumps({"ok": False,
                                    "error": f"path-traversal blocked: {info.filename}"})
            if info.is_dir():
                os.makedirs(target, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with open(target, "wb") as f:
                    f.write(zf.read(info.filename))
        zf.close()

        # Install agents
        installed, errors = _install_from_disk(rar, ws_path, _agents_dir())

        # Mint rappid + workspace + subscription (NO SECOND CHAT NEEDED)
        operator_rappid = _mint_rappid(_brainstem_home())
        ws_result = _mint_workspace(ws_path, handle, nb_slug)
        _record_subscription(_brainstem_home(), gate_repo, nb_rappid,
                              nb_display, ws_path)
        os.environ["NB_WORKSPACE"] = ws_path

        return json.dumps({
            "schema": "bootstrap-result/1.0",
            "ok": not errors,
            "mode": "from_egg",
            "egg_path": egg_path,
            "neighborhood_name": nb_display,
            "neighborhood_slug": nb_slug,
            "neighborhood_rappid": nb_rappid,
            "operator_rappid": operator_rappid,
            "handle": handle,
            "workspace": ws_path,
            "agents_installed": len(installed),
            "agents_errors": errors,
            "workspace_mint": ws_result,
            "internet_used": False,
            "next_step": (
                f"Done. {nb_display} is loaded. Workspace at {ws_path}. "
                f"Your local-only customer data dir: {ws_result['local_data_dir']}. "
                f"Try in chat: any of the loaded workflow agents (e.g. "
                f"`Twin intro` or `EngagementFactory slug=hello-world ...`)."
            ),
        }, indent=2)

    # ─── from_repo: online clone ──────────────────────────────────────

    def _from_repo(self, **kwargs) -> str:
        gate_repo = (kwargs.get("from_repo") or "").strip().strip("/")
        force = bool(kwargs.get("force", False))
        handle = (kwargs.get("handle") or "").strip() or _detect_handle()

        if not gate_repo or "/" not in gate_repo:
            return json.dumps({"ok": False,
                                "error": "from_repo must be 'owner/name'"})
        if not handle:
            return json.dumps({"ok": False,
                                "error": "couldn't detect handle"})

        ws_root = kwargs.get("workspace") or _workspace_root()
        ws_root = os.path.expanduser(ws_root)
        os.makedirs(ws_root, exist_ok=True)
        _, name = gate_repo.split("/", 1)
        ws_path = os.path.join(ws_root, name)

        if os.path.isdir(os.path.join(ws_path, ".git")) and not force:
            clone_status = "already-cloned"
        else:
            if force and os.path.isdir(ws_path):
                shutil.rmtree(ws_path)
            rc, out, err = _gh(["repo", "clone", gate_repo, ws_path])
            if rc != 0:
                return json.dumps({
                    "ok": False,
                    "error": (f"gh repo clone failed: {err.strip() or out.strip()}. "
                               "Run `gh auth login` if not authenticated, OR confirm "
                               "you're a collaborator on this private repo."),
                })
            clone_status = "cloned"

        rar_path = os.path.join(ws_path, "rar", "index.json")
        nb_path = os.path.join(ws_path, "neighborhood.json")
        if not os.path.isfile(rar_path) or not os.path.isfile(nb_path):
            return json.dumps({"ok": False,
                                "error": "repo doesn't look like a neighborhood (no rar/index.json + neighborhood.json)"})
        rar = json.load(open(rar_path))
        nb_meta = json.load(open(nb_path))
        nb_slug = nb_meta.get("name") or name
        nb_display = nb_meta.get("display_name") or nb_slug
        nb_rappid = nb_meta.get("neighborhood_rappid") or nb_meta.get("rappid") or ""

        installed, errors = _install_from_disk(rar, ws_path, _agents_dir())
        operator_rappid = _mint_rappid(_brainstem_home())
        ws_result = _mint_workspace(ws_path, handle, nb_slug)
        _record_subscription(_brainstem_home(), gate_repo, nb_rappid,
                              nb_display, ws_path)
        os.environ["NB_WORKSPACE"] = ws_path

        return json.dumps({
            "schema": "bootstrap-result/1.0",
            "ok": not errors,
            "mode": "from_repo",
            "gate_repo": gate_repo,
            "neighborhood_name": nb_display,
            "neighborhood_slug": nb_slug,
            "neighborhood_rappid": nb_rappid,
            "operator_rappid": operator_rappid,
            "handle": handle,
            "workspace": ws_path,
            "clone_status": clone_status,
            "agents_installed": len(installed),
            "agents_errors": errors,
            "workspace_mint": ws_result,
            "internet_used": True,
            "next_step": (
                f"Done. {nb_display} cloned + loaded. Try the workflow "
                f"agents in chat. Push your front-door changes back when "
                f"ready: cd {ws_path} && git commit -am 'add {handle}' && git push."
            ),
        }, indent=2)

    # ─── pack_egg: produce a sneakernet payload from current workspace ──

    def _pack_egg(self, **kwargs) -> str:
        ws_path = kwargs.get("workspace")
        if not ws_path:
            # Auto-discover from subscription
            sub = os.path.expanduser("~/.brainstem/neighborhoods.json")
            if os.path.exists(sub):
                try:
                    data = json.load(open(sub))
                    for s in data.get("subscribed", []):
                        wp = s.get("workspace_path")
                        if wp and os.path.isdir(wp):
                            ws_path = wp
                            break
                except Exception:
                    pass
        ws_path = os.path.expanduser(ws_path or "")
        if not ws_path or not os.path.isdir(ws_path):
            return json.dumps({"ok": False,
                                "error": "no workspace found; pass workspace=<path>"})

        # Read neighborhood.json for name + identity
        nb_path = os.path.join(ws_path, "neighborhood.json")
        if not os.path.isfile(nb_path):
            return json.dumps({"ok": False,
                                "error": f"no neighborhood.json at {ws_path}"})
        nb_meta = json.load(open(nb_path))
        nb_slug = nb_meta.get("name") or "unnamed"

        out_path = kwargs.get("output_path")
        if not out_path:
            egg_dir = os.path.expanduser("~/brainstem-eggs")
            os.makedirs(egg_dir, exist_ok=True)
            ts = _now_iso().replace(":", "").replace("-", "")[:13]
            out_path = os.path.join(egg_dir, f"{nb_slug}-{ts}.egg")
        out_path = os.path.expanduser(out_path)

        # Walk workspace; exclude .git, .gitignore'd dirs, customer data
        EXCLUDE_DIRS = {".git", "__pycache__", ".bwat-data", ".brainstem"}
        EXCLUDE_FILES = {".DS_Store"}
        files_packed = 0
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(ws_path):
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
                for f in files:
                    if f in EXCLUDE_FILES:
                        continue
                    full = os.path.join(root, f)
                    rel = os.path.relpath(full, ws_path)
                    zf.write(full, rel)
                    files_packed += 1

        return json.dumps({
            "schema": "bootstrap-result/1.0",
            "ok": True,
            "mode": "pack_egg",
            "workspace": ws_path,
            "egg_path": out_path,
            "egg_size_bytes": os.path.getsize(out_path),
            "files_packed": files_packed,
            "next_step": (
                f"Egg packed at {out_path}. To share: copy this file + the "
                f"`bootstrap_agent.py` to a peer (USB / AirDrop / scp). They "
                f"drop the .py into their brainstem agents/ and chat: "
                f"`EggHatcher from_egg={out_path}`. That's the entire setup."
            ),
        }, indent=2)

    # ─── status: probe what's set up ──────────────────────────────────

    def _status(self) -> str:
        home = _brainstem_home()
        rappid_path = os.path.join(home, "rappid.json")
        sub_path = os.path.join(home, "neighborhoods.json")
        rappid = None
        if os.path.exists(rappid_path):
            try:
                rappid = json.load(open(rappid_path)).get("rappid")
            except Exception:
                pass
        subs = []
        if os.path.exists(sub_path):
            try:
                subs = json.load(open(sub_path)).get("subscribed", [])
            except Exception:
                pass
        return json.dumps({
            "ok": True,
            "agent": self.name,
            "operator_rappid": rappid,
            "subscriptions": [
                {"gate_repo": s.get("gate_repo"),
                  "display_name": s.get("display_name"),
                  "workspace_path": s.get("workspace_path"),
                  "joined_at": s.get("joined_at")}
                for s in subs
            ],
            "modes": ["from_egg", "from_repo", "pack_egg", "status"],
            "next_step": (
                "To bootstrap from a sneakernet egg: `EggHatcher from_egg=/path/to/file.egg`. "
                "To clone an online repo: `EggHatcher from_repo=owner/name`. "
                "To pack your current workspace as an egg for sharing: `EggHatcher pack_egg=true`."
            ),
        }, indent=2)
