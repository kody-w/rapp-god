#!/usr/bin/env python3
"""
Build repos/<name>.md one-pagers and repos/_index.md from the canonical
repo inventory. Uses gh CLI via subprocess (must be authenticated).

Skips private repos (don't link them as if public).
Skips repos without a README.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Mirrored from sanitize_pii but evaluated locally to be safe.
PII_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"marriott", r"fujifilm", r"sonosite", r"bchydro", r"bc.?hydro",
        r"unilever", r"manpowergroup",
    ]
] + [re.compile(r"\bMSC\b")]


def sanitize(text: str) -> str:
    out = text
    for pat in PII_PATTERNS:
        out = pat.sub("example-co", out)
    return out


# (name, tier, role)
INVENTORY = [
    # Tier 1
    ("RAPP", 1, "Kernel + organism spec, CONSTITUTION, NEIGHBORHOOD_PROTOCOL"),
    ("RAPP-Network", 1, "Project-anchored twin neighborhoods (drop-in agent.py)"),
    ("RAPP_Store", 1, "Public catalog of rapplications (single-file agents)"),
    ("RAR", 1, "RAPP Agent Registry — browse/vote/share agent.py files"),
    ("RAPP_Sense_Store", 1, "Catalog of senses (per-channel output overlays)"),
    ("rapp-installer", 1, "One-liner install path for the brainstem"),
    ("rapp-mcp", 1, "MCP gateway — serve agents + a brainstem to any MCP host (rapp-mcp-spec/1.0)"),
    # Tier 2
    ("rappterbook", 2, "Social network for AI agents (GitHub-native)"),
    ("twin-egg-hatcher", 2, "Generic single-file hatcher for organism eggs"),
    ("ez-rapp", 2, "Electron desktop wrapper for the brainstem"),
    ("openrappter", 2, "Local-first AI agent powered by GitHub Copilot SDK"),
    ("rapp-leviathan-hub", 2, "Portable .leviathan.egg distribution hub"),
    ("rapp-commons", 2, "Cross-estate signed event stream (global hangout)"),
    ("rapp-estate", 2, "Local-first inventory of a single operator's estate"),
    ("rappter-distro", 2, "Full-bodied Rappter organism distro on top of the kernel"),
    ("rappterverse", 2, "RAPPverse federation hub"),
    ("rappterbox", 2, "Local-first brainstem console for digital organisms"),
    # Tier 3 — front doors, link only
    ("heimdall", 3, "Front door — Heimdall"),
    ("kody-twin", 3, "Front door — Kody Wildfeuer"),
    ("kody-w-twin", 3, "Front door — Kody Wildfeuer (twin v2)"),
    ("echo-brainstem", 3, "Front door — Echo (pattern-synthesizer)"),
    ("lumen-brainstem", 3, "Front door — Lumen (chronicler)"),
    ("tide-brainstem", 3, "Front door — Tide (rhythmic/oceanic voice)"),
]


def gh_repo(name: str) -> dict | None:
    try:
        out = subprocess.run(
            ["gh", "api", f"repos/kody-w/{name}"],
            capture_output=True, text=True, timeout=20,
        )
        if out.returncode != 0:
            return None
        return json.loads(out.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return None


def gh_readme(name: str) -> str | None:
    """Fetch README via raw URL (works for any default branch)."""
    import urllib.request
    for branch in ("main", "master"):
        url = f"https://raw.githubusercontent.com/kody-w/{name}/{branch}/README.md"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "rapp-bible/1.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                if resp.status == 200:
                    return resp.read().decode("utf-8", errors="replace")
        except Exception:
            continue
    return None


def first_paragraph(md: str, max_chars: int = 600) -> str:
    """Extract the first non-heading paragraph from markdown."""
    if not md:
        return ""
    lines = md.splitlines()
    buf: list[str] = []
    seen_text = False
    for ln in lines:
        s = ln.strip()
        if not s:
            if seen_text:
                break
            continue
        if s.startswith("#") or s.startswith("<!--") or s.startswith("!["):
            continue
        if s.startswith("```"):
            continue
        buf.append(s)
        seen_text = True
        if sum(len(x) for x in buf) > max_chars:
            break
    return " ".join(buf)[:max_chars]


def build_one(name: str, tier: int, role: str) -> tuple[bool, str]:
    meta = gh_repo(name)
    if meta is None:
        return False, f"could not fetch metadata for {name}"
    if meta.get("private"):
        return False, f"skipped (private): {name}"

    readme = gh_readme(name)
    summary = sanitize(first_paragraph(readme)) if readme else ""
    desc = sanitize(meta.get("description") or "")

    body = []
    body.append(f"# {name}")
    body.append("")
    body.append(f"**Tier {tier}** — {role}")
    body.append("")
    body.append(f"- Canonical: https://github.com/kody-w/{name}")
    homepage = meta.get("homepage")
    if homepage:
        body.append(f"- Site: {homepage}")
    body.append(f"- Default branch: `{meta.get('default_branch', 'main')}`")
    body.append(f"- Last updated: {meta.get('updated_at', 'unknown')}")
    body.append(f"- License: {(meta.get('license') or {}).get('spdx_id') or 'unspecified'}")
    body.append("")
    body.append("## Description")
    body.append("")
    body.append(desc if desc else "_No description set upstream._")
    body.append("")
    if summary:
        body.append("## Summary (from upstream README)")
        body.append("")
        body.append(summary)
        body.append("")
    body.append("## Role in the ecosystem")
    body.append("")
    body.append(role)
    body.append("")
    body.append("---")
    body.append("")
    body.append("_This page is generated by `scripts/build_repo_pages.py`. ")
    body.append("Upstream README is the source of truth — edit there, not here._")
    body.append("")

    dest = REPO_ROOT / "repos" / f"{name}.md"
    dest.write_text("\n".join(body), encoding="utf-8")
    return True, str(dest.relative_to(REPO_ROOT))


def build_index(results: list[tuple[str, int, str, bool, str]]) -> None:
    by_tier: dict[int, list[tuple[str, str]]] = {1: [], 2: [], 3: []}
    skipped: list[tuple[str, str]] = []
    for name, tier, role, ok, msg in results:
        if ok:
            by_tier[tier].append((name, role))
        else:
            skipped.append((name, msg))

    tier_labels = {
        1: "Tier 1 — Core specs and kernel",
        2: "Tier 2 — Distribution and ecosystem",
        3: "Tier 3 — Front doors (link only)",
    }

    lines = [
        "# Repos Index",
        "",
        "Every RAPP-ecosystem repo the Bible knows about, grouped by tier.",
        "Each entry links to the Bible one-pager (which in turn links upstream).",
        "",
    ]
    for tier in (1, 2, 3):
        lines.append(f"## {tier_labels[tier]}")
        lines.append("")
        lines.append("| Repo | Role |")
        lines.append("|------|------|")
        for name, role in sorted(by_tier[tier]):
            lines.append(f"| [{name}]({name}.md) | {role} |")
        lines.append("")

    if skipped:
        lines.append("## Skipped")
        lines.append("")
        lines.append("| Repo | Reason |")
        lines.append("|------|--------|")
        for name, msg in sorted(skipped):
            lines.append(f"| {name} | {msg} |")
        lines.append("")

    (REPO_ROOT / "repos" / "_index.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    results: list[tuple[str, int, str, bool, str]] = []
    for name, tier, role in INVENTORY:
        ok, msg = build_one(name, tier, role)
        print(f"  {'OK' if ok else 'SKIP'}: {name} — {msg}")
        results.append((name, tier, role, ok, msg))
    build_index(results)
    print(f"\nBuilt {sum(1 for r in results if r[3])} repo pages, skipped {sum(1 for r in results if not r[3])}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
