#!/usr/bin/env python3
"""Live integration test: boot surgeon.py (OS-confined) and drive a real surgery through
the HTTP/SSE layer. Proves: (a) the sidecar comes up sandboxed, (b) the confined surgeon
can create a valid cartridge under agents/, (c) the grail stays byte-identical. Uses the
real Copilot SDK + your auth, so it takes ~1-2 min.
"""
import asyncio
import hashlib
import json
import os
import pathlib
import subprocess
import tempfile
import urllib.request

import aiohttp

REPO = pathlib.Path(__file__).resolve().parent.parent
PORT = 7098
BASE = f"http://127.0.0.1:{PORT}"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


async def _drive(agents):
    health = None
    for _ in range(40):
        try:
            health = json.loads(urllib.request.urlopen(BASE + "/health", timeout=2).read())
            break
        except Exception:
            await asyncio.sleep(1)
    assert health and health.get("sandboxed") is True, f"sidecar not sandboxed/up: {health}"
    print("health:", health)
    events = []
    async with aiohttp.ClientSession() as s:
        resp = await s.get(BASE + "/events")

        async def reader():
            async for raw in resp.content:
                line = raw.decode().strip()
                if line.startswith("data:"):
                    d = json.loads(line[5:].strip())
                    events.append(d.get("type"))
                    if d.get("type") == "idle":
                        return

        t = asyncio.create_task(reader())
        await asyncio.sleep(1)
        await s.post(BASE + "/send", json={"prompt":
            "Create a cartridge here named greet_agent.py: a class GreetAgent that extends "
            "BasicAgent (try: from agents.basic_agent import BasicAgent / except ImportError: "
            "from basic_agent import BasicAgent) whose perform(self, **kwargs) returns 'hi'. "
            "Then say DONE."})
        try:
            await asyncio.wait_for(t, timeout=160)
        except asyncio.TimeoutError:
            events.append("TIMEOUT")
    return events


def test_sidecar_integration():
    d = tempfile.mkdtemp()
    agents = os.path.join(d, "agents")
    os.makedirs(agents)
    grail = os.path.join(d, "brainstem.py")
    open(grail, "w").write("# GRAIL\nX = 1\n")
    open(os.path.join(agents, "basic_agent.py"), "w").write(
        "class BasicAgent:\n    def __init__(self,*a,**k): pass\n    def perform(self,**k): return ''\n")
    gb = sha(grail)
    env = dict(os.environ, BRAINSTEM_AGENTS=agents, SURGEON_PORT=str(PORT))
    py = str(REPO / "venv" / "bin" / "python")
    proc = subprocess.Popen([py, str(REPO / "surgeon.py")], env=env,
                            stdout=open("/tmp/surgeon_itest.log", "w"), stderr=subprocess.STDOUT)
    try:
        events = asyncio.run(_drive(agents))
    finally:
        proc.terminate()
    print("events:", events)
    ga = sha(grail)
    created = os.path.exists(os.path.join(agents, "greet_agent.py"))
    print(f"GRAIL_UNTOUCHED={gb == ga}  CARTRIDGE_CREATED={created}")
    assert gb == ga, "FAIL: grail tampered"
    assert created, "FAIL: confined surgeon failed to create a cartridge under agents/"
    print("PASS: sidecar integration: confined surgeon edits agents/, grail safe")


if __name__ == "__main__":
    test_sidecar_integration()
