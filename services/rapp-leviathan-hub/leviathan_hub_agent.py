"""leviathan_hub_agent.py — v0.1.0

SELF-CONTAINED RAPP agent that hatches frozen Leviathans into a live
brainstem. Drop this single file into any RAPP brainstem's agents/
directory and you get one tool, "LeviathanHub", that can:

  • list eggs available locally OR on the public hub (kody-w/rapp-leviathan-hub)
  • download an egg from the hub
  • hatch an egg into a living organism (writes the tree to ~/.rapp/,
    retrofits per-cell agent.py at every layer, drops a brainstem shim,
    auto-discovered by the brainstem as Ask<Slug>)
  • freeze a live leviathan into a portable .leviathan.egg file

A `.leviathan.egg` is a single JSON file (schema rapp-leviathan-egg/1.0)
containing the entire on-disk state of a leviathan — rappid, every
estate.json, every soul.md, every persona prompt. Eggs are portable
across machines and operators. Hatch one anywhere and the same
multicellular organism wakes up. Composes with @kody-w/rapp_leviathan_factory
(which mints inert organisms from intent) and @kody-w/wrap_leviathan
(which wires inert organisms into a brainstem).

Self-contained — inlines the wrapped_organism cell runtime so hatch
works even if @kody-w/wrap_leviathan isn't installed.

Implements WRAPPED_ORGANISM_SPEC.md v1.0.

API
===

  LeviathanHub(action="hub_status")
  LeviathanHub(action="list_eggs")
  LeviathanHub(action="list_eggs", remote=True)
  LeviathanHub(action="download", egg="kody")
  LeviathanHub(action="hatch",    egg="kody")
  LeviathanHub(action="hatch",    egg="/path/to/local.leviathan.egg")
  LeviathanHub(action="freeze",   slug="my-twin", out_dir="~/eggs/")

Default hub: https://raw.githubusercontent.com/kody-w/rapp-leviathan-hub/main/
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import socket
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone


try:
    from agents.basic_agent import BasicAgent
except ModuleNotFoundError:
    try:
        from openrappter.agents.basic_agent import BasicAgent
    except ModuleNotFoundError:
        class BasicAgent:                       # standalone fallback
            def __init__(self, name, metadata):
                self.name, self.metadata = name, metadata


__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@kody-w/leviathan_hub",
    "version": "0.1.0",
    "display_name": "LeviathanHub",
    "description": (
        "Distribute Wrapped-Organism Leviathans as portable .leviathan.egg "
        "files. List + download + hatch eggs from the public hub "
        "(kody-w/rapp-leviathan-hub), or freeze a local live leviathan "
        "into a shareable egg. Hatching writes the full tree to ~/.rapp/, "
        "retrofits per-cell agent.py at every layer per "
        "WRAPPED_ORGANISM_SPEC.md, and drops a brainstem shim so the "
        "leviathan immediately appears as an Ask<Slug> tool. Self-"
        "contained: one file, no sibling deps, inlines the cell runtime."
    ),
    "author": "kody-w",
    "industry": "meta",
    "tags": [
        "meta", "hub", "registry", "egg", "leviathan",
        "wrapped-organism", "hatch", "freeze", "distribution",
        "singleton", "self-contained",
    ],
    "category": "meta",
    "quality_tier": "community",
    "requires_env": [],
    "dependencies": ["@rapp/basic_agent"],
    "example_call": {
        "args": {"action": "hatch", "egg": "kody"},
    },
}


# ─── Configuration ──────────────────────────────────────────────────────────

HOME = pathlib.Path.home()
RAPP_HOME = HOME / ".rapp"
LEVIATHANS_ROOT = pathlib.Path(os.environ.get(
    "RAPP_LEVIATHANS_ROOT", RAPP_HOME / "leviathans"))
ESTATES_ROOT = pathlib.Path(os.environ.get(
    "RAPP_ESTATES_ROOT", RAPP_HOME / "estates"))
EGGS_CACHE = RAPP_HOME / "egg_cache"
WRAPPED_ORGANISM_INSTALL = RAPP_HOME / "wrapped_organism"

HUB_BASE = os.environ.get(
    "RAPP_LEVIATHAN_HUB_URL",
    "https://raw.githubusercontent.com/kody-w/rapp-leviathan-hub/main",
)
HUB_INDEX_URL = f"{HUB_BASE}/index.json"

BRAINSTEM_AGENTS_CANDIDATES = [
    HOME / ".brainstem" / "src" / "rapp_brainstem" / "agents",
    HOME / ".brainstem" / "agents",
    pathlib.Path("/opt/rapp/brainstem/agents"),
]


# ─── Estate organ vocabulary (mirrors the factory) ─────────────────────────

ESTATE_ORGAN_QUESTIONS = {
    "sanctum": ("soul",  "Who am I?"),
    "polity":  ("will",  "What shall I do?"),
    "works":   ("hands", "What shall I make?"),
    "press":   ("eyes",  "What is true?"),
    "commons": ("mouth", "Who shall I speak to?"),
}


# ─── Inlined: wrapped_organism/cell.py ─────────────────────────────────────
# Installed verbatim to ~/.rapp/wrapped_organism/cell.py during hatch.
# Same source as kody-w/rappterbook scripts/wrapped_organism/cell.py.

INLINE_CELL_PY = r'''"""wrapped_organism/cell.py — runtime for one cell of a wrapped digital organism.

