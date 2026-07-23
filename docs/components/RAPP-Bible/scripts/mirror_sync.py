#!/usr/bin/env python3
"""
RAPP Bible — mirror sync.

Fetches canonical spec files from upstream RAPP-ecosystem repos and writes
them into SPEC/ with a provenance header. Records any fetch failures into
_fetch_failures.json at the repo root. Reports drift between mirrored copies
and upstream HEAD.

Usage:
    python3 scripts/mirror_sync.py                  # fetch + write
    python3 scripts/mirror_sync.py --check          # check drift only, no write
    python3 scripts/mirror_sync.py --allow-drift    # write even if drift detected

Stdlib only. No external dependencies.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent

# (upstream_repo, upstream_path, local_dest_relative_to_repo_root)
MIRRORS: list[tuple[str, str, str]] = [
    ("kody-w/RAPP", "CONSTITUTION.md", "SPEC/kernel/CONSTITUTION.md"),
    ("kody-w/RAPP", "NEIGHBORHOOD_PROTOCOL.md", "SPEC/kernel/NEIGHBORHOOD_PROTOCOL.md"),
    ("kody-w/RAPP", "pages/docs/SPEC.md", "SPEC/kernel/SPEC.md"),
    ("kody-w/RAPP", "pages/docs/ESTATE_SPEC.md", "SPEC/kernel/ESTATE_SPEC.md"),
    ("kody-w/RAPP", "pages/docs/TWIN_LIFECYCLE_SPEC.md", "SPEC/kernel/TWIN_LIFECYCLE_SPEC.md"),
    ("kody-w/RAPP", "pages/docs/NEIGHBORHOOD_EGG_SPEC.md", "SPEC/kernel/NEIGHBORHOOD_EGG_SPEC.md"),
    ("kody-w/RAPP-Network", "SPEC.md", "SPEC/network/SPEC.md"),
    ("kody-w/RAPP_Store", "SPEC.md", "SPEC/catalog/SPEC.md"),
    ("kody-w/RAR", "README.md", "SPEC/registry/SPEC.md"),
    ("kody-w/RAPP_Sense_Store", "README.md", "SPEC/senses/SPEC.md"),
    ("kody-w/rapp-mcp", "SPEC.md", "SPEC/mcp/SPEC.md"),
]

RAW_URL = "https://raw.githubusercontent.com/{repo}/main/{path}"

# Customer names that must NEVER appear in committed Bible files (case-insensitive).
# Replaced with generic placeholders during mirror. This protects against accidental
# inclusion if upstream specs ever reference a private engagement.
PII_REPLACEMENTS: list[tuple[str, str]] = [
    ("marriott", "example-co"),
    ("fujifilm", "example-co"),
    ("sonosite", "example-co"),
    ("bchydro", "example-co"),
    ("bc-hydro", "example-co"),
    ("bc hydro", "example-co"),
    ("unilever", "example-co"),
    ("manpowergroup", "example-co"),
]


def sanitize_pii(text: str) -> str:
    """Strip customer names from mirrored content (case-insensitive, preserve case style)."""
    import re
    out = text
    for needle, repl in PII_REPLACEMENTS:
        pattern = re.compile(re.escape(needle), re.IGNORECASE)
        out = pattern.sub(repl, out)
    # Handle word-boundary " MSC " separately (avoid matching unrelated words)
    out = re.sub(r"\bMSC\b", "example-co", out)
    return out


def fetch_url(url: str, timeout: float = 30.0) -> Optional[bytes]:
    """Fetch a URL, returning bytes or None on failure."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "rapp-bible-sync/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return None
            return resp.read()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        return None


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def strip_provenance(text: str) -> str:
    """Remove the provenance header so we can compare to upstream."""
    lines = text.splitlines(keepends=True)
    if lines and lines[0].startswith("<!-- MIRRORED FROM"):
        # Drop provenance line + blank line that follows it
        out = lines[1:]
        if out and out[0].strip() == "":
            out = out[1:]
        return "".join(out)
    return text


def provenance_header(repo: str, path: str) -> str:
    url = f"https://github.com/{repo}/blob/main/{path}"
    return (
        f"<!-- MIRRORED FROM {url} — DO NOT EDIT HERE; edit upstream and re-sync. -->\n\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Check drift only, no write")
    parser.add_argument("--allow-drift", action="store_true", help="Write even when drift detected")
    args = parser.parse_args()

    failures: list[dict] = []
    drift: list[dict] = []
    written: list[str] = []

    for repo, upstream_path, dest_rel in MIRRORS:
        url = RAW_URL.format(repo=repo, path=upstream_path)
        print(f"[fetch] {url}")
        data = fetch_url(url)
        if data is None:
            print(f"  FAIL: could not fetch {url}")
            failures.append({"repo": repo, "path": upstream_path, "url": url})
            continue

        raw_text = data.decode("utf-8", errors="replace")
        upstream_text = sanitize_pii(raw_text)
        upstream_sha = sha256(upstream_text.encode("utf-8"))

        dest = REPO_ROOT / dest_rel
        existing_local: Optional[str] = None
        if dest.exists():
            existing_local = strip_provenance(dest.read_text(encoding="utf-8"))
            local_sha = sha256(existing_local.encode("utf-8"))
            if local_sha != upstream_sha:
                drift.append({
                    "repo": repo,
                    "path": upstream_path,
                    "dest": dest_rel,
                    "local_sha": local_sha,
                    "upstream_sha": upstream_sha,
                })
                print(f"  DRIFT: {dest_rel} local={local_sha[:8]} upstream={upstream_sha[:8]}")

        if args.check:
            continue

        content = provenance_header(repo, upstream_path) + upstream_text
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        written.append(dest_rel)
        print(f"  WROTE: {dest_rel} ({len(upstream_text)} bytes)")

        # Be gentle on rate-limit
        time.sleep(0.1)

    fail_path = REPO_ROOT / "_fetch_failures.json"
    if failures:
        fail_path.write_text(json.dumps(failures, indent=2), encoding="utf-8")
        print(f"\n{len(failures)} fetch failures written to {fail_path.name}")
    elif fail_path.exists():
        fail_path.unlink()

    print(f"\nSummary: wrote {len(written)}, drift {len(drift)}, failures {len(failures)}")

    if drift and not args.allow_drift and args.check:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
