"""Cowork Cookbook — RACon cartridge loader (the ONLY file you export + hotload).

RACon = RAPP Agent Console. Drop this one agent.py into your local brainstem's agents/ dir. On run it:

  1. pulls the portable .egg cartridge from the public repo (raw GitHub),
  2. unpacks it fully into a local twin root (everything the rapplication needs is in the .egg),
  3. spins it up as its OWN running rapplication twin on its OWN port,
  4. registers it so the global brainstem.py collaborates with it over twin-chat.

Insert the cartridge, the console boots it as a twin — and you use the Cowork Cookbook with its own
twin + workspace, like a game/app on a console. Self-contained, stdlib only.

  perform()                 → hatch (download → unpack → boot twin → register)
  perform(action="status")  → the twins registry
  perform(action="stop")    → stop this twin
  perform(dry_run=true)     → say exactly what hatch would do, do nothing
"""

__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@cowork/cowork_cookbook_agent",
    "version": "1.0.0",
    "display_name": "CoworkCookbook",
    "description": "RACon cartridge loader for the Cowork Cookbook — pulls the .egg and hatches it as its own brainstem-twin on its own port.",
    "author": "kody-w",
    "tags": ["racon", "rapp-agent-console", "cartridge", "twin", "cowork", "cookbook", "loader", "egg"],
    "category": "integrations",
    "quality_tier": "community",
    "requires_env": [],
    "dependencies": ["@rapp/basic_agent"],
}

import os
import io
import sys
import json
import time
import socket
import zipfile
import subprocess
import urllib.request
from datetime import datetime, timezone

try:
    from agents.basic_agent import BasicAgent  # type: ignore
except Exception:
    class BasicAgent:
        def __init__(self, name, metadata):
            self.name = name
            self.metadata = metadata

REPO = "kody-w/cowork-cookbook-rapp"
RAW = "https://raw.githubusercontent.com/" + REPO + "/main"
EGG_URL = RAW + "/cowork_cookbook.egg"
TWIN_ID = "cowork_cookbook"
TWIN_NAME = "Cowork Cookbook"


def _root():
    return os.path.expanduser(os.environ.get("BRAINSTEM_HOME", "~/.brainstem"))


def _data():
    return os.path.join(_root(), ".brainstem_data")


def _twin_root():
    return os.path.join(_data(), "twins", TWIN_ID)


def _registry():
    return os.path.join(_data(), "twins.json")


def _free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close()
    return p


def _find_brainstem_py():
    env = os.environ.get("BRAINSTEM_PY")
    if env and os.path.exists(env):
        return env
    for c in [os.path.join(_root(), "src", "rapp_brainstem", "brainstem.py"),
              os.path.join(_root(), "brainstem.py")]:
        if os.path.exists(c):
            return c
    return None


def _load_registry():
    try:
        return json.load(open(_registry()))
    except Exception:
        return {"schema": "rapp-twins/1.0", "twins": []}


def _save_registry(reg):
    os.makedirs(os.path.dirname(_registry()), exist_ok=True)
    json.dump(reg, open(_registry(), "w"), indent=2)


def _register(entry):
    reg = _load_registry()
    reg["twins"] = [t for t in reg.get("twins", []) if t.get("id") != entry["id"]] + [entry]
    _save_registry(reg)


class CoworkCookbookAgent(BasicAgent):
    def __init__(self):
        self.name = "CoworkCookbook"
        self.metadata = {
            "name": self.name,
            "description": "RACon cartridge loader — hatch the Cowork Cookbook as its own twin. "
                           "perform() to hatch; action='status'|'stop'; dry_run=true to preview.",
            "parameters": {"type": "object", "properties": {
                "action": {"type": "string", "description": "hatch (default) | status | stop"},
                "dry_run": {"type": "boolean", "description": "Describe the hatch without doing it."},
            }, "required": []},
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs):
        action = (kwargs.get("action") or "hatch").lower()
        if action == "status":
            reg = _load_registry()
            mine = [t for t in reg.get("twins", []) if t.get("id") == TWIN_ID]
            return json.dumps(mine[0], indent=2) if mine else "Cowork Cookbook twin not hatched yet. Run me to hatch it."
        if action == "stop":
            reg = _load_registry()
            for t in reg.get("twins", []):
                if t.get("id") == TWIN_ID and t.get("pid"):
                    try:
                        os.kill(int(t["pid"]), 15)
                    except Exception:
                        pass
                    t["status"] = "stopped"
            _save_registry(reg)
            return "Cowork Cookbook twin stopped."

        port = _free_port()
        bspy = _find_brainstem_py()
        twin_root = _twin_root()
        plan = ("RACon hatch plan:\n"
                "  1. fetch  %s\n"
                "  2. unpack → %s\n"
                "  3. boot a brainstem-twin on port %d (agents = twin/agents)\n"
                "  4. register in %s → reachable over twin-chat at http://127.0.0.1:%d/chat\n"
                "  brainstem.py: %s" % (EGG_URL, twin_root, port, _registry(), port, bspy or "NOT FOUND (will unpack + register; start it manually)"))
        if kwargs.get("dry_run"):
            return plan

        # 1 + 2: load the portable .egg and unpack everything locally.
        # Source: cloud (raw GitHub) is the DEFAULT; set RACON_EGG=/path/to/.egg to load a local cartridge.
        local = os.environ.get("RACON_EGG")
        try:
            if local and os.path.exists(local):
                egg = open(local, "rb").read(); src = local
            else:
                with urllib.request.urlopen(EGG_URL, timeout=30) as r:
                    egg = r.read(); src = EGG_URL
            os.makedirs(twin_root, exist_ok=True)
            zipfile.ZipFile(io.BytesIO(egg)).extractall(twin_root)
        except Exception as e:
            return "Couldn't load/unpack the cartridge (" + (local or EGG_URL) + ") — " + str(e)

        agents_path = os.path.join(twin_root, "twin", "agents")
        # 3: boot the twin (best-effort; graceful if no brainstem.py)
        pid, status = None, "unpacked"
        if bspy:
            try:
                env = dict(os.environ, AGENTS_PATH=agents_path, PORT=str(port),
                           BRAINSTEM_PORT=str(port), BRAINSTEM_HOME=twin_root)
                proc = subprocess.Popen([sys.executable, bspy], cwd=twin_root, env=env,
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                pid, status = proc.pid, "running"
                time.sleep(1)
            except Exception as e:
                status = "unpacked (boot failed: %s)" % e

        # 4: register for twin-chat federation
        _register({
            "id": TWIN_ID, "name": TWIN_NAME, "port": port, "pid": pid, "status": status,
            "chat": "http://127.0.0.1:%d/chat" % port,
            "agents_path": agents_path, "soul": "Cowork Cookbook — recipe→agent converter (WorkIQ)",
            "egg": EGG_URL, "hatched": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        })

        if status == "running":
            return ("🎮 Inserted the Cowork Cookbook cartridge — hatched as its own twin.\n"
                    "Port %d · twin-chat http://127.0.0.1:%d/chat · registered in twins.json.\n"
                    "The global brainstem can now collaborate with it over twin-chat. "
                    "It carries the recipe→agent converter (WorkIQ); ask it to list or convert a recipe." % (port, port))
        return ("Unpacked the Cowork Cookbook cartridge to %s and registered it (status: %s).\n"
                "No brainstem.py found to auto-boot — start one with AGENTS_PATH=%s on a free port, "
                "or set BRAINSTEM_PY and re-run me.\n%s" % (twin_root, status, agents_path, plan))


if __name__ == "__main__":
    print(CoworkCookbookAgent().perform(dry_run=True))
