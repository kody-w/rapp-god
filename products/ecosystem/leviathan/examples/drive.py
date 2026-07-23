#!/usr/bin/env python3
"""
drive.py — a minimal tour of driving the Leviathan (one mind, many bodies).

Point it at your own fleet first:
    export HIVEMIND_NODES='{"alpha":"10.0.0.11","beta":"10.0.0.12"}'
Then:
    python examples/drive.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import leviathan  # noqa: E402

# 1. liveness + degrade board — one Result per body (down/llm-degraded/healthy)
print("── up ──")
print(leviathan.up().summary())

# 2. a shell command across the whole fleet, in parallel
print("\n── sh_all 'hostname' ──")
print(leviathan.sh_all("hostname").summary())

# 3. one capability on every body that has it (others come back status='missing')
print("\n── all Base64(encode 'hi') ──")
print(leviathan.all("Base64", action="encode", text="hi").summary())

# 4. route: where does a capability live?
print("\n── who('Base64') ──")
print(leviathan.who("Base64"))

# 5. scatter: different capabilities to different bodies in ONE wave
print("\n── scatter ──")
print(leviathan.scatter([
    ("alpha", "RemoteControl", {"command": "uname -a"}),
    ("beta", "RemoteControl", {"command": "date"}),
]).summary())
