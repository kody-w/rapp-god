#!/usr/bin/env python3
"""
build_god.py — the ONLY build step for rapp-god (à la RAR's build_registry.py).

rapp-god is the registry of the whole RAPP "god" and every part it is made of. For each part it
collects every distinct VERSION that exists across the repos carrying it (the grail + its mirrors,
plus optional git history), stores each unique version as a content-addressed frame under
  versions/<part>/<sha8><ext>
append-only — nothing is ever deleted — and regenerates:

  registry.json        the generated index: parts -> versions -> which source is on which version,
                       whether an update is waiting, and a raw-URL fallback to pin ANY version.
  api/v1/status.json   the latest computed verdict (machine-readable).
  api/v1/badge.json    a shields.io endpoint badge.

It OBSERVES; it never fixes. Drift just means another version exists — a signal, never a mandate.
Every version stays reachable forever via its raw URL, so this is a load-bearing fallback.

Usage:  python3 build_god.py            (capture + regenerate)
        python3 build_god.py --no-net   (regenerate registry from already-captured frames only)
Exit code is nonzero only if a part marked "kind":"enforce" has drifted.
"""
import json, os, sys, re, hashlib, base64, subprocess, datetime, urllib.request, urllib.parse

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW_SELF = "https://raw.githubusercontent.com/kody-w/rapp-god/main"
NOW = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
NO_NET = "--no-net" in sys.argv
HIST_CAP = int(os.environ.get("RAPP_GOD_HISTORY_CAP", "60"))

def sha256(b): return hashlib.sha256(b).hexdigest()

def write_json_stable(path, obj, ts_keys=("generated",)):
    """Write JSON; if the only change vs the existing file is the timestamp field(s), preserve the
    old timestamp so the bytes stay identical — no spurious git diff on no-op CI runs."""
    new = json.loads(json.dumps(obj, ensure_ascii=False))
    if os.path.exists(path):
        try:
            old = json.load(open(path))
            if {k: v for k, v in new.items() if k not in ts_keys} == {k: v for k, v in old.items() if k not in ts_keys}:
                for k in ts_keys:
                    if k in old: new[k] = old[k]
        except Exception:
            pass
    with open(path, "w") as f:
        json.dump(new, f, indent=2, ensure_ascii=False); f.write("\n")

def fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "rapp-god"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read()
    except Exception:
        return None

def parse_raw(url):
    m = re.match(r"https://raw\.githubusercontent\.com/([^/]+)/([^/]+)/([^/]+)/(.+)$", url)
    if not m: return None
    owner, repo, ref, path = m.groups()
    return f"{owner}/{repo}", ref, urllib.parse.unquote(path)

def gh_api(path):
    try:
        out = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=90)
        return out.stdout if out.returncode == 0 else None
    except Exception:
        return None

def history_versions(url, cap=HIST_CAP):
    """(commit_sha, utc, bytes) for each commit that touched this file, newest first. Needs gh."""
    pr = parse_raw(url)
    if not pr: return
    repo, ref, path = pr
    raw = gh_api(f"repos/{repo}/commits?path={urllib.parse.quote(path)}&sha={ref}&per_page={cap}")
    if not raw: return
    try: commits = json.loads(raw)
    except Exception: return
    for c in commits[:cap]:
        csha = c.get("sha")
        utc = c.get("commit", {}).get("committer", {}).get("date")
        cont = gh_api(f"repos/{repo}/contents/{urllib.parse.quote(path)}?ref={csha}")
        if not cont: continue
        try:
            j = json.loads(cont)
            if isinstance(j, list): continue
            b = base64.b64decode(j["content"])
        except Exception:
            continue
        yield csha, utc, b

def load_prev():
    p = os.path.join(ROOT, "registry.json")
    if os.path.exists(p):
        try: return json.load(open(p))
        except Exception: return None
    return None