Implements the Wrapped Organism Spec v1.0 §II.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import re
import urllib.error
import urllib.request


SCHEMA_VERSION = "rapp-cell/1.0"
VALID_LAYERS = {"leviathan", "estate", "industry", "neighborhood", "factory"}
MANIFEST_REQUIRED_KEYS = {"schema", "layer", "path", "context", "children", "souls"}


class ProtocolError(ValueError):
    pass


def validate_manifest(manifest):
    missing = MANIFEST_REQUIRED_KEYS - set(manifest.keys())
    if missing:
        raise ProtocolError(f"manifest missing keys: {sorted(missing)}")
    if manifest["schema"] != SCHEMA_VERSION:
        raise ProtocolError(f"unsupported schema: {manifest['schema']!r}")
    if manifest["layer"] not in VALID_LAYERS:
        raise ProtocolError(f"invalid layer: {manifest['layer']!r}")
    if not isinstance(manifest["children"], list):
        raise ProtocolError("children must be a list")
    if not isinstance(manifest["souls"], list):
        raise ProtocolError("souls must be a list")
    if not isinstance(manifest["context"], str) or not manifest["context"].strip():
        raise ProtocolError("context must be a non-empty string")


def is_leaf(manifest):
    return not manifest.get("children")


def shape(transcript, manifest):
    return transcript + [{"role": "system", "content": manifest["context"]}]


_TOK_RE = re.compile(r"[A-Za-z0-9_\-]+")


def _clean_reply(raw, children):
    if not raw:
        return ""
    s = raw.strip().strip("\"'`").strip()
    if s in children:
        return s
    for tok in _TOK_RE.findall(raw):
        if tok in children:
            return tok
        for c in children:
            if tok.lower() == c.lower():
                return c
    return s


def route(transcript, manifest, brain):
    children = manifest["children"]
    if not children:
        return None
    ask = transcript + [{
        "role": "user",
        "content": (f"You must pick exactly one child of this cell to route to. "
                    f"Valid children: {children}. "
                    f"Reply with ONLY the slug, no punctuation, no explanation."),
    }]
    raw = brain.chat(ask, temperature=0, max_tokens=32)
    choice = _clean_reply(raw, children)
    if choice not in children:
        raise ProtocolError(f"router returned invalid child: {raw!r} (valid: {children})")
    return choice


def hotload(cell_dir, child_slug):
    target = cell_dir / child_slug / "agent.py"
    if not target.exists():
        raise FileNotFoundError(f"no cell at {target}")
    spec = importlib.util.spec_from_file_location(
        f"wrapped_cell_{child_slug}_{id(target)}", target)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_souls_chain(transcript, manifest, souls_dir, brain):
    reply = ""
    for soul_name in manifest.get("souls") or []:
        soul_file = souls_dir / f"{soul_name}.md"
        soul_prompt = (soul_file.read_text(encoding="utf-8") if soul_file.exists()
                       else f"You are the {soul_name} persona.")
        chain = [{"role": "system", "content": soul_prompt}] + transcript
        if reply:
            chain.append({"role": "assistant", "content": reply})
        reply = brain.chat(chain)
    if not manifest.get("souls"):
        reply = brain.chat(transcript)
    return reply


