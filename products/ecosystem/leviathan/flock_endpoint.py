"""
FlockEndpoint — give this brainstem a DIRECT, no-LLM agent-invocation endpoint.

The /chat endpoint runs the node's LLM to decide which agent to call — expensive,
and on a shared Copilot token it throttles the whole flock. For control/flock
operations (run a shell command, dispatch a CLI task, check health) we don't need
the node to think at all: the controller (Claude) already knows the exact agent
and args. This agent injects, at import time, a route:

    POST /api/agent/<AgentName>   body = JSON kwargs   ->   {ok, agent, result}

which calls that agent's perform(**body) directly — NO LLM, NO Copilot token, no
throttling. The flock controller drives every node through this; the node's LLM
is never touched.

It injects via the Werkzeug url_map directly (Flask's add_url_rule is locked
after the first request), guarded + idempotent. Drop in via /agents/import — it
works even when /chat is down (deploying an agent doesn't use the LLM).
"""
import json
import os
import sys

from agents.basic_agent import BasicAgent

_ENDPOINT = "flock_direct_agent"


def _record_flight(agent_name, args, result, error, ip):
    """Record every direct /api/agent call into the Flight Recorder store, so the
    hivemind/direct path is captured too (the /chat-wrapping recorder misses it).
    Respects the recorder's enable flag; never raises (recording must not break a call)."""
    try:
        import datetime
        fr = os.path.expanduser("~/.brainstem/flight_recorder")
        ctrl = os.path.join(fr, "control.json")
        if os.path.exists(ctrl):
            try:
                if not json.load(open(ctrl)).get("enabled", True):
                    return
            except Exception:
                pass
        os.makedirs(fr, exist_ok=True)
        now = datetime.datetime.now()
        out = result if isinstance(result, str) else (json.dumps(result) if result is not None else "")
        rec = {
            "ts": now.strftime("%Y-%m-%dT%H:%M:%S"),
            "caller": "hivemind", "channel": "api/agent", "ip": ip,
            "agent": agent_name,
            "args": {k: str(v)[:300] for k, v in (args or {}).items()},
            "user_input": f"→ {agent_name}(" + ", ".join((args or {}).keys()) + ")",
            "response": (f"ERROR: {error}" if error else out)[:4000],
        }
        with open(os.path.join(fr, now.strftime("%Y-%m-%d") + ".jsonl"), "a") as f:
            f.write(json.dumps(rec) + "\n")
    except Exception:
        pass


def _brainstem():
    for nm in ("brainstem", "__main__"):
        m = sys.modules.get(nm)
        if m is not None and hasattr(m, "app") and hasattr(m, "load_agents"):
            return m
    return None


def _install_route():
    bs = _brainstem()
    if bs is None:
        return "no brainstem app found"
    app = bs.app
    try:
        from flask import request, jsonify
        from werkzeug.routing import Rule
    except Exception as e:
        return f"flask import failed: {e}"

    def _direct(name):
        body = {}
        try:
            ip = request.remote_addr
        except Exception:
            ip = None
        try:
            agents = bs.load_agents()
            inst = agents.get(name)
            body = request.get_json(silent=True) or {}
            if not isinstance(body, dict):
                body = {}
            if inst is None:
                _record_flight(name, body, None, f"no agent '{name}'", ip)
                return jsonify({"ok": False, "error": f"no agent '{name}'", "available": sorted(agents)}), 404
            result = inst.perform(**body)
            _record_flight(name, body, result, None, ip)
            return jsonify({"ok": True, "agent": name, "result": result})
        except Exception as e:
            _record_flight(name, body, None, str(e), ip)
            return jsonify({"ok": False, "agent": name, "error": str(e)}), 500

    # Always (re)bind the view so re-imports pick up new code (e.g. flight recording).
    app.view_functions[_ENDPOINT] = _direct
    # Add the route only once (bypass Flask's post-first-request setup lock via url_map).
    have_rule = any(r.endpoint == _ENDPOINT for r in app.url_map.iter_rules())
    if not have_rule:
        app.url_map.add(Rule("/api/agent/<name>", endpoint=_ENDPOINT, methods=["POST", "OPTIONS"]))
        app.url_map.update()
        return "installed"
    return "updated (view rebound)"


_INSTALL_RESULT = ""
try:
    _INSTALL_RESULT = _install_route()
except Exception as e:  # never break agent loading
    _INSTALL_RESULT = f"error: {e}"


class FlockEndpointAgent(BasicAgent):
    def __init__(self):
        self.name = "FlockEndpoint"
        self.metadata = {
            "name": self.name,
            "description": (
                "Installs (on load) a direct, no-LLM agent-invocation endpoint on this brainstem: "
                "POST /api/agent/<AgentName> with JSON kwargs runs that agent's perform() directly and "
                "returns the result — no LLM, no Copilot token. Lets a controller drive the node without "
                "throttling. Call this agent (action=status) to confirm the endpoint is live."
            ),
            "parameters": {"type": "object", "properties": {
                "action": {"type": "string", "enum": ["status"], "description": "status — confirm the endpoint is installed"}
            }},
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs):
        return json.dumps({
            "ok": True,
            "direct_endpoint": "POST /api/agent/<AgentName> (JSON kwargs -> perform() result, no LLM)",
            "install_result": _INSTALL_RESULT or _install_route(),
        })
