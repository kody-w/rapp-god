#!/bin/bash
# rebuild.sh — regenerate the DERIVED indexes (INDEX.md, graph.json, llms.txt)
# from brain/cards/. Run by CI on every push; writers never run it and never
# edit its outputs, which is what keeps parallel writes conflict-free.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"; cd "$HERE"
python3 - <<'PY'
import json, glob, os, datetime
cards = []
for f in sorted(glob.glob("brain/cards/*.json")):
    try: cards.append(json.load(open(f)))
    except Exception as e: print(f"skip {f}: {e}")

nodes, edges = [], []
for c in cards:
    nodes.append({k: c.get(k) for k in ("id","kind","name","estate_class","visibility","role")})
    for e in c.get("edges", []):
        edges.append({"from": c["id"], **e})
graph = {"generated": None, "node_count": len(nodes), "edge_count": len(edges),
         "nodes": nodes, "edges": edges}
json.dump(graph, open("brain/graph.json","w"), indent=1, sort_keys=True)

by_class = {}
for c in cards: by_class.setdefault(c.get("estate_class","adjacent"), []).append(c)
with open("brain/INDEX.md","w") as f:
    f.write("# The RAPP second brain — index\n\n")
    f.write(f"{len(cards)} nodes carded. Derived from `cards/` by CI — do not hand-edit.\n\n")
    for cls in sorted(by_class):
        f.write(f"## {cls}\n\n")
        for c in sorted(by_class[cls], key=lambda x: x.get("name","")):
            f.write(f"- **{c.get('name')}** (`{c.get('id')}`) — {c.get('role','')}. {c.get('summary','')[:140]}\n")
        f.write("\n")

with open("brain/llms.txt","w") as f:
    f.write("# RAPP second brain\n\n> Machine-readable map of the RAPP ecosystem. "
            "Cards in brain/cards/*.json (schema: SCHEMA.md); graph in brain/graph.json.\n\n")
    f.write(f"- {len(cards)} nodes, {len(edges)} edges\n")
    f.write("- [INDEX.md](./INDEX.md) human index · [graph.json](./graph.json) machine graph\n")
print(f"rebuilt: {len(cards)} cards -> INDEX.md, graph.json ({len(edges)} edges), llms.txt")
PY
