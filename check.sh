#!/usr/bin/env bash
# rapp-god drift check — a god's-eye sweep of the RAPP ecosystem.
#   Lens A: each canonical source vs this repo's snapshot (integrity).
#   Lens B: cross-repo copies that must stay byte-identical.
# Exits non-zero if any Lens A file drifts or any "identical"-expected pair diverges.
# "watch" pairs are reported but never fail the build. Writes a GitHub step summary when in CI.
set -uo pipefail
cd "$(dirname "$0")"
python3 - <<'PY'
import json, hashlib, sys, os, urllib.request
m = json.load(open('manifest.json'))
def fetch(u):
    with urllib.request.urlopen(u, timeout=30) as r: return r.read()
def h(b): return hashlib.sha256(b).hexdigest()
fail = 0
out = []   # (lens, verdict, label, detail) for the optional step summary

print("== Lens A — canonical integrity (snapshot vs canonical) ==")
for c in m['tracked']:
    for f in c['files']:
        label = f"{c['component']}/{f['path']}"
        try:
            cs = h(fetch(f['canonical'])); ss = h(open(f['snapshot'], 'rb').read())
            ok = cs == ss
            print(("  OK    " if ok else "  DRIFT ") + f"{label}  {cs[:12]} {'==' if ok else '!='} {ss[:12]}")
            out.append(("A", "✅" if ok else "⚠️ DRIFT", label, f"`{cs[:12]}` {'==' if ok else '≠'} `{ss[:12]}`"))
            if not ok: fail = 1
        except Exception as e:
            print(f"  ERR    {label}  {e}"); out.append(("A", "⚠️ error", label, str(e))); fail = 1

print("== Lens B — cross-repo drift (copies that must agree) ==")
for p in m.get('pairs', []):
    try:
        a = h(fetch(p['a']['url'])); b = h(fetch(p['b']['url'])); same = a == b
        if same:
            print(f"  OK    {p['name']}  {a[:12]} == {b[:12]}")
            out.append(("B", "✅", p['name'], f"`{a[:12]}` == `{b[:12]}`"))
        elif p['expect'] == 'identical':
            print(f"  DRIFT {p['name']}  {a[:12]} != {b[:12]}  (must match)")
            out.append(("B", "⚠️ DRIFT", p['name'], f"`{a[:12]}` ≠ `{b[:12]}` — must match")); fail = 1
        else:
            print(f"  WATCH {p['name']}  {a[:12]} != {b[:12]}  (two homes — human call)")
            out.append(("B", "👁️ differ", p['name'], f"`{a[:12]}` ≠ `{b[:12]}` — watch"))
    except Exception as e:
        print(f"  ERR   {p['name']}  {e}"); out.append(("B", "⚠️ error", p['name'], str(e))); fail = 1

print("\n" + ("⚠️  DRIFT DETECTED — see rows above." if fail else "✅ ALL IN SYNC."))

sm = os.environ.get('GITHUB_STEP_SUMMARY')
if sm:
    with open(sm, 'a') as s:
        s.write("# 👁️ rapp-god drift sweep\n\n")
        s.write("**" + ("⚠️ drift detected" if fail else "✅ all in sync") + "**\n\n")
        s.write("| Lens | Status | What | Detail |\n|---|---|---|---|\n")
        for lens, v, label, detail in out:
            s.write(f"| {lens} | {v} | `{label}` | {detail} |\n")

sys.exit(1 if fail else 0)
PY
