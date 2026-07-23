#!/usr/bin/env python3
"""Restore cards into vault/cards/ from a binder import bundle (.txt) or a backup JSON.

Usage:
    python scripts/restore_from_bundle.py binder-import-bundle-2026-04-18.txt
    python scripts/restore_from_bundle.py obsidian-binder-backup-2026-04-18.json

Bundle format (.txt, produced by the web Import button):
    <<<FILE: vault/cards/Foo.md >>>
    ---
    seed: "..."
    ...
    ---

    body text...

    <<<FILE: vault/cards/Bar.md >>>
    ...

Backup format (.json, produced by the web Export Backup button):
    {"format": "obsidian-binder-backup", "cards": [{...with body and frontmatter...}]}

Both round-trip: export -> commit elsewhere -> restore here -> identical vault.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VAULT_CARDS = REPO_ROOT / "vault" / "cards"

FILE_MARK_RE = re.compile(r"^<<<FILE:\s*(.+?)\s*>>>\s*$")


def write_card(rel_path: str, content: str) -> Path:
    """Write content to a vault file under repo root, returning the path."""
    target = REPO_ROOT / rel_path.lstrip("/").lstrip("\\")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.rstrip() + "\n", encoding="utf-8")
    return target


def restore_bundle(bundle: Path) -> int:
    """Parse a multi-document bundle and write each FILE block to disk."""
    written = 0
    current_path: str | None = None
    buf: list[str] = []
    for raw in bundle.read_text(encoding="utf-8").splitlines():
        match = FILE_MARK_RE.match(raw)
        if match:
            if current_path is not None:
                write_card(current_path, "\n".join(buf))
                written += 1
            current_path = match.group(1)
            buf = []
        elif current_path is not None:
            buf.append(raw)
    if current_path is not None and buf:
        write_card(current_path, "\n".join(buf))
        written += 1
    return written


def serialize_frontmatter(fm: dict) -> str:
    lines = ["---"]
    for k, v in fm.items():
        if isinstance(v, list):
            lines.append(f"{k}: [{', '.join(str(x) for x in v)}]")
        elif isinstance(v, str):
            escaped = v.replace('"', '\\"')
            lines.append(f'{k}: "{escaped}"')
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines)


def restore_json_backup(backup: Path) -> int:
    """Read backup JSON and write each card to vault/cards/<vault_file>."""
    data = json.loads(backup.read_text(encoding="utf-8"))
    written = 0
    for card in data.get("cards", []):
        fm = card.get("frontmatter") or {
            "seed": card.get("seed"),
            "incantation": card.get("incantation"),
            "name": card.get("name"),
            "agent_id": card.get("agent_id"),
            "source": card.get("source"),
            "tags": card.get("tags") or [],
            "created": card.get("created"),
        }
        body = (card.get("body") or "").rstrip()
        filename = card.get("vault_file") or f"{card.get('name', 'Untitled')}.md"
        rel = f"vault/cards/{filename}"
        write_card(rel, serialize_frontmatter(fm) + "\n\n" + body)
        written += 1
    return written


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    src = Path(argv[1]).expanduser().resolve()
    if not src.exists():
        print(f"error: {src} not found", file=sys.stderr)
        return 1
    suffix = src.suffix.lower()
    if suffix == ".json":
        n = restore_json_backup(src)
        kind = "JSON backup"
    elif suffix in {".txt", ".bundle"}:
        n = restore_bundle(src)
        kind = "bundle"
    else:
        # Sniff
        head = src.read_text(encoding="utf-8", errors="replace")[:200].lstrip()
        if head.startswith("{"):
            n = restore_json_backup(src)
            kind = "JSON backup (sniffed)"
        else:
            n = restore_bundle(src)
            kind = "bundle (sniffed)"
    print(f"Restored {n} card(s) from {kind}: {src.name}")
    print(f"  → {VAULT_CARDS.relative_to(REPO_ROOT)}/")
    print("Next: run `python scripts/build.py` to regenerate federation files + view, then commit.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
