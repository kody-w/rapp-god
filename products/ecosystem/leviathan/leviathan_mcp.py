#!/usr/bin/env python3
"""
leviathan_mcp.py — hook ANY MCP-speaking agent runtime into the Leviathan.

Claude Code, Claude Desktop, the GitHub Copilot CLI, Cursor, Cline, Continue —
they all speak the Model Context Protocol. This is a stdio MCP server (stdlib only,
zero dependencies) that exposes the Leviathan controller as MCP tools, so any of
them becomes "the mind" and drives your fleet of no-LLM bodies natively.

Point it at your fleet with the HIVEMIND_NODES env (JSON) or ~/.hivemind/nodes.json,
then register it (see HOOKUP.md). It speaks newline-delimited JSON-RPC 2.0 over
stdin/stdout — nothing is printed to stdout except protocol messages.

Tools exposed: leviathan_up, leviathan_sh, leviathan_one, leviathan_all,
leviathan_scatter, leviathan_who, leviathan_deploy, leviathan_forge.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import leviathan  # noqa: E402

SERVER = {"name": "leviathan", "version": "1.0.0"}

TOOLS = [
    {"name": "leviathan_up",
     "description": "Liveness + degrade board for the whole fleet. Shows each body: reachable? its own LLM up/down? version, agent count. Start here.",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "leviathan_sh",
     "description": "Run a shell command on one body, or on every body in parallel (node='all'). Returns exit code + stdout per body. No LLM is used.",
     "inputSchema": {"type": "object", "properties": {
         "node": {"type": "string", "description": "a body name from the roster, or 'all' for the whole fleet"},
         "command": {"type": "string"}}, "required": ["node", "command"]}},
    {"name": "leviathan_one",
     "description": "Invoke one named agent on one body, directly (no LLM). args is a JSON object of the agent's kwargs.",
     "inputSchema": {"type": "object", "properties": {
         "node": {"type": "string"}, "agent": {"type": "string"},
         "args": {"type": "object", "description": "kwargs passed to the agent's perform()"}},
         "required": ["node", "agent"]}},
    {"name": "leviathan_all",
     "description": "Invoke one named agent on EVERY body in parallel. Bodies lacking it come back status='missing'. args = the agent's kwargs.",
     "inputSchema": {"type": "object", "properties": {
         "agent": {"type": "string"}, "args": {"type": "object"}}, "required": ["agent"]}},
    {"name": "leviathan_scatter",
     "description": "Run DIFFERENT agents on DIFFERENT bodies in one parallel wave. calls = [{node, agent, args}, ...].",
     "inputSchema": {"type": "object", "properties": {
         "calls": {"type": "array", "items": {"type": "object", "properties": {
             "node": {"type": "string"}, "agent": {"type": "string"}, "args": {"type": "object"}},
             "required": ["node", "agent"]}}}, "required": ["calls"]}},
    {"name": "leviathan_who",
     "description": "List which bodies currently hold a given agent (for routing).",
     "inputSchema": {"type": "object", "properties": {"agent": {"type": "string"}}, "required": ["agent"]}},
    {"name": "leviathan_deploy",
     "description": "Install an agent (Python source for a BasicAgent subclass) on every body, hot-loaded, no restart.",
     "inputSchema": {"type": "object", "properties": {
         "code": {"type": "string", "description": "full agent source"},
         "name": {"type": "string", "description": "agent name (file becomes <name>_agent.py)"}},
         "required": ["code", "name"]}},
    {"name": "leviathan_forge",
     "description": "Manufacture vetted capability FLEET-WIDE: install each spec, run its deterministic test, keep where it passes / prune where it fails. specs = [{name, code, test_args, expect, description}].",
     "inputSchema": {"type": "object", "properties": {
         "specs": {"type": "array", "items": {"type": "object"}}}, "required": ["specs"]}},
    {"name": "rapp_route",
     "description": "Ride the whole RAPP medium: given your SITUATION, crawl the spine and get which protocol(s) govern it + how to act. Works for any agent, RAPP or not.",
     "inputSchema": {"type": "object", "properties": {
         "situation": {"type": "string", "description": "what you're trying to do"}}, "required": ["situation"]}},
    {"name": "rapp_north_star",
     "description": "Pull the RAPP ecosystem's north star + the medium definition from the hydra-served roadmap.",
     "inputSchema": {"type": "object", "properties": {}}},
]

import urllib.request as _u  # noqa: E402


def _hydra_json(repo, path):
    for base in (f"https://raw.githubusercontent.com/kody-w/{repo}/main",
                 f"https://cdn.jsdelivr.net/gh/kody-w/{repo}@main",
                 f"https://raw.githack.com/kody-w/{repo}/main"):
        try:
            return json.loads(_u.urlopen(f"{base}/{path}", timeout=10).read())
        except Exception:
            continue
    return None


def _call(name, a):
    if name == "leviathan_up":
        return leviathan.up().summary()
    if name == "leviathan_sh":
        node, cmd = a["node"], a["command"]
        if node == "all":
            return leviathan.sh_all(cmd).summary()
        r = leviathan.sh(node, cmd)
        return f"{r!r}\nexit={r.rc}\n{r.out}{('[stderr] ' + r.err) if r.err else ''}"
    if name == "leviathan_one":
        r = leviathan.one(a["node"], a["agent"], **(a.get("args") or {}))
        return f"{r!r}\nvalue: {json.dumps(r.value, default=str)[:2000]}" + (f"\nerror: {r.error}" if r.error else "")
    if name == "leviathan_all":
        return leviathan.all(a["agent"], **(a.get("args") or {})).summary()
    if name == "leviathan_scatter":
        calls = [(c["node"], c["agent"], c.get("args", {})) for c in a["calls"]]
        return leviathan.scatter(calls).summary()
    if name == "leviathan_who":
        return json.dumps(leviathan.who(a["agent"]))
    if name == "leviathan_deploy":
        return leviathan.deploy(a["code"], name=a["name"]).summary()
    if name == "leviathan_forge":
        out = leviathan.forge_batch(a["specs"])
        return "\n".join(f"{v['verdict']:<10} {v['agent']}  kept_on={v.get('kept_on', [])}" for v in out)
    if name == "rapp_route":
        reg = _hydra_json("rapp-spine", "registry.json") or {}
        sit = (a.get("situation") or "").lower()
        words = {w for w in sit.replace(",", " ").split() if len(w) > 3}
        scored = sorted(((sum(1 for w in words if w in (r.get("situation","")+" "+r.get("why","")+" "+" ".join(r.get("use",[]))).lower()), r)
                         for r in reg.get("router", [])), key=lambda x: -x[0])
        hits = [r for s, r in scored[:3] if s > 0]
        if not hits:
            return "No direct route. Crawl the full spine: https://raw.githubusercontent.com/kody-w/rapp-spine/main/registry.json"
        return "\n\n".join(f"→ USE: {', '.join(r['use'])}\n  situation: {r['situation']}\n  why: {r['why']}" for r in hits)
    if name == "rapp_north_star":
        rm = _hydra_json("rapp-roadmap", "roadmap.json") or {}
        return json.dumps({"north_star": rm.get("north_star"), "the_medium": rm.get("the_medium")}, indent=2)
    raise ValueError(f"unknown tool {name}")


def _handle(method, params):
    if method == "initialize":
        return {"protocolVersion": params.get("protocolVersion", "2024-11-05"),
                "capabilities": {"tools": {"listChanged": False}}, "serverInfo": SERVER}
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        try:
            text = _call(params["name"], params.get("arguments") or {})
            return {"content": [{"type": "text", "text": text}], "isError": False}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"error: {e}"}], "isError": True}
    if method == "ping":
        return {}
    raise ValueError(f"unknown method: {method}")


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except Exception:
            continue
        mid = msg.get("id")
        method = msg.get("method")
        if mid is None:  # a notification (e.g. notifications/initialized) — no reply
            continue
        try:
            result = _handle(method, msg.get("params") or {})
            resp = {"jsonrpc": "2.0", "id": mid, "result": result}
        except Exception as e:
            resp = {"jsonrpc": "2.0", "id": mid, "error": {"code": -32603, "message": str(e)}}
        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
