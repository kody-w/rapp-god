"""egg_hatcher_agent — the universal entry point for any neighborhood operation.

THE SNEAKERNET PORTABILITY INVARIANT (per specs/NEIGHBORHOOD_PROTOCOL.md):
A neighborhood shared between operators consists of EXACTLY two files —
this `agent.py` and one `<neighborhood>.egg`. The receiver:

    1. Drops the .py into their brainstem's agents/ dir (drag + drop).
    2. Chats one command to their brainstem.

That's it. NO shell commands. NO `cd`. NO `pip install`. NO follow-up
configuration. The `bootstrap_agent.py` is responsible for everything
the receiver needs in one perform() call.

Modes (the user picks one in chat):

    Bootstrap from_egg=/path/to/<name>.egg
        Unpacks the egg, sha256-verifies + installs every workflow agent,
        mints the operator's rappid if missing, mints the operator's
        per-handle workspace (front door + local-only data dir), records
        the subscription. Internet not required.

    Bootstrap from_repo=owner/name
        Same as from_egg but pulls from a GitHub repo via gh. Internet +
        gh auth required. Use when the neighborhood is online + you have
        collaborator access.

    Bootstrap pack_egg=true output_path=~/Downloads/my-neighborhood.egg
        Packs the operator's current workspace into a new .egg, ready
        to sneakernet to anyone. Includes EVERYTHING needed for a clean
        bootstrap on a peer's machine. Pair the output .egg with a copy
        of THIS file → the recipient has the full two-file payload.

    Bootstrap status
        Reports what's set up, what's missing, what's stale.

The agent does workspace mint INTERNALLY — no second chat required.
After from_egg or from_repo, the user has a complete working
neighborhood loaded into their brainstem.
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
    # Fully-airgapped fallback. Emit the canonical §6.1 rappid
    # (rappid:@<owner>/<slug>:<64hex>) — the slug is canonicalized to the grammar
    # and the tail is Hb("rapp/1:rappid", uuid4) (full 64-hex, domain-separated,
    # keyless — NOT uuid4().hex, which is only 32 hex and fails §6.1). `kind`
    # lives in the record below.
    import platform, uuid, re, hashlib
    host = re.sub(r"[^a-z0-9]+", "-", platform.node().lower()).strip("-")[:32] or "device"
    _tail = hashlib.sha256(b"rapp/1:rappid\n" + uuid.uuid4().bytes).hexdigest()
    rappid = f"rappid:@local/{host}-brainstem:{_tail}"
    with open(path, "w") as f:
        json.dump({
            "schema": "rapp/1",
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
            "Universal neighborhood bootstrap. ONE call from chat does "
            "everything: unpacks the .egg (or clones the repo), sha256-"
            "verifies and installs every workflow agent, mints the "
            "operator's rappid + per-handle workspace + local data dir. "
            "No second chat, no shell commands. Modes: from_egg (sneakernet), "
            "from_repo (online), pack_egg (produce a portable .egg from "
            "current workspace for sharing), status (probe what's set up)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "from_egg": {
                    "type": "string",
                    "description": "Path to a local .egg file. Triggers the sneakernet flow.",
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

        if not egg_path or not os.path.isfile(egg_path):
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
