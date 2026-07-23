#!/usr/bin/env python3
"""
bench.py — latency benchmark for a running RAPP brainstem (localhost:7071).

Times full /chat round-trips per model so "which model should be the default"
is a measured number, not a vibe. (v0.6.5 made Haiku the default on the claim
it responds faster — this is the receipt.)

Usage:
    python3 bench.py                          # bench the CURRENT model only
    python3 bench.py --models claude-haiku-4.5 claude-sonnet-5
    python3 bench.py --runs 5 --prompt "Say only the word pong."
    python3 bench.py --restore auto           # what to set after (default: auto)

NOTE: /models/set persists a specific pick (sticky). By default this script
restores "auto" when done. If you had a manual pick, pass --restore <that-id>.
Results print as a markdown table and save to results/ (gitignored).
"""

import argparse
import json
import statistics
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "http://localhost:7071"


def api(path, payload=None, timeout=120):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Content-Type": "application/json"},
        method="POST" if payload is not None else "GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def bench_model(model, prompt, runs):
    if model:
        api("/models/set", {"model": model})
    active = api("/health")["model"]
    times, errors = [], 0
    for i in range(runs):
        t0 = time.monotonic()
        try:
            d = api("/chat", {"user_input": prompt, "session_id": f"bench-{i}"})
            ok = bool(d.get("response"))
        except Exception:
            ok = False
        dt = time.monotonic() - t0
        if ok:
            times.append(dt)
            print(f"    run {i+1}/{runs}: {dt:.2f}s")
        else:
            errors += 1
            print(f"    run {i+1}/{runs}: ERROR")
    return {
        "model": active,
        "runs": runs,
        "errors": errors,
        "median_s": round(statistics.median(times), 2) if times else None,
        "min_s": round(min(times), 2) if times else None,
        "max_s": round(max(times), 2) if times else None,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=[None],
                    help="model ids to bench (default: whatever is active)")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--prompt", default="Reply with exactly one short sentence: what is a brainstem?")
    ap.add_argument("--restore", default="auto",
                    help='model to set when done (default "auto"; use your pinned id if you had one)')
    args = ap.parse_args()

    health = api("/health")
    print(f"brainstem v{health['version']} — starting model: {health['model']}\n")

    results = []
    for m in args.models:
        print(f"  benching: {m or health['model']}")
        results.append(bench_model(m, args.prompt, args.runs))

    if args.models != [None]:
        api("/models/set", {"model": args.restore})
        print(f"\nrestored model setting: {args.restore}")

    md = ["| model | median | min | max | errors |", "|---|---|---|---|---|"]
    for r in sorted(results, key=lambda r: (r["median_s"] is None, r["median_s"])):
        md.append(f"| {r['model']} | {r['median_s']}s | {r['min_s']}s | {r['max_s']}s | {r['errors']}/{r['runs']} |")
    table = "\n".join(md)
    print("\n" + table)

    out = Path(__file__).parent / "results"
    out.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    (out / f"bench-{stamp}.json").write_text(json.dumps(
        {"at": stamp, "prompt": args.prompt, "results": results}, indent=2))
    print(f"\nsaved: results/bench-{stamp}.json")


if __name__ == "__main__":
    main()
