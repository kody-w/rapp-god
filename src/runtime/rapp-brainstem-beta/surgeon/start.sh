#!/usr/bin/env bash
# Launch the Brain Surgeon sidecar. Creates a venv, installs the Copilot SDK (which
# bundles the CLI) + aiohttp, then runs surgeon.py. Python 3.11+ only.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

PY="${PYTHON:-}"
if [ -z "$PY" ]; then
  for c in python3.11 python3.12 python3.13 python3; do
    command -v "$c" >/dev/null 2>&1 && { PY="$c"; break; }
  done
fi
[ -n "$PY" ] || { echo "Python 3.11+ required (python.org)"; exit 1; }

./venv/bin/python -c "" 2>/dev/null || { rm -rf venv; "$PY" -m venv venv; }
./venv/bin/pip install -q --no-cache-dir --upgrade pip >/dev/null
./venv/bin/pip install -q --no-cache-dir -r requirements.txt

echo "Brain Surgeon sidecar - http://localhost:${SURGEON_PORT:-7072}"
echo "   operating on: ${BRAINSTEM_AGENTS:-$HOME/.brainstem/src/rapp_brainstem/agents}"
echo "   grail (brainstem.py) is OS-confined and off-limits."
exec ./venv/bin/python surgeon.py
