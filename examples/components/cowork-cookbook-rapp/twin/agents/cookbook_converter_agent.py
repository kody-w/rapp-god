"""Cowork Cookbook Converter — turn a Cowork Cookbook recipe into a single-file agent.py with WorkIQ access.

A recipe (`recipe.yaml` + `prompt.md`) from https://github.com/seangalliher/Coworkcookbook describes a
Microsoft Copilot Cowork task: a prompt plus the plugin actions it uses (e.g. Dynamics 365 ERP
`data_find_entities_sql`). This agent converts any recipe into a single-file `agent.py` whose
`perform()` runs that prompt against the LLM with **WorkIQ** context — the work-intelligence layer
Cowork runs on — so the generated agent behaves "just like Cowork" once WorkIQ is wired into the host.

  perform(recipe="<slug>"[, process_area="<area>"])   → the generated agent.py source (paste/hotload it)
  perform(list=true[, process_area="<area>"])          → browse the catalog
  perform(describe="<slug>")                           → a recipe's metadata + prompt

Recipes are read from the bundled snapshot first, then fetched live from the cookbook (raw GitHub).
Stdlib only. Not affiliated with Microsoft.
"""

__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@cowork/cookbook_converter_agent",
    "version": "1.0.0",
    "display_name": "CookbookConverter",
    "description": "Convert a Cowork Cookbook recipe into a single-file agent.py with WorkIQ access (runs the recipe's prompt like Cowork).",
    "author": "Cowork Cookbook (recipes © their authors, CC-BY-4.0)",
    "tags": ["cowork", "cookbook", "workiq", "copilot", "recipe", "codegen", "dynamics-365", "converter"],
    "category": "integrations",
    "quality_tier": "community",
    "requires_env": [],
    "dependencies": ["@rapp/basic_agent"],
}

import os
import re
import json
import urllib.request

try:
    from agents.basic_agent import BasicAgent  # type: ignore
except Exception:
    class BasicAgent:
        def __init__(self, name, metadata):
            self.name = name
            self.metadata = metadata

COOKBOOK = "seangalliher/Coworkcookbook"
RAW = "https://raw.githubusercontent.com/" + COOKBOOK + "/main"
BUNDLED = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "recipes")


def _get(url):
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return r.read().decode("utf-8", "replace")
    except Exception:
        return None


def _index():
    """The recipe catalog: {area: [slug,...]}. Bundled index.json first, else None (browse live)."""
    p = os.path.join(BUNDLED, "index.json")
    if os.path.exists(p):
        try:
            return json.load(open(p))
        except Exception:
            pass
    live = _get(RAW + "/recipes/index.json")
    if live:
        try:
            return json.loads(live)
        except Exception:
            pass
    return {}


def _find_area(idx, slug):
    for area, slugs in (idx or {}).items():
        if slug in slugs:
            return area
    return None


def _read_recipe(slug, area=None):
    """Return (yaml_text, prompt_text) from the bundled snapshot or live. area optional."""
    idx = _index()
    area = area or _find_area(idx, slug)
    cands = [area] if area else list((idx or {}).keys()) or [
        "acquire-to-dispose", "order-to-cash", "source-to-pay", "record-to-report"]
    for a in cands:
        base_local = os.path.join(BUNDLED, a or "", slug)
        y = os.path.join(base_local, "recipe.yaml"); pr = os.path.join(base_local, "prompt.md")
        if os.path.exists(y) and os.path.exists(pr):
            return open(y).read(), open(pr).read(), a
        yt = _get(RAW + "/recipes/%s/%s/recipe.yaml" % (a, slug))
        pt = _get(RAW + "/recipes/%s/%s/prompt.md" % (a, slug))
        if yt and pt:
            return yt, pt, a
    return None, None, area


def _yaml_lite(text):
    """Tolerant parse of the recipe.yaml fields we need (no PyYAML dependency)."""
    m = {}
    for key in ("id", "title", "summary", "business_value", "plugin", "recipe_type", "difficulty"):
        r = re.search(r"(?m)^%s:\s*(?:>-)?\s*(.*)$" % key, text)
        if r:
            m[key] = r.group(1).strip().strip('"').strip()
    # folded scalars (summary/business_value with >-) — grab the indented continuation
    for key in ("summary", "business_value"):
        if m.get(key) == "":
            r = re.search(r"(?m)^%s:\s*>-\s*\n((?:[ \t]+.*\n?)+)" % key, text)
            if r:
                m[key] = " ".join(l.strip() for l in r.group(1).splitlines() if l.strip())
    # plugin actions used (uses_skills.plugin → action: X)
    actions = re.findall(r"(?m)^\s*-?\s*action:\s*([A-Za-z0-9_]+)", text)
    m["actions"] = sorted(set(actions))
    tags = re.findall(r"(?m)^\s*-\s*([a-z0-9][a-z0-9/_-]+)\s*$", text)
    m["process_tags"] = [t for t in tags if "/" in t][:4]
    return m


def _classname(slug):
    parts = re.split(r"[^a-z0-9]+", slug.lower())
    return "".join(p.capitalize() for p in parts if p) + "Agent"


