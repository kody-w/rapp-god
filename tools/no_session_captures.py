#!/usr/bin/env python3
"""Structural content gate: no captured sessions or credential-shaped files.

The staged secret scan finds secret VALUES. This finds whole artefact CLASSES
that must never ride into a public monorepo regardless of what a pattern
matcher makes of their contents:

  * captured browser/session DOM dumps -- a 30 MB signed-in M365 capture
    reached this repo carrying a real work identity, a JWK cryptoKey with
    A256GCM key material, and 126 tenant GUIDs. Value-level scanning did not
    stop it, because none of that is shaped like a token.
  * tracked credential filenames (.env, *.copilot_token, *.pem, ...).

Deliberately shape-based, not value-based: you cannot pattern-match the
identifiers you did not know to look for, but you CAN refuse the file class
that carries them.
"""
import argparse, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CAPTURE_NAMES = re.compile(r"(^|/)(snapshot-\d{10,}\.html|.*-session-capture\..*|har-.*\.har|.*\.har)$", re.I)
CRED_NAMES = re.compile(r"(^|/)(\.env(\.[\w-]+)?|[\w.-]*\.copilot_token|[\w.-]*\.pem|[\w.-]*_token|secrets?\.(json|ya?ml|txt))$", re.I)
ALLOW = re.compile(r"(\.env\.(example|sample|template)|local\.settings\.json\.(example|sample))$", re.I)

def scan():
    bad = []
    for p in ROOT.rglob("*"):
        if not p.is_file() or ".git/" in str(p):
            continue
        rel = str(p.relative_to(ROOT))
        if ALLOW.search(rel):
            continue
        if CAPTURE_NAMES.search(rel):
            bad.append(("session-capture", rel, p.stat().st_size))
        elif CRED_NAMES.search(rel):
            bad.append(("credential-filename", rel, p.stat().st_size))
    return bad

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.parse_args()
    bad = scan()
    if bad:
        print(f"{len(bad)} forbidden artefact(s):")
        for kind, rel, size in sorted(bad)[:50]:
            print(f"  {kind:<20} {rel}  ({size} bytes)")
        print("\nThese classes must never ride into a public monorepo. Remove them "
              "upstream FIRST -- the import re-vacuums upstream wholesale, so a "
              "deletion only here returns on the next pass.")
        return 1
    print("no session captures or tracked credential filenames")
    return 0

if __name__ == "__main__":
    sys.exit(main())