def main():
    manifest = json.load(open(os.path.join(ROOT, "manifest.json")))
    prev = load_prev() or {}
    prev_parts = {p["name"]: p for p in prev.get("parts", [])}

    # ---- assemble the parts list (multi-source parts win over canonical tracked files) ----
    parts_in = []
    seen = set()
    for p in manifest.get("parts", []):
        sources = [{"label": p["grail"]["label"], "role": "grail", "url": p["grail"]["url"]}]
        for m in p.get("mirrors", []):
            sources.append({"label": m["label"], "role": "mirror", "url": m["url"]})
        parts_in.append({"name": p["name"], "group": p.get("group", ""), "kind": p.get("kind", "observe"),
                         "note": p.get("note", ""), "history": bool(p.get("history")), "sources": sources})
        seen.add(p["name"])
    for comp in manifest.get("tracked", []):
        for f in comp.get("files", []):
            nm = os.path.basename(f["path"])
            if nm in seen:    # the richer multi-source part already covers it
                continue
            seen.add(nm)
            parts_in.append({"name": nm, "group": "canonical · " + comp["component"], "kind": "observe",
                             "note": comp.get("role", ""), "history": False,
                             "sources": [{"label": comp["component"], "role": "canonical", "url": f["canonical"]}]})

    out_parts, summary = [], {"parts": 0, "in_sync": 0, "drift": 0, "update_available": 0, "versions": 0}
    stats = {"frames_added": 0}
    enforce_fail = 0

    for part in parts_in:
        name = part["name"]
        ext = os.path.splitext(name)[1]
        vdir = os.path.join(ROOT, "versions", name)
        prevp = prev_parts.get(name, {})
        prev_versions = {v["sha"]: v for v in prevp.get("versions", [])}
        versions = {}   # sha -> meta

        def capture(content, source_label=None, commit=None, utc=None):
            h = sha256(content)
            v = versions.get(h)
            if not v:
                pv = prev_versions.get(h, {})
                short = h[:12]
                rel = f"versions/{name}/{short}{ext}"
                fp = os.path.join(ROOT, rel)
                if not os.path.exists(fp):
                    os.makedirs(vdir, exist_ok=True)
                    open(fp, "wb").write(content)
                    if not pv: stats["frames_added"] += 1
                v = versions[h] = {
                    "sha": h, "sha8": short, "bytes": len(content), "path": rel,
                    "url": f"{RAW_SELF}/{rel}",
                    "first_captured": pv.get("first_captured", NOW),
                    "carried_by": [], "commits": pv.get("commits", []),
                }
            if source_label and source_label not in v["carried_by"]:
                v["carried_by"].append(source_label)
            if commit and not any(c.get("sha") == commit for c in v["commits"]):
                v["commits"].append({"sha": commit, "utc": utc})
            return h

        # preserve previously-captured versions (append-only) even if a source has since moved on
        for sha, v in prev_versions.items():
            fp = os.path.join(ROOT, v.get("path", ""))
            if os.path.exists(fp):
                versions[sha] = {**v, "carried_by": []}   # carried_by recomputed from live sources below

        # live current version of each source
        src_out, grail_sha = [], None
        for s in part["sources"]:
            content = None if NO_NET else fetch(s["url"])
            cur = capture(content, s["label"]) if content is not None else None
            if s["role"] in ("grail", "canonical") and cur:
                grail_sha = cur
            src_out.append({**s, "current_sha": cur, "current_sha8": (cur[:12] if cur else None),
                            "reachable": content is not None})

        # optional git history of the grail/canonical source -> every past version
        if part["history"] and not NO_NET:
            gsrc = next((s for s in part["sources"] if s["role"] in ("grail", "canonical")), None)
            if gsrc:
                for csha, utc, b in history_versions(gsrc["url"]):
                    capture(b, commit=csha, utc=utc)

        live = {s["current_sha"] for s in src_out if s.get("current_sha")}
        drift = len(live) > 1
        update_available = grail_sha is not None and any(
            s.get("current_sha") and s["current_sha"] != grail_sha for s in src_out)

        if drift and part["kind"] == "enforce":
            enforce_fail += 1

        summary["parts"] += 1
        summary["versions"] += len(versions)
        if drift: summary["drift"] += 1
        else: summary["in_sync"] += 1
        if update_available: summary["update_available"] += 1

        vlist = sorted(versions.values(), key=lambda v: (v["first_captured"], v["sha8"]))
        out_parts.append({
            "name": name, "group": part["group"], "kind": part["kind"], "note": part["note"],
            "ext": ext, "drift": drift, "update_available": update_available,
            "grail_label": next((s["label"] for s in src_out if s["role"] in ("grail", "canonical")), None),
            "grail_sha8": (grail_sha[:12] if grail_sha else None),
            "version_count": len(versions),
            "sources": [{"label": s["label"], "role": s["role"], "url": s["url"],
                         "sha8": s.get("current_sha8"), "on_grail": (s.get("current_sha") == grail_sha),
                         "reachable": s.get("reachable", False)} for s in src_out],
            "versions": vlist,
        })

    registry = {
        "schema": "rapp-god-registry/1.0",
        "name": "rapp-god",
        "tagline": "the registry of the RAPP god and every version of every part it is made of",
        "generated": NOW,
        "self": RAW_SELF,
        "dashboard": "https://kody-w.github.io/rapp-god/",
        "policy": manifest.get("policy", {}),
        "summary": summary,
        "parts": out_parts,
        "map": manifest.get("map", []),
    }
    write_json_stable(os.path.join(ROOT, "registry.json"), registry)

    # ---- static API ----
    os.makedirs(os.path.join(ROOT, "api", "v1"), exist_ok=True)
    status = {
        "schema": "rapp-god-status/1.0", "generated": NOW,
        "dashboard": "https://kody-w.github.io/rapp-god/", "summary": summary,
        "parts": [{"name": p["name"], "group": p["group"], "kind": p["kind"],
                   "drift": p["drift"], "update_available": p["update_available"],
                   "grail_sha8": p["grail_sha8"], "versions": p["version_count"],
                   "sources": [{"label": s["label"], "role": s["role"], "sha8": s["sha8"], "on_grail": s["on_grail"]}
                               for s in p["sources"]]} for p in out_parts],
    }
    write_json_stable(os.path.join(ROOT, "api", "v1", "status.json"), status)

    d = summary["drift"]
    badge = {"schemaVersion": 1, "label": "rapp-god",
             "message": ("all in sync" if d == 0 else f"{d} part{'s' if d != 1 else ''} forked · {summary['versions']} versions held"),
             "color": "brightgreen" if d == 0 else "blue"}
    json.dump(badge, open(os.path.join(ROOT, "api", "v1", "badge.json"), "w"), indent=2, ensure_ascii=False)

    # ---- report ----
    print(f"rapp-god build @ {NOW}")
    print(f"  parts {summary['parts']} · versions held {summary['versions']} (+{stats['frames_added']} new) "
          f"· forked {summary['drift']} · updates waiting {summary['update_available']}")
    for p in out_parts:
        flag = "⑂ forked " if p["drift"] else "= in sync"
        print(f"  {flag}  {p['name']:<26} {p['version_count']} ver  grail {p['grail_sha8']}  [{p['group']}]")
    sm = os.environ.get("GITHUB_STEP_SUMMARY")
    if sm:
        with open(sm, "a") as s:
            s.write(f"# 👁️ rapp-god — {summary['parts']} parts · {summary['versions']} versions held\n\n")
            s.write(f"**{summary['drift']} forked · {summary['update_available']} updates waiting** "
                    f"(+{stats['frames_added']} new frames captured)\n\n")
            s.write("| Part | State | Versions | Grail | Group |\n|---|---|---|---|---|\n")
            for p in out_parts:
                s.write(f"| `{p['name']}` | {'⑂ forked' if p['drift'] else '= in sync'} | "
                        f"{p['version_count']} | `{p['grail_sha8']}` | {p['group']} |\n")

    if enforce_fail:
        print(f"\n⚠️  {enforce_fail} enforced part(s) drifted — failing.")
        sys.exit(1)
    print("\n✅ observe-only: drift recorded, nothing enforced.")

if __name__ == "__main__":
    main()
