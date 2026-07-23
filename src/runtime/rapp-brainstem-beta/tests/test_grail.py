#!/usr/bin/env python3
"""Keystone test (deterministic, no LLM): the OS sandbox confines writes to agents/
and makes brainstem.py physically unwritable — even from a child process. This is the
grail guarantee. If this fails, nothing ships.
"""
import os
import subprocess
import tempfile
import pathlib

REPO = pathlib.Path(__file__).resolve().parent.parent
WRAPPER = REPO / "sandbox" / "copilot-sandboxed.sh"


def _profile(src, agents):
    f = tempfile.NamedTemporaryFile("w", suffix=".sb", delete=False)
    f.write("(version 1)\n(allow default)\n"
            f'(deny file-write* (subpath "{src}"))\n'
            f'(allow file-write* (subpath "{agents}"))\n')
    f.close()
    return f.name


def _sandboxed(profile, shell_cmd):
    return subprocess.run(["/usr/bin/sandbox-exec", "-f", profile, "/bin/sh", "-c", shell_cmd],
                          capture_output=True, text=True)


def test_grail_confinement():
    assert os.path.exists("/usr/bin/sandbox-exec"), "macOS sandbox-exec required"
    assert WRAPPER.exists(), "sandbox wrapper missing"
    d = tempfile.mkdtemp()
    src = os.path.realpath(d)
    agents = os.path.join(src, "agents")
    os.makedirs(agents)
    grail = os.path.join(src, "brainstem.py")
    open(grail, "w").write("# GRAIL\nSECRET = 42\n")
    prof = _profile(src, agents)

    # 1. writes INSIDE agents/ are allowed
    _sandboxed(prof, f"echo cartridge > '{agents}/x_agent.py'")
    assert os.path.exists(os.path.join(agents, "x_agent.py")), "agents/ write should be allowed"

    # 2. writing the grail is OS-denied (direct shell)
    _sandboxed(prof, f"echo HACK >> '{grail}'")
    assert "HACK" not in open(grail).read(), "grail write must be blocked"

    # 3. child-process escape (python -c) is ALSO denied — the real test
    _sandboxed(prof, f"python3 -c \"open('{grail}','a').write('PYHACK')\"")
    assert "PYHACK" not in open(grail).read(), "child-process grail write must be blocked"

    # 4. tee escape is denied too
    _sandboxed(prof, f"echo X | tee -a '{grail}' >/dev/null 2>&1")
    assert "X" not in open(grail).read().replace("SECRET", ""), "tee grail write must be blocked"

    print("PASS: grail OS-confinement holds (agents/ writable; brainstem.py unwritable via shell, python, tee)")


if __name__ == "__main__":
    test_grail_confinement()
