#!/usr/bin/env python3
"""rappbot — the RIONet crawler.

Reads sites.json (seed sites), fetches each site's `rapp.robots.txt` to discover the RIO pages it
publishes (as GitHub raw data), fetches those pages, extracts title/snippet/outlinks, computes
**rappPageRank** over the page link graph, and writes index.json — the search index the RIO browser
queries with `search:<query>`.

Anyone joins RIONet by (1) putting a `rapp.robots.txt` at their repo's raw root listing their `.md`
pages, and (2) adding their raw base to sites.json. Pages link to each other with `rpage:<slug>`.
"""
import datetime
import json
import os
import re
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))


def get(url):
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return r.read().decode("utf-8", "replace")
    except Exception:
        return None


def parse_robots(txt):
    site, base, pages = "", "", []
    for line in (txt or "").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        k, v = k.strip().lower(), v.strip()
        if k == "site":
            site = v
        elif k == "base":
            base = v
        elif k == "pages":
            pages = [p.strip() for p in v.split(",") if p.strip()]
    return site, base, pages


def title_of(md, slug):
    m = re.search(r'^title:\s*"?([^"\n]+)"?', md, re.M) or re.search(r"^#\s+(.+)$", md, re.M)
    return m.group(1).strip() if m else slug


def snippet_of(md):
    body = re.sub(r"^---.*?---", "", md, count=1, flags=re.S)         # strip YAML frontmatter
    body = re.sub(r"\[([^\]]+)\]\(rpage:[a-z0-9-]+\)", r"\1", body)    # delink rpage links
    body = re.sub(r"[#*`>\[\]]", "", body)
    return " ".join(body.split())[:220]


def main():
    sites = json.load(open(os.path.join(HERE, "sites.json")))["sites"]
    pages = {}                                                        # slug -> record
    for base in sites:
        site, declared, plist = parse_robots(get(base.rstrip("/") + "/rapp.robots.txt"))
        b = (declared or base).rstrip("/")
        for rel in plist:
            slug = re.sub(r"\.md$", "", rel.split("/")[-1])
            md = get(b + "/" + rel)
            if md is None:
                continue
            outs = sorted(set(re.findall(r"rpage:([a-z0-9-]+)", md)))
            pages[slug] = {"url": b + "/" + rel, "title": title_of(md, slug),
                           "snippet": snippet_of(md), "site": site or b, "out": outs}

    # ---- rappPageRank (damped, with sink redistribution) ----
    slugs = list(pages)
    N = len(slugs) or 1
    d = 0.85
    rank = {s: 1.0 / N for s in slugs}
    for _ in range(50):
        nxt = {s: (1 - d) / N for s in slugs}
        for s in slugs:
            outs = [o for o in pages[s]["out"] if o in pages]
            if outs:
                for o in outs:
                    nxt[o] += d * rank[s] / len(outs)
            else:
                for t in slugs:
                    nxt[t] += d * rank[s] / N
        rank = nxt

    index = {
        "schema": "rionet-index/1.0",
        "generated": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sites": len(sites),
        "pages": [{"slug": s, "url": pages[s]["url"], "title": pages[s]["title"],
                   "snippet": pages[s]["snippet"], "site": pages[s]["site"],
                   "rank": round(rank[s], 5), "out": pages[s]["out"]}
                  for s in sorted(slugs, key=lambda s: -rank[s])],
    }
    json.dump(index, open(os.path.join(HERE, "index.json"), "w"), indent=2)
    print(f"rappbot: indexed {len(slugs)} page(s) from {len(sites)} site(s). top by rappPageRank:")
    for p in index["pages"][:10]:
        print(f"  {p['rank']:.4f}  {p['title']}  (rpage:{p['slug']})")


if __name__ == "__main__":
    main()
