#!/usr/bin/env python3
"""
rapp-dv — the RAPP Dataverse CLI.

Hatches the first RAPP "brainstem" into a real, OUT-OF-THE-BOX Dataverse environment using an
**application user** (server-to-server OAuth client credentials), so you can then chat with it in
Copilot Studio. No custom tables, no custom fields, no solution import.

It uses the SAME deterministic primary-key GUIDs as the static digital twin
(github.com/kody-w/rapp-dataverse -> dataverse/), so the real instance and the vTwin stay 1:1
and can be synced by upsert-by-id.

Auth: register an app, add it as an Application User in your environment with Create/Read/Write on
the OOTB account, contact, and annotation tables. Then:

    export RAPP_DV_URL=https://yourorg.crm.dynamics.com
    export RAPP_DV_TENANT=<tenant-guid>
    export RAPP_DV_CLIENT_ID=<app-client-id>
    export RAPP_DV_CLIENT_SECRET=<app-client-secret>

    python rapp_dv.py whoami          # verify the connection
    python rapp_dv.py hatch           # create the first RAPP brainstem (idempotent)
    python rapp_dv.py agents list
    python rapp_dv.py chat "what is 6 * 7?"   # local grounded preview against real Dataverse

See README.md for the full app-user setup and the Copilot Studio wiring.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.parse
import urllib.request

API_VERSION = "v9.2"
SCHEMA = f"api/data/{API_VERSION}"

# The global vTwin — a public, server-less static Dataverse (GitHub raw). Used automatically
# whenever no real Dataverse is configured, so the user is NEVER blocked by lacking an instance.
STATIC_BASE = "https://raw.githubusercontent.com/kody-w/rapp-dataverse/main/twin"

DEFAULT_SOUL = (
    "You are RAPP, a helpful Microsoft assistant running entirely on out-of-the-box Dataverse. "
    "Be concise, accurate, and honest about which agents you actually call. Use shared memory for "
    "common knowledge and user memory for the current person."
)

# Default agents the brainstem hatches with. The full agent.py is stored in Dataverse (sourcecode).
DEFAULT_AGENTS = [
    {
        "name": "EchoAgent",
        "description": "Echo back the provided text. Useful for testing the agent dispatch path.",
        "manifest": {"schema": "rapp-agent/1.0", "name": "@rapp/echo", "version": "1.0.0"},
        "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
        "kind": "python",
        "enabled": True,
        "sourcecode": (
            "from basic_agent import BasicAgent\n\n"
            "class EchoAgent(BasicAgent):\n"
            "    def __init__(self):\n"
            "        self.name = \"EchoAgent\"\n"
            "        self.metadata = {\"name\": self.name, \"description\": \"Echo text.\",\n"
            "            \"parameters\": {\"type\": \"object\", \"properties\": {\"text\": {\"type\": \"string\"}}, \"required\": [\"text\"]}}\n"
            "        super().__init__()\n\n"
            "    def perform(self, text=\"\", **kwargs):\n"
            "        return f\"Echo: {text}\"\n"
        ),
    },
    {
        "name": "CalculatorAgent",
        "description": "Evaluate a basic arithmetic expression like '6 * 7' and return the result.",
        "manifest": {"schema": "rapp-agent/1.0", "name": "@rapp/calculator", "version": "1.0.0"},
        "parameters": {"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]},
        "kind": "python",
        "enabled": True,
        "sourcecode": (
            "import ast, operator\n"
            "from basic_agent import BasicAgent\n\n"
            "_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}\n\n"
            "def _ev(n):\n"
            "    if isinstance(n, ast.Constant): return n.value\n"
            "    if isinstance(n, ast.BinOp): return _OPS[type(n.op)](_ev(n.left), _ev(n.right))\n"
            "    raise ValueError('unsupported')\n\n"
            "class CalculatorAgent(BasicAgent):\n"
            "    def __init__(self):\n"
            "        self.name = \"CalculatorAgent\"\n"
            "        self.metadata = {\"name\": self.name, \"description\": \"Evaluate arithmetic.\",\n"
            "            \"parameters\": {\"type\": \"object\", \"properties\": {\"expression\": {\"type\": \"string\"}}, \"required\": [\"expression\"]}}\n"
            "        super().__init__()\n\n"
            "    def perform(self, expression=\"\", **kwargs):\n"
            "        try: return str(_ev(ast.parse(expression, mode='eval').body))\n"
            "        except Exception as e: return f'Error: {e}'\n"
        ),
    },
    {
        "name": "ManageMemory",
        "description": "Store a durable memory. Memory scope is shared (the RAPP account) or user (a contact).",
        "manifest": {"schema": "rapp-agent/1.0", "name": "@rapp/manage-memory", "version": "1.0.0"},
        "parameters": {"type": "object", "properties": {
            "memory_type": {"type": "string"}, "content": {"type": "string"},
            "scope": {"type": "string", "enum": ["shared", "user"]}}, "required": ["content"]},
        "kind": "dataverse",
        "enabled": True,
        "sourcecode": "",  # native: POST an annotation subject='rapp.memory' (see README)
    },
    {
        "name": "ContextMemory",
        "description": "Recall stored memories. Shared + user memory is already injected into the brainstem each turn.",
        "manifest": {"schema": "rapp-agent/1.0", "name": "@rapp/context-memory", "version": "1.0.0"},
        "parameters": {"type": "object", "properties": {"full_recall": {"type": "boolean"}}, "required": []},
        "kind": "dataverse",
        "enabled": True,
        "sourcecode": "",  # native: List rows annotations subject='rapp.memory' (see README)
    },
]


# ── identity (must match the static twin's guid() exactly to stay 1:1) ───────

def guid(seed: str) -> str:
    h = hashlib.md5(seed.encode()).hexdigest()
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


RAPP_ACCOUNT_ID = guid("account:rapp-system")


# ── config + auth ────────────────────────────────────────────────────────────

class Config:
    def __init__(self, args):
        self.url = (args.url or os.getenv("RAPP_DV_URL", "")).rstrip("/")
        self.tenant = args.tenant or os.getenv("RAPP_DV_TENANT", "")
        self.client_id = args.client_id or os.getenv("RAPP_DV_CLIENT_ID", "")
        self.client_secret = args.client_secret or os.getenv("RAPP_DV_CLIENT_SECRET", "")
        self.dry_run = getattr(args, "dry_run", False)
        self.static = (getattr(args, "static", None) or os.getenv("RAPP_DV_STATIC") or STATIC_BASE).rstrip("/")
        self.force_vtwin = getattr(args, "vtwin", False)
        self.force_online = getattr(args, "online", False)
        self._token = None

    @property
    def has_creds(self) -> bool:
        return all([self.url, self.tenant, self.client_id, self.client_secret])

    @property
    def offline(self) -> bool:
        """True → serve reads from the global vTwin. Default whenever no real Dataverse is set."""
        if self.force_online:
            return False
        return self.force_vtwin or not self.has_creds

    @property
    def mode(self) -> str:
        return "vTwin · global static Dataverse" if self.offline else f"connected · {self.url}"

    def require(self):
        """Required only for live writes against a real Dataverse."""
        missing = [k for k in ("url", "tenant", "client_id", "client_secret") if not getattr(self, k)]
        if missing:
            sys.exit(f"error: this needs a real Dataverse connection: set "
                     f"{', '.join('RAPP_DV_' + m.upper() for m in missing)} "
                     f"(or run read-only against the vTwin).")

    def token(self) -> str:
        if self._token:
            return self._token
        self.require()
        data = urllib.parse.urlencode({
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": f"{self.url}/.default",
        }).encode()
        url = f"https://login.microsoftonline.com/{self.tenant}/oauth2/v2.0/token"
        req = urllib.request.Request(url, data=data, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                self._token = json.loads(r.read())["access_token"]
        except urllib.error.HTTPError as e:
            sys.exit(f"auth failed ({e.code}): {e.read().decode()[:300]}")
        return self._token


def api(cfg: Config, method: str, path: str, body=None, headers=None, parse=True):
    """Call the Dataverse Web API. path is relative to /api/data/v9.2/ or absolute ($ paths)."""
    full = path if path.startswith("http") else f"{cfg.url}/{SCHEMA}/{path.lstrip('/')}"
    h = {
        "Authorization": f"Bearer {cfg.token()}",
        "Accept": "application/json",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Content-Type": "application/json; charset=utf-8",
    }
    if headers:
        h.update(headers)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(full, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
            if not parse or not raw:
                return {"status": r.status}
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        detail = e.read().decode()[:500]
        sys.exit(f"{method} {path} failed ({e.code}): {detail}")


def upsert(cfg: Config, entityset: str, record_id: str, payload: dict, label: str):
    """Upsert by id (PATCH to a keyed URL creates-or-updates in Dataverse)."""
    if cfg.offline or cfg.dry_run:
        tag = "vtwin" if cfg.offline else "dry-run"
        print(f"  [{tag}] upsert {entityset}({record_id})  {label}")
        return
    api(cfg, "PATCH", f"{entityset}({record_id})", body=payload,
        headers={"Prefer": "return=minimal"}, parse=False)
    print(f"  ✓ {entityset}({record_id})  {label}")


# ── note (annotation) helpers ────────────────────────────────────────────────

def note_payload(subject: str, notetext: dict, regarding_set: str, regarding_id: str) -> dict:
    bind = "objectid_account@odata.bind" if regarding_set == "accounts" else "objectid_contact@odata.bind"
    return {
        "subject": subject,
        "notetext": json.dumps(notetext, ensure_ascii=False),
        "isdocument": False,
        bind: f"/{regarding_set}({regarding_id})",
    }


# ── twin sync (hatcher) + compare ────────────────────────────────────────────

_ID_FIELD = {"accounts": "accountid", "contacts": "contactid", "annotations": "annotationid"}


def _content_hash(parts) -> str:
    return hashlib.sha256("||".join("" if p is None else str(p) for p in parts).encode()).hexdigest()[:12]


def _row_id(es, row):
    return row.get(_ID_FIELD[es])


def _row_hash(es, row):
    if es == "accounts":
        return _content_hash([row.get("name"), row.get("description")])
    if es == "contacts":
        return _content_hash([row.get("fullname"), row.get("emailaddress1")])
    return _content_hash([row.get("subject"), row.get("notetext")])


def _load_odata_source(cfg, src=None):
    """Load a brainstem (accounts/contacts/annotations, with ids) from a source.
    Default source = the global vTwin. src may be a raw/Pages dataverse base or a local folder."""
    base = (src or cfg.static).rstrip("/")
    if "/api/data/" not in base:
        base = f"{base}/{SCHEMA}"
    out = {}
    for es in ("accounts", "contacts", "annotations"):
        if base.startswith("http"):
            with urllib.request.urlopen(f"{base}/{es}.json", timeout=30) as r:
                out[es] = json.loads(r.read()).get("value", [])
        else:
            out[es] = json.loads(open(os.path.join(base, f"{es}.json"), encoding="utf-8").read()).get("value", [])
    return out


def _defaults_source():
    """The bundled minimal brainstem in the same shape (ids + notetext strings)."""
    def note(seed, subj, payload):
        return {"annotationid": guid("annotation:" + seed), "subject": subj,
                "notetext": json.dumps(payload, ensure_ascii=False),
                "_objectid_value": RAPP_ACCOUNT_ID, "objecttypecode": "account"}
    anns = [note("config", "rapp.config", {"maxrounds": 3, "voice_enabled": False})]
    for a in DEFAULT_AGENTS:
        anns.append(note("agent-" + a["name"].lower(), "rapp.agent", a))
    anns.append(note("memory-hatch", "rapp.memory",
                     {"memory_type": "fact", "content": "RAPP was hatched on out-of-the-box Dataverse via rapp-dv."}))
    return {"accounts": [{"accountid": RAPP_ACCOUNT_ID, "name": "RAPP System", "description": DEFAULT_SOUL}],
            "contacts": [], "annotations": anns}


def _apply_brainstem(cfg, data):
    """Twin-sync write: upsert a full brainstem (accounts -> contacts -> annotations) by id."""
    n = 0
    for a in data.get("accounts", []):
        upsert(cfg, "accounts", a["accountid"],
               {"name": a.get("name"), "description": a.get("description"), "accountcategorycode": 1},
               a.get("name", "")); n += 1
    for c in data.get("contacts", []):
        upsert(cfg, "contacts", c["contactid"],
               {"firstname": c.get("firstname"), "lastname": c.get("lastname"),
                "emailaddress1": c.get("emailaddress1")}, c.get("fullname", "")); n += 1
    for an in data.get("annotations", []):
        rset = "accounts" if an.get("objecttypecode") == "account" else "contacts"
        upsert(cfg, "annotations", an["annotationid"],
               note_payload(an["subject"], json.loads(an["notetext"]), rset, an["_objectid_value"]),
               an["subject"]); n += 1
    return n


def _all_rapp_annotations(cfg):
    if cfg.offline:
        return [n for n in _static_collection(cfg, "annotations") if str(n.get("subject", "")).startswith("rapp.")]
    flt = urllib.parse.quote("startswith(subject,'rapp.')")
    return api(cfg, "GET", f"annotations?$filter={flt}&$select=annotationid,subject,notetext,_objectid_value,objecttypecode").get("value", [])


def _read_target(cfg):
    """The side compared to the reference: the connected instance, or (offline) the bundled defaults."""
    if cfg.offline:
        return _defaults_source(), "bundled defaults (offline)"
    acct = api(cfg, "GET", f"accounts({RAPP_ACCOUNT_ID})?$select=accountid,name,description")
    accounts = [acct] if acct.get("accountid") else []
    contacts = api(cfg, "GET", "contacts?$select=contactid,fullname,emailaddress1").get("value", [])
    return {"accounts": accounts, "contacts": contacts, "annotations": _all_rapp_annotations(cfg)}, f"connected · {cfg.url}"


def _do_compare(cfg, src=None, label="compare"):
    """Diff the target (connected instance / defaults) against a reference brainstem (default: vTwin)."""
    ref = _load_odata_source(cfg, src)
    tgt, tgt_label = _read_target(cfg)
    refname = "global vTwin" if not src else f"source {src}"
    print(f"=== {label}: [{tgt_label}]  vs  reference [{refname}] ===")
    drift_total = miss_total = 0
    for es in ("accounts", "contacts", "annotations"):
        refmap = {_row_id(es, r): _row_hash(es, r) for r in ref.get(es, [])}
        tgtmap = {_row_id(es, r): _row_hash(es, r) for r in tgt.get(es, [])}
        drift = [i for i in refmap if i in tgtmap and tgtmap[i] != refmap[i]]
        missing = [i for i in refmap if i not in tgtmap]
        in_sync = [i for i in refmap if tgtmap.get(i) == refmap[i]]
        drift_total += len(drift); miss_total += len(missing)
        print(f"  {es:12} in-sync {len(in_sync):2} · drift {len(drift)} · missing {len(missing)}  (ref {len(refmap)})")
    ok = drift_total == 0 and miss_total == 0
    print(f"  → {'✅ IN SYNC with the global brainstem' if ok else f'⚠ {drift_total} drifted · {miss_total} missing'}")
    return ok


# ── commands ─────────────────────────────────────────────────────────────────

def cmd_hatch(cfg: Config, args):
    """Twin-sync hatcher: replicate a full brainstem (default: the global vTwin) into this instance,
    by upsert-by-id, so the instance becomes identical to the global brainstem."""
    if args.defaults:
        data = _defaults_source()
        if args.soul_file:
            data["accounts"][0]["description"] = open(args.soul_file, encoding="utf-8").read().strip()
        srclabel = "the bundled minimal brainstem"
    else:
        data = _load_odata_source(cfg, args.src)
        srclabel = f"source {args.src}" if args.src else "the global vTwin brainstem"
    print(f"Twin-sync hatch ({cfg.mode}) — replicating {srclabel} into this instance (OOTB only)…\n")

    count = _apply_brainstem(cfg, data)

    if cfg.offline:
        print(f"\n   Would sync {count} rows · RAPP System id {RAPP_ACCOUNT_ID}")
        print("(vTwin preview — read-only. Set RAPP_DV_* to hatch into a real instance.)")
    else:
        print(f"\n🐣 Brainstem hatched — {count} rows synced.")
        _do_compare(cfg, args.src, label="post-hatch verify")
        print("\nNext: wire Copilot Studio (README → 'Chat in Copilot Studio'). "
              "Re-check anytime with `rapp-dv compare` (vs the global vTwin).")


def cmd_compare(cfg: Config, args):
    """Compare this instance (or the bundled defaults, offline) against the global vTwin brainstem."""
    _do_compare(cfg, getattr(args, "src", None))




def cmd_agents_list(cfg: Config, args):
    notes = _rapp_notes(cfg, "rapp.agent")
    print(f"# agents ({cfg.mode})")
    for n in notes:
        a = json.loads(n["notetext"])
        print(f"- {a.get('name'):16} [{a.get('kind')}] {'on' if a.get('enabled') else 'OFF'}  {a.get('description','')[:60]}")


def cmd_memory_list(cfg: Config, args):
    notes = _rapp_notes(cfg, "rapp.memory")
    print(f"# memory ({cfg.mode})")
    for n in notes:
        m = json.loads(n["notetext"])
        scope = "shared" if n.get("_objectid_value") == RAPP_ACCOUNT_ID else "user"
        print(f"- [{scope}] ({m.get('memory_type','')}) {m.get('content','')}")


def _static_collection(cfg: Config, entityset: str):
    """Fetch an OOTB collection from the global vTwin (public GitHub raw)."""
    url = f"{cfg.static}/{SCHEMA}/{entityset}.json"
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read()).get("value", [])


def _rapp_notes(cfg: Config, subject: str):
    """Read rapp.* annotations from the vTwin (offline) or the live Web API (connected)."""
    if cfg.offline:
        return [n for n in _static_collection(cfg, "annotations") if n.get("subject") == subject]
    flt = urllib.parse.quote(f"subject eq '{subject}'")
    return api(cfg, "GET", f"annotations?$filter={flt}&$select=subject,notetext,_objectid_value").get("value", [])


def _read_soul(cfg: Config) -> str:
    if cfg.offline:
        for a in _static_collection(cfg, "accounts"):
            if a.get("accountid") == RAPP_ACCOUNT_ID or a.get("name") == "RAPP System":
                return a.get("description", DEFAULT_SOUL)
        return DEFAULT_SOUL
    return api(cfg, "GET", f"accounts({RAPP_ACCOUNT_ID})?$select=description").get("description", DEFAULT_SOUL)


def cmd_whoami(cfg: Config, args):
    if cfg.offline:
        print(f"Mode: {cfg.mode}")
        print(f"vTwin: {cfg.static}")
        try:
            with urllib.request.urlopen(f"{cfg.static}/registry.json", timeout=30) as r:
                reg = json.loads(r.read())
            print(f"Simulated org: {reg.get('org_url')}  ·  {reg.get('summary')}")
        except Exception:
            pass
        print("No real Dataverse required — reads are served from the global vTwin. "
              "Set RAPP_DV_URL/TENANT/CLIENT_ID/CLIENT_SECRET to connect a real instance for writes.")
        return
    who = api(cfg, "GET", "WhoAmI")
    print(json.dumps(who, indent=2))
    print(f"\nConnected to {cfg.url} as application user {who.get('UserId')}.")


def cmd_seed(cfg: Config, args):
    """Alias for hatch from an explicit source — apply a brainstem export by upsert-by-id (twin sync)."""
    if cfg.offline:
        sys.exit("seed/sync writes to a real Dataverse — set RAPP_DV_* to connect "
                 "(the global vTwin is read-only).")
    n = _apply_brainstem(cfg, _load_odata_source(cfg, args.src))
    print(f"Twin applied — {n} rows synced (upsert-by-id).")


def cmd_chat(cfg: Config, args):
    """Local grounded preview: assemble the brainstem context from Dataverse (real or vTwin).
    Inference happens in Copilot Studio; this proves the brainstem is hatched and grounded."""
    soul = _read_soul(cfg)
    agents = [json.loads(n["notetext"]) for n in _rapp_notes(cfg, "rapp.agent")]
    mem = _rapp_notes(cfg, "rapp.memory")
    shared = [json.loads(n["notetext"]).get("content", "") for n in mem
              if n.get("_objectid_value") == RAPP_ACCOUNT_ID]
    user = [json.loads(n["notetext"]).get("content", "") for n in mem
            if n.get("_objectid_value") != RAPP_ACCOUNT_ID]
    print(f"=== grounded brainstem context ({cfg.mode}) ===")
    print("SOUL:", soul)
    print("AGENTS:", ", ".join(f"{a['name']}({a['kind']})" for a in agents) or "(none)")
    print("SHARED MEMORY:", "; ".join(shared) or "(none)")
    print("USER MEMORY:", "; ".join(user) or "(none)")
    print("USER INPUT:", args.message)
    print("\nThis is exactly what the Copilot Studio router prompt grounds on "
          "(shared vs user memory, per the brainstem). Create the agent + flow per README "
          "to get live replies.")


def cmd_selftest(cfg: Config, args):
    """Offline: verify the CLI's identity scheme is 1:1 with the static twin."""
    expected = "8ca2fe51-9671-bc68-b70d-ff88641b0fb2"  # twin's RAPP System accountid
    ok = RAPP_ACCOUNT_ID == expected
    print(f"RAPP System accountid: {RAPP_ACCOUNT_ID}  (twin expects {expected})")
    print("✅ 1:1 with the static twin" if ok else "❌ identity mismatch — NOT 1:1")
    sys.exit(0 if ok else 1)


