#!/usr/bin/env python3
"""
golden.py — behavioral regression tests for a running brainstem.

Each golden/*.json case is {"name", "prompt", "must_contain": [...],
"must_call_agent": "AgentName" (optional)}. A case passes when the /chat
response contains every must_contain string (case-insensitive) and, if
specified, the agent log shows the named agent was called.

Run after model changes, soul edits, or agent updates:
    python3 golden.py            # all cases
    python3 golden.py memory     # only cases whose filename matches
Exit code: 0 all pass, 1 otherwise.
"""

import json
import sys
import urllib.request
from pathlib import Path

BASE = "http://localhost:7071"


def chat(prompt):
    req = urllib.request.Request(
        BASE + "/chat",
        data=json.dumps({"user_input": prompt, "session_id": "golden"}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def main():
    pattern = sys.argv[1] if len(sys.argv) > 1 else ""
    cases = sorted((Path(__file__).parent / "golden").glob("*.json"))
    cases = [c for c in cases if pattern in c.stem]
    if not cases:
        print("no golden cases matched")
        return 1

    failed = 0
    for path in cases:
        case = json.loads(path.read_text())
        try:
            d = chat(case["prompt"])
        except Exception as e:
            print(f"✗ {case['name']}: request failed — {e}")
            failed += 1
            continue
        resp = (d.get("response") or "").lower()
        logs = d.get("agent_logs") or ""
        misses = [s for s in case.get("must_contain", []) if s.lower() not in resp]
        agent = case.get("must_call_agent")
        agent_ok = (agent is None) or (agent in logs)
        if not misses and agent_ok:
            print(f"✓ {case['name']}")
        else:
            failed += 1
            print(f"✗ {case['name']}: " +
                  ("; ".join(f"missing {m!r}" for m in misses) or "") +
                  ("" if agent_ok else f" agent {agent} not called"))
    print(f"\n{len(cases) - failed}/{len(cases)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