def _gen_agent(slug, meta, prompt):
    name = meta.get("title") or slug
    cls = _classname(slug)
    plugin = meta.get("plugin") or ""
    actions = meta.get("actions") or []
    manifest = {
        "schema": "rapp-agent/1.0",
        "name": "@cowork/%s_agent" % re.sub(r"[^a-z0-9_]+", "_", slug.lower()),
        "version": "1.0.0",
        "display_name": cls[:-5],
        "description": (meta.get("summary") or name)[:200],
        "author": "Cowork Cookbook recipe (CC-BY-4.0)",
        "tags": ["cowork", "workiq", "recipe", plugin or "cowork"] + meta.get("process_tags", [])[:2],
        "category": "integrations",
        "quality_tier": "community",
        "requires_env": [],
        "dependencies": ["@rapp/basic_agent"],
    }
    return '''"""%s — a Cowork Cookbook recipe as a single-file agent, WorkIQ-enabled.

Generated by @cowork/cookbook_converter_agent from recipe "%s".
perform(ask="...") runs the recipe's prompt against the LLM with WorkIQ context — the work-
intelligence Cowork uses (plugin: %s). Drop this file into a brainstem's agents/ dir; it works
like Cowork once `utils.workiq` is wired. Recipe content CC-BY-4.0, its authors. Not MS-affiliated.
"""

__manifest__ = %s

import json

try:
    from agents.basic_agent import BasicAgent  # type: ignore
except Exception:
    class BasicAgent:
        def __init__(self, name, metadata):
            self.name = name
            self.metadata = metadata

# WorkIQ access — the work-intelligence layer Microsoft Copilot Cowork runs on. Host-provided; the
# stub keeps the agent runnable offline (it just won't have live tenant data until WorkIQ is wired).
try:
    from utils.workiq import workiq  # type: ignore
except Exception:
    def workiq(query, plugin=None, action=None, **kw):
        return {"workiq": "unavailable — wire utils.workiq in your brainstem for live Cowork data",
                "query": query, "plugin": plugin, "action": action}

try:
    from utils.llm import call_llm  # type: ignore
except Exception:
    call_llm = None

RECIPE = %s
PROMPT = %s


class %s(BasicAgent):
    def __init__(self):
        self.name = %r
        self.metadata = {"name": self.name, "description": %r,
                         "parameters": {"type": "object", "properties": {
                             "ask": {"type": "string", "description": "Optional override / focus for the recipe."}}, "required": []}}
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs):
        ask = kwargs.get("ask") or kwargs.get("user_input") or PROMPT
        # Pull the work context this recipe needs from WorkIQ — the same plugin actions Cowork calls.
        ctx = {a: workiq(ask, plugin=RECIPE.get("plugin"), action=a) for a in RECIPE.get("actions", [])} or \\
              {"context": workiq(ask, plugin=RECIPE.get("plugin"))}
        full = PROMPT + "\\n\\n[WorkIQ context]\\n" + json.dumps(ctx, indent=2, default=str) + "\\n\\n[Ask]\\n" + str(ask)
        if call_llm:
            try:
                return call_llm(full)
            except Exception as e:
                return "LLM error: " + str(e) + "\\n\\n" + full
        return "Recipe assembled (no LLM wired — prompt + WorkIQ context below):\\n\\n" + full
''' % (
        name.replace('"', "'"), slug, plugin or "(none)",
        json.dumps(manifest, indent=4),
        json.dumps({"id": slug, "title": name, "plugin": plugin, "actions": actions,
                    "process_tags": meta.get("process_tags", [])}, indent=4),
        json.dumps(prompt),
        cls, cls[:-5], (meta.get("summary") or name)[:160],
    )


class CoworkCookbookConverterAgent(BasicAgent):
    def __init__(self):
        self.name = "CookbookConverter"
        self.metadata = {
            "name": self.name,
            "description": "Convert a Cowork Cookbook recipe into a single-file agent.py with WorkIQ access. "
                           "list=true to browse; recipe='<slug>' to convert; describe='<slug>' for details.",
            "parameters": {"type": "object", "properties": {
                "recipe": {"type": "string", "description": "Recipe slug to convert into an agent.py."},
                "process_area": {"type": "string", "description": "Optional business-process area to scope the search."},
                "list": {"type": "boolean", "description": "Browse the recipe catalog."},
                "describe": {"type": "string", "description": "Show a recipe's metadata + prompt."},
            }, "required": []},
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs):
        if kwargs.get("list"):
            idx = _index(); area = kwargs.get("process_area")
            if not idx:
                return "Couldn't read the catalog. Browse it at https://github.com/" + COOKBOOK + "/tree/main/recipes"
            if area and area in idx:
                return area + " recipes:\n" + "\n".join("  • " + s for s in idx[area])
            return "Cowork Cookbook — %d process areas:\n" % len(idx) + "\n".join(
                "  %s (%d recipes)" % (a, len(s)) for a, s in sorted(idx.items()))

        slug = kwargs.get("recipe") or kwargs.get("describe")
        if not slug:
            return ("CookbookConverter — turn Cowork Cookbook recipes into WorkIQ-enabled agents.\n"
                    "Try: list=true · recipe='adaptive-card-analyze-asset-utilization' · describe='<slug>'.")
        yt, pt, area = _read_recipe(slug, kwargs.get("process_area"))
        if not yt or not pt:
            return "Couldn't find recipe '%s'. Try list=true to see slugs." % slug
        meta = _yaml_lite(yt)
        if kwargs.get("describe"):
            return ("**%s**  (%s · plugin %s)\n%s\n\nWorkIQ actions: %s\n\n--- prompt ---\n%s"
                    % (meta.get("title", slug), area, meta.get("plugin", "?"),
                       meta.get("summary", ""), ", ".join(meta.get("actions", [])) or "(none)", pt.strip()))
        return _gen_agent(slug, meta, pt)


if __name__ == "__main__":
    a = CoworkCookbookConverterAgent()
    print(a.perform(recipe="adaptive-card-analyze-asset-utilization", process_area="acquire-to-dispose")[:1400])