def main():
    p = argparse.ArgumentParser(prog="rapp-dv", description="RAPP Dataverse CLI — hatch the first brainstem on OOTB Dataverse.")
    p.add_argument("--url"); p.add_argument("--tenant")
    p.add_argument("--client-id", dest="client_id"); p.add_argument("--client-secret", dest="client_secret")
    p.add_argument("--dry-run", action="store_true", help="print writes without making them")
    p.add_argument("--static", help="vTwin base URL (default: the public global static Dataverse)")
    p.add_argument("--vtwin", action="store_true", help="force vTwin (global static, read-only) mode")
    p.add_argument("--online", action="store_true", help="force a real Dataverse connection")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("whoami", help="verify the application-user connection")
    h = sub.add_parser("hatch", help="twin-sync the full brainstem into this instance (idempotent)")
    h.add_argument("--from", dest="src", default=None,
                   help="brainstem source (raw/Pages base or folder); default: the global vTwin")
    h.add_argument("--defaults", action="store_true",
                   help="hatch the bundled minimal brainstem instead of replicating the global vTwin")
    h.add_argument("--soul-file", help="override the soul (only meaningful with --defaults)")
    al = sub.add_parser("agents"); al.add_argument("action", choices=["list"])
    ml = sub.add_parser("memory"); ml.add_argument("action", choices=["list"])
    s = sub.add_parser("seed", help="apply a brainstem export by upsert-by-id (twin sync)")
    s.add_argument("src", help="folder or raw base URL containing accounts/contacts/annotations .json")
    cp = sub.add_parser("compare", help="compare this instance against the global vTwin brainstem")
    cp.add_argument("--from", dest="src", default=None, help="reference source (default: global vTwin)")
    c = sub.add_parser("chat", help="local grounded preview against live Dataverse")
    c.add_argument("message")
    sub.add_parser("selftest", help="offline: verify 1:1 identity with the static twin")

    args = p.parse_args()
    cfg = Config(args)
    dispatch = {
        "whoami": cmd_whoami, "hatch": cmd_hatch, "seed": cmd_seed, "chat": cmd_chat,
        "compare": cmd_compare, "selftest": cmd_selftest,
        "agents": cmd_agents_list, "memory": cmd_memory_list,
    }
    dispatch[args.cmd](cfg, args)


if __name__ == "__main__":
    main()
