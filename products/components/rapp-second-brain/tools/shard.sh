#!/bin/bash
# shard.sh <N> <i> — print the slice of uncarded public nodes assigned to
# writer i of N (deterministic sha1 split), so parallel Opuses divide the
# work up front instead of racing claims. Claims still run as a backstop.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"; cd "$HERE"
N="${1:?usage: shard.sh <N> <i>}"; I="${2:?usage: shard.sh <N> <i>}"
python3 - "$N" "$I" <<'PY'
import json, sys, hashlib, glob, os
N, I = int(sys.argv[1]), int(sys.argv[2])
# a node needs work if its card is still seed-depth (or missing)
import glob as _g
def needs_deepening(safe):
    f = f"brain/cards/{safe}.json"
    if not os.path.exists(f): return True
    try: return json.load(open(f)).get("provenance",{}).get("depth") == "seed"
    except Exception: return True
inv = json.load(open("brain/inventory.json"))
for r in inv:
    cid = f"repo:kody-w/{r['name']}"
    safe = cid.replace('/','_').replace(':','_').replace('@','_')
    if not needs_deepening(safe): continue
    if int(hashlib.sha1(r['name'].encode()).hexdigest(), 16) % N == I:
        print(cid)
PY