def perform(input_, manifest, cell_dir, brain, trace=None):
    validate_manifest(manifest)
    if trace is None:
        trace = []
    transcript = shape(
        input_ if isinstance(input_, list) else [{"role": "user", "content": str(input_)}],
        manifest,
    )
    trace.append({"path": manifest["path"], "layer": manifest["layer"]})
    if is_leaf(manifest):
        response = run_souls_chain(transcript, manifest, cell_dir / "souls", brain)
        return {"response": response, "trace": trace, "leaf_path": manifest["path"]}
    child = route(transcript, manifest, brain)
    child_cell = hotload(cell_dir, child)
    return child_cell.perform_local(transcript, brain, trace)


class BrainstemBrain:
    def __init__(self, url="http://localhost:7071/chat", timeout=180):
        self.url, self.timeout = url, timeout

    def chat(self, transcript, **_kw):
        sys_p = [m["content"] for m in transcript if m["role"] == "system"]
        user_p = [m["content"] for m in transcript if m["role"] == "user"]
        asst_p = [m["content"] for m in transcript if m["role"] == "assistant"]
        prompt = ""
        if sys_p: prompt += "[CONTEXT]\n" + "\n\n".join(sys_p) + "\n[/CONTEXT]\n\n"
        if asst_p: prompt += "[PRIOR ASSISTANT]\n" + asst_p[-1] + "\n[/PRIOR ASSISTANT]\n\n"
        if user_p:
            if len(user_p) > 1:
                prompt += "[ORIGINAL INPUT]\n" + user_p[0] + "\n[/ORIGINAL INPUT]\n\n"
                prompt += "[CURRENT REQUEST]\n" + user_p[-1] + "\n[/CURRENT REQUEST]"
            else:
                prompt += user_p[0]
        body = json.dumps({"user_input": prompt}).encode("utf-8")
        req = urllib.request.Request(self.url, data=body,
            headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                data = json.loads(r.read().decode("utf-8"))
        except urllib.error.URLError as e:
            raise RuntimeError(f"brainstem unreachable: {e}")
        return (data.get("response") or "").strip()
'''


# ─── Per-cell agent.py template (used by retrofit) ──────────────────────────

CELL_TEMPLATE = '''"""Generated cell for {path}. Layer: {layer}. Children: {children_repr}
{souls_line}
Hatched from {slug}.leviathan.egg by leviathan_hub. Regenerate via LeviathanHub(action="hatch", egg="{slug}").
"""
from __future__ import annotations
import pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
_PKG_DIR = pathlib.Path.home() / ".rapp"
if str(_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(_PKG_DIR))

from wrapped_organism.cell import perform, validate_manifest, BrainstemBrain  # noqa


__manifest__ = {manifest_repr}

validate_manifest(__manifest__)


def perform_local(transcript, brain, trace):
    return perform(transcript, __manifest__, HERE, brain, trace)


def perform_root(input_text, brain=None):
    return perform(input_text, __manifest__, HERE, brain or BrainstemBrain())


if __name__ == "__main__":
    import sys as _s
    print(perform_root(_s.argv[1] if len(_s.argv) > 1 else "Hello.")["response"])
'''


# ─── Brainstem shim template ────────────────────────────────────────────────

SHIM_TEMPLATE = '''"""{slug}_leviathan_agent.py — brainstem shim for {slug} (hatched from egg).

Hatched by LeviathanHub(action="hatch", egg="{slug}"). Registers ONE tool
("Ask{Cap}") that walks the {slug}-leviathan tree.
"""
from __future__ import annotations
import importlib.util, pathlib, sys, threading

try:
    from openrappter.agents.basic_agent import BasicAgent
except ImportError:
    from agents.basic_agent import BasicAgent


_RAPP_HOME = pathlib.Path.home() / ".rapp"
if str(_RAPP_HOME) not in sys.path:
    sys.path.insert(0, str(_RAPP_HOME))


ROOT = _RAPP_HOME / "leviathans" / "{slug}" / "agent.py"
_REENTRY = threading.local()


def _load_root():
    if not ROOT.exists():
        raise FileNotFoundError(
            f"{slug} root cell missing at {{ROOT}}. "
            f"Re-hatch via LeviathanHub(action='hatch', egg='{slug}')."
        )
    for cached in [k for k in list(sys.modules) if k.startswith("wrapped_organism")]:
        sys.modules.pop(cached, None)
    spec = importlib.util.spec_from_file_location("{slug}_root_cell", ROOT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class {Cap}LeviathanAgent(BasicAgent):
    def __init__(self):
        self.name = "Ask{Cap}"
        self.metadata = {{
            "name": self.name,
            "description": (
                "Route a question through the {slug}-leviathan — a multicellular "
                "Wrapped Organism hatched from an egg. The cell tree routes "
                "input to the appropriate leaf which generates the response."
            ),
            "parameters": {{
                "type": "object",
                "properties": {{"query": {{"type": "string"}}}},
                "required": ["query"],
            }},
        }}
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs):
        query = kwargs.get("query", "").strip()
        if not query:
            return {{"error": "query is required"}}
        if getattr(_REENTRY, "active", False):
            return ("(routing in progress — answer the prior routing "
                    "question with just the slug)")
        _REENTRY.active = True
        try:
            root = _load_root()
            result = root.perform_root(query)
            return {{
                "response": result.get("response", ""),
                "leaf": result.get("leaf_path", ""),
                "trace": " → ".join(s["path"] for s in result.get("trace", [])),
            }}
        except Exception as e:
            return {{"error": str(e), "type": type(e).__name__}}
        finally:
            _REENTRY.active = False
'''


# ════════════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════════════


def _ok(action, **extra):
    return json.dumps({"status": "ok", "action": action, **extra}, indent=2,
                      ensure_ascii=False)


def _err(action, message, **extra):
    return json.dumps({"status": "error", "action": action, "message": message,
                       **extra}, indent=2, ensure_ascii=False)


def _find_brainstem_agents_dir():
    for p in BRAINSTEM_AGENTS_CANDIDATES:
        if p.exists() and p.is_dir():
            return p
    return None


def _http_get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "leviathan-hub/0.1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _http_get_json(url, timeout=30):
    return json.loads(_http_get(url, timeout=timeout).decode("utf-8"))


def _install_wrapped_organism_runtime():
    """Write the inlined cell.py to ~/.rapp/wrapped_organism/."""
    WRAPPED_ORGANISM_INSTALL.mkdir(parents=True, exist_ok=True)
    (WRAPPED_ORGANISM_INSTALL / "__init__.py").write_text("", encoding="utf-8")
    (WRAPPED_ORGANISM_INSTALL / "cell.py").write_text(INLINE_CELL_PY, encoding="utf-8")
    pycache = WRAPPED_ORGANISM_INSTALL / "__pycache__"
    if pycache.exists():
        shutil.rmtree(pycache, ignore_errors=True)


def _manifest_repr(manifest):
    return json.dumps(manifest, indent=4, ensure_ascii=False).replace(
        "true", "True").replace("false", "False").replace("null", "None")


def _write_cell(target_dir, manifest, slug):
    target_dir.mkdir(parents=True, exist_ok=True)
    src = CELL_TEMPLATE.format(
        path=manifest["path"], layer=manifest["layer"],
        children_repr=manifest["children"] or "(leaf)",
        souls_line=(f"Souls: {manifest['souls']}\n" if manifest["souls"] else ""),
        slug=slug, manifest_repr=_manifest_repr(manifest),
    )
    (target_dir / "agent.py").write_text(src, encoding="utf-8")


# ─── Build per-layer manifests from estate.json data ───────────────────────


def _lev_manifest(slug, rappid, estates, tagline):
    return {
        "schema": "rapp-cell/1.0", "layer": "leviathan",
        "path": slug, "rappid": rappid,
        "context": (
            f"You are {slug}-leviathan — a full digital being with rappid {rappid}. "
            f"{tagline} You have {len(estates)} estate(s) reporting to you: {estates}. "
            f"When given input, decide which estate handles it."
        ),
        "children": list(estates), "souls": [],
    }


def _est_manifest(lev_slug, est_slug, est_json, rappid):
    organ, q = ESTATE_ORGAN_QUESTIONS.get(est_slug, ("?", "?"))
    industries = [i["id"] for i in est_json.get("industries", [])]
    intent = est_json.get("intent") or est_json.get("tagline") or ""
    return {
        "schema": "rapp-cell/1.0", "layer": "estate",
        "path": f"{lev_slug}/{est_slug}", "rappid": rappid,
        "context": (f"You are the {est_slug.title()} estate ({organ}) of "
                    f"{lev_slug}-leviathan. You answer: \"{q}\" {intent} "
                    f"Industries reporting to you: {industries}. "
                    f"Pick the one that handles the input."),
        "children": industries, "souls": [],
    }


def _ind_manifest(path_prefix, industry, rappid):
    nbh = [n["id"] for n in industry.get("neighborhoods", [])]
    return {
        "schema": "rapp-cell/1.0", "layer": "industry",
        "path": f"{path_prefix}/{industry['id']}", "rappid": rappid,
        "context": (f"You are the {industry.get('name', industry['id'])} industry. "
                    f"{industry.get('tagline','')} Neighborhoods: {nbh}. "
                    f"Pick the one for this input."),
        "children": nbh, "souls": [],
    }


def _nbh_manifest(path_prefix, nbh, rappid):
    factories = [f["id"] for f in nbh.get("factories", [])]
    return {
        "schema": "rapp-cell/1.0", "layer": "neighborhood",
        "path": f"{path_prefix}/{nbh['id']}", "rappid": rappid,
        "context": (f"You are the {nbh.get('name', nbh['id'])} neighborhood. "
                    f"{nbh.get('tagline','')} Factories: {factories}. "
                    f"Pick the one for this input."),
        "children": factories, "souls": [],
    }


def _fac_manifest(path_prefix, factory, rappid):
    return {
        "schema": "rapp-cell/1.0", "layer": "factory",
        "path": f"{path_prefix}/{factory['id']}", "rappid": rappid,
        "context": (f"You are the {factory.get('name', factory['id'])} factory. "
                    f"{factory.get('tagline','')} You are a leaf — your souls "
                    f"produce the actual output."),
        "children": [], "souls": list(factory.get("souls", [])),
    }


# ════════════════════════════════════════════════════════════════════════════
# Actions
# ════════════════════════════════════════════════════════════════════════════


def _hub_status():
    info = {
        "hub_base": HUB_BASE,
        "hub_index_url": HUB_INDEX_URL,
        "local_cache": str(EGGS_CACHE),
        "leviathans_root": str(LEVIATHANS_ROOT),
        "estates_root": str(ESTATES_ROOT),
        "runtime_install": str(WRAPPED_ORGANISM_INSTALL),
        "brainstem_agents_dir": str(_find_brainstem_agents_dir() or "(not found)"),
    }
    return _ok("hub_status", **info)


def _list_eggs(remote=False):
    out = {"local": [], "remote": []}

    # Local eggs in the cache
    if EGGS_CACHE.exists():
        for e in sorted(EGGS_CACHE.glob("*.leviathan.egg")):
            try:
                data = json.loads(e.read_text(encoding="utf-8"))
                out["local"].append({
                    "name": e.stem.replace(".leviathan", ""),
                    "path": str(e),
                    "size_kb": round(e.stat().st_size / 1024, 1),
                    "stats": data.get("stats", {}),
                    "frozen_at": data.get("_meta", {}).get("frozen_at"),
                })
            except Exception as ex:  # pragma: no cover
                out["local"].append({"name": e.name, "error": str(ex)})

    if remote:
        try:
            idx = _http_get_json(HUB_INDEX_URL)
            out["remote"] = idx.get("eggs", [])
        except Exception as e:
            out["remote_error"] = str(e)

    return _ok("list_eggs", **out, count_local=len(out["local"]),
               count_remote=len(out["remote"]))


def _download(egg_name):
    """Fetch <egg_name>.leviathan.egg from the hub into the local cache."""
    EGGS_CACHE.mkdir(parents=True, exist_ok=True)
    # Allow either bare name or full filename
    if egg_name.endswith(".leviathan.egg"):
        filename = egg_name
        stem = egg_name[:-len(".leviathan.egg")]
    else:
        stem = egg_name
        filename = f"{egg_name}.leviathan.egg"
    url = f"{HUB_BASE}/eggs/{filename}"
    target = EGGS_CACHE / filename
    try:
        body = _http_get(url, timeout=60)
    except urllib.error.HTTPError as e:
        return _err("download", f"HTTP {e.code} fetching {url}")
    except Exception as e:
        return _err("download", f"{type(e).__name__}: {e}", url=url)
    target.write_bytes(body)
    return _ok("download", egg=stem, path=str(target),
               size_kb=round(len(body) / 1024, 1), source=url)


def _resolve_egg_path(egg_arg):
    """Accept: full local path, bare name (look in cache), or URL."""
    p = pathlib.Path(egg_arg).expanduser()
    if p.exists():
        return p
    # Try cache
    candidates = [
        EGGS_CACHE / egg_arg,
        EGGS_CACHE / f"{egg_arg}.leviathan.egg",
    ]
    for c in candidates:
        if c.exists():
            return c
    # Try downloading
    dl = json.loads(_download(egg_arg))
    if dl.get("status") == "ok":
        return pathlib.Path(dl["path"])
    return None


def _hatch(egg_arg, wire=True):
    """Materialize an egg as a live leviathan: dirs + cells + brainstem shim."""
    egg_path = _resolve_egg_path(egg_arg)
    if egg_path is None:
        return _err("hatch", f"egg not found and could not be downloaded: {egg_arg}")

    try:
        egg = json.loads(egg_path.read_text(encoding="utf-8"))
    except Exception as e:
        return _err("hatch", f"invalid egg file {egg_path}: {e}")

    if egg.get("schema") != "rapp-leviathan-egg/1.0":
        return _err("hatch", f"unsupported egg schema: {egg.get('schema')!r}")

    slug = egg["slug"]
    rappid = egg.get("rappid")

    # 1. Install runtime
    _install_wrapped_organism_runtime()

    # 2. Recreate ~/.rapp/leviathans/<slug>/
    lev_dir = LEVIATHANS_ROOT / slug
    lev_dir.mkdir(parents=True, exist_ok=True)
    (lev_dir / "rappid.json").write_text(
        json.dumps(egg.get("rappid_data", {}), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    if egg.get("leviathan_json"):
        (lev_dir / "leviathan.json").write_text(
            json.dumps(egg["leviathan_json"], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # 3. For each estate, recreate ~/.rapp/estates/<slug>_<est>/
    estate_slugs = list(egg["estates"].keys())
    stats = {"estates": 0, "industries": 0, "neighborhoods": 0,
             "factories": 0, "souls": 0}
    for est_slug, est_payload in egg["estates"].items():
        est_dir = ESTATES_ROOT / f"{slug}_{est_slug}"
        est_dir.mkdir(parents=True, exist_ok=True)

        (est_dir / "rappid.json").write_text(
            json.dumps(est_payload.get("rappid_data", {}), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (est_dir / "estate.json").write_text(
            json.dumps(est_payload["estate_json"], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # Souls
        for rel_path, content in est_payload.get("souls", {}).items():
            soul_path = est_dir / rel_path
            soul_path.parent.mkdir(parents=True, exist_ok=True)
            soul_path.write_text(content, encoding="utf-8")
            stats["souls"] += 1

        # Materialize the directory tree implied by estate.json
        est_json = est_payload["estate_json"]
        for industry in est_json.get("industries", []):
            ind_dir = est_dir / "industries" / industry["id"]
            ind_dir.mkdir(parents=True, exist_ok=True)
            stats["industries"] += 1
            for nbh in industry.get("neighborhoods", []):
                nbh_dir = ind_dir / nbh["id"]
                nbh_dir.mkdir(parents=True, exist_ok=True)
                stats["neighborhoods"] += 1
                for fac in nbh.get("factories", []):
                    fac_dir = nbh_dir / fac["id"]
                    fac_dir.mkdir(parents=True, exist_ok=True)
                    (fac_dir / "souls").mkdir(exist_ok=True)
                    stats["factories"] += 1

        stats["estates"] += 1

    # 4. Retrofit — write per-layer agent.py + symlinks
    _retrofit_after_hatch(slug, estate_slugs, rappid, egg)

    # 5. Drop the brainstem shim
    shim_info = None
    if wire:
        agents_dir = _find_brainstem_agents_dir()
        if agents_dir:
            cap = "".join(p.capitalize() for p in slug.split("_"))
            shim_path = agents_dir / f"{slug}_leviathan_agent.py"
            shim_path.write_text(SHIM_TEMPLATE.format(slug=slug, Cap=cap),
                                 encoding="utf-8")
            shim_info = {"shim_path": str(shim_path), "tool_name": f"Ask{cap}"}
        else:
            shim_info = {"warning": "no brainstem agents/ dir found; skipped wire"}

    return _ok("hatch", slug=slug, rappid=rappid, stats=stats,
               from_egg=str(egg_path), wired=shim_info)


def _retrofit_after_hatch(slug, estate_slugs, rappid, egg):
    """Mirror @kody-w/wrap_leviathan's retrofit using egg-derived data."""
    lev_dir = LEVIATHANS_ROOT / slug
    tagline = egg.get("rappid_data", {}).get("intent") or ""

    # Symlink estates into leviathan dir + write leviathan cell
    for est_slug in estate_slugs:
        est_dir = ESTATES_ROOT / f"{slug}_{est_slug}"
        link = lev_dir / est_slug
        if not link.exists() and not link.is_symlink():
            link.symlink_to(est_dir)
    lev_man = _lev_manifest(slug, rappid, estate_slugs, tagline)
    _write_cell(lev_dir, lev_man, slug)

    for est_slug in estate_slugs:
        est_dir = ESTATES_ROOT / f"{slug}_{est_slug}"
        est_payload = egg["estates"][est_slug]
        est_json = est_payload["estate_json"]
        est_rappid = est_payload.get("rappid") or rappid

        est_man = _est_manifest(slug, est_slug, est_json, est_rappid)
        _write_cell(est_dir, est_man, slug)

        for industry in est_json.get("industries", []):
            ind_dir = est_dir / "industries" / industry["id"]
            if not ind_dir.exists():
                continue
            up = est_dir / industry["id"]
            if not up.exists() and not up.is_symlink():
                up.symlink_to(ind_dir)
            ind_man = _ind_manifest(f"{slug}/{est_slug}", industry, est_rappid)
            _write_cell(ind_dir, ind_man, slug)

            for nbh in industry.get("neighborhoods", []):
                nbh_dir = ind_dir / nbh["id"]
                if not nbh_dir.exists():
                    continue
                nbh_man = _nbh_manifest(
                    f"{slug}/{est_slug}/{industry['id']}", nbh, est_rappid)
                _write_cell(nbh_dir, nbh_man, slug)

                for fac in nbh.get("factories", []):
                    fac_dir = nbh_dir / fac["id"]
                    if not fac_dir.exists():
                        continue
                    fac_man = _fac_manifest(
                        f"{slug}/{est_slug}/{industry['id']}/{nbh['id']}",
                        fac, est_rappid)
                    _write_cell(fac_dir, fac_man, slug)


# ─── Freeze: live leviathan → egg ──────────────────────────────────────────


def _load_json(path, default=None):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def _freeze(slug, out_dir=None):
    lev_dir = LEVIATHANS_ROOT / slug
    if not lev_dir.exists():
        return _err("freeze", f"no leviathan at {lev_dir}")

    rappid_data = _load_json(lev_dir / "rappid.json", {})
    leviathan_composite = _load_json(lev_dir / "leviathan.json", None)

    estates = {}
    stats = {"estates": 0, "industries": 0, "neighborhoods": 0,
             "factories": 0, "souls": 0}
    if ESTATES_ROOT.exists():
        prefix = f"{slug}_"
        for d in sorted(ESTATES_ROOT.iterdir()):
            if not (d.is_dir() and d.name.startswith(prefix)):
                continue
            est_slug = d.name[len(prefix):]
            est_json = _load_json(d / "estate.json", {})
            est_rappid = _load_json(d / "rappid.json", {})
            souls = {}
            for soul_md in d.rglob("souls/*.md"):
                rel = soul_md.relative_to(d).as_posix()
                souls[rel] = soul_md.read_text(encoding="utf-8")
            for ind in est_json.get("industries", []):
                stats["industries"] += 1
                for n in ind.get("neighborhoods", []):
                    stats["neighborhoods"] += 1
                    for f in n.get("factories", []):
                        stats["factories"] += 1
            stats["estates"] += 1
            stats["souls"] += len(souls)
            estates[est_slug] = {
                "rappid": est_rappid.get("rappid"),
                "rappid_data": est_rappid,
                "estate_json": est_json,
                "souls": souls,
            }

    egg = {
        "schema": "rapp-leviathan-egg/1.0",
        "_meta": {
            "frozen_at": datetime.now(timezone.utc).isoformat(),
            "frozen_by": "@kody-w/leviathan_hub v0.1.0",
            "host": socket.gethostname(),
        },
        "slug": slug,
        "rappid": rappid_data.get("rappid"),
        "rappid_data": rappid_data,
        "leviathan_json": leviathan_composite,
        "estates": estates,
        "stats": stats,
    }
    out_dir_p = pathlib.Path(out_dir).expanduser() if out_dir else EGGS_CACHE
    out_dir_p.mkdir(parents=True, exist_ok=True)
    out_path = out_dir_p / f"{slug}.leviathan.egg"
    out_path.write_text(json.dumps(egg, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    return _ok("freeze", slug=slug, path=str(out_path),
               size_kb=round(out_path.stat().st_size / 1024, 1),
               stats=stats)


# ════════════════════════════════════════════════════════════════════════════
# Agent
# ════════════════════════════════════════════════════════════════════════════


class LeviathanHub(BasicAgent):
    """Distribute Wrapped-Organism Leviathans as portable .leviathan.egg files."""

    def __init__(self):
        self.name = "LeviathanHub"
        self.metadata = {
            "name": self.name,
            "description": __manifest__["description"],
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["hub_status", "list_eggs", "download",
                                 "hatch", "freeze"],
                        "description": "Which hub action to perform.",
                    },
                    "egg": {
                        "type": "string",
                        "description": (
                            "Egg name (e.g. 'kody'), or a local path to a "
                            ".leviathan.egg file. For hatch/download."
                        ),
                    },
                    "slug": {
                        "type": "string",
                        "description": "Live leviathan slug to freeze.",
                    },
                    "remote": {
                        "type": "boolean",
                        "description": "For list_eggs: also fetch the hub's remote index.",
                    },
                    "wire": {
                        "type": "boolean",
                        "description": (
                            "For hatch: drop the brainstem shim so the "
                            "leviathan becomes immediately callable. "
                            "Default true."
                        ),
                    },
                    "out_dir": {
                        "type": "string",
                        "description": "For freeze: directory to write the egg into.",
                    },
                },
                "required": ["action"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs):
        action = kwargs.get("action") or "hub_status"
        try:
            if action == "hub_status":
                return _hub_status()
            if action == "list_eggs":
                return _list_eggs(remote=bool(kwargs.get("remote")))
            if action == "download":
                if not kwargs.get("egg"):
                    return _err(action, "egg is required")
                return _download(kwargs["egg"])
            if action == "hatch":
                if not kwargs.get("egg"):
                    return _err(action, "egg is required")
                wire = kwargs.get("wire", True)
                return _hatch(kwargs["egg"], wire=wire)
            if action == "freeze":
                if not kwargs.get("slug"):
                    return _err(action, "slug is required")
                return _freeze(kwargs["slug"], out_dir=kwargs.get("out_dir"))
            return _err(action, f"unknown action: {action!r}")
        except Exception as e:
            return _err(action, f"{type(e).__name__}: {e}")


# Standalone CLI
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("action", default="hub_status", nargs="?")
    p.add_argument("--egg")
    p.add_argument("--slug")
    p.add_argument("--remote", action="store_true")
    p.add_argument("--no-wire", action="store_true")
    p.add_argument("--out-dir")
    args = p.parse_args()
    out = LeviathanHub().perform(
        action=args.action, egg=args.egg, slug=args.slug,
        remote=args.remote, wire=not args.no_wire,
        out_dir=args.out_dir,
    )
    print(out)
