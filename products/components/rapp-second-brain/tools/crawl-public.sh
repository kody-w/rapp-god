#!/bin/bash
# crawl-public.sh — Phase 1 discovery + seed for the PUBLIC hemisphere ONLY.
# Inventories every public kody-w repo and writes ONE seed card per repo
# (brain/cards/*.json). Reads ONLY public metadata — never a private repo's
# contents. This is a single-writer bootstrap (one bulk commit); Opus later
# DEEPENS individual cards via tools/save-card.sh (the parallel path).
# INDEX.md / graph.json are NOT written here — CI (reduce.yml) derives them.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"; cd "$HERE"
BRAIN="$HERE/brain"; mkdir -p "$BRAIN/cards" "$BRAIN/claims"

echo "[crawl] inventorying public kody-w repos…"
gh repo list kody-w --limit 500 --no-archived \
  --json name,visibility,description,pushedAt,url,isFork \
  --jq '[.[] | select(.visibility=="PUBLIC")]' > "$BRAIN/inventory.raw.json"

# BOUNDARY ENFORCEMENT: a stray PUBLIC description may mention a PRIVATE repo
# name (e.g. "public mirror of kody-w/<private>"). The public hemisphere must
# never COLLECT private names. Read private names (metadata only, as a
# denylist) and redact any kody-w/<private> token from ingested text.
gh repo list kody-w --limit 500 --json name,visibility \
  --jq '[.[]|select(.visibility=="PRIVATE")|.name]' > "$BRAIN/.private-denylist.json"
python3 - "$BRAIN" <<'PYRED'
import json, re, sys
brain = sys.argv[1]
priv = set(json.load(open(f"{brain}/.private-denylist.json")))
raw = json.load(open(f"{brain}/inventory.raw.json"))
def redact(text):
    if not text: return text
    return re.sub(r'kody-w/([A-Za-z0-9._-]+)',
                  lambda m: f"kody-w/<private-repo>" if m.group(1) in priv else m.group(0), text)
for r in raw:
    r["description"] = redact(r.get("description"))
json.dump(raw, open(f"{brain}/inventory.json","w"), indent=1)
PYRED
rm -f "$BRAIN/inventory.raw.json" "$BRAIN/.private-denylist.json"

python3 - "$BRAIN" <<'PY'
import json, sys, datetime
brain = sys.argv[1]
inv = json.load(open(f"{brain}/inventory.json"))
def cls(n):
    if n == "rapp-installer": return "kernel"
    if n in ("rapp-canary","rapp-nightly","rapp-alpha","rapp-beta"): return "ring"
    if n == "RAPP": return "distro"
    if n.startswith("rapp-holo") or n in ("rapp-frame-net","rapp-spine"): return "spec"
    if n in ("rapp-train","rapp-tower","rapp-second-brain","rapp-map"): return "brain/deck"
    if n.startswith("rapp") or n == "RAR": return "tool/app"
    return "adjacent"
made = 0
for r in inv:
    cid = f"repo:kody-w/{r['name']}"
    safe = cid.replace('/','_').replace(':','_').replace('@','_')
    card = {
        "id": cid, "kind": "repo", "name": r["name"], "visibility": "public",
        "estate_class": cls(r["name"]), "role": "", "entry_points": [r["url"]],
        "protocols": [], "edges": [],
        "health": {"last_commit": r["pushedAt"], "ci": "unknown",
                   "pages": None, "is_fork": r["isFork"]},
        "summary": (r.get("description") or "").strip() or "(no description — deep-card in Phase 2)",
        "provenance": {"crawled_at": None, "depth": "seed",
                       "sources": [f"gh repo metadata: {r['url']}"]},
    }
    json.dump(card, open(f"{brain}/cards/{safe}.json","w"), indent=1, sort_keys=True)
    made += 1
print(f"[crawl] wrote {made} seed cards (rapp estate: "
      f"{sum(1 for r in inv if cls(r['name']) not in ('adjacent',))})")
PY

bash "$HERE/tools/rebuild.sh"
echo "[crawl] Phase 1 seed complete. Deep-card via Phase 2 (see OPUS-HANDOFF.md + COORDINATION.md)."
