#!/usr/bin/env python3
"""Build seed-index.json and JSON card sidecars from vault/cards/*.md.

Reads YAML frontmatter from each markdown card note in vault/cards/.
Generates:
  - seed-index.json at repo root (federation-ready)
  - cards/{seed}.json at repo root (federation-ready)

Usage: python scripts/build.py

Requires only Python stdlib. No dependencies.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VAULT_ROOT = REPO_ROOT / "vault"
VAULT_CARDS = VAULT_ROOT / "cards"
VAULT_ESSAYS = VAULT_ROOT / "essays"
OUTPUT_CARDS = REPO_ROOT / "cards"
SEED_INDEX = REPO_ROOT / "seed-index.json"
VIEW_HTML = REPO_ROOT / "vault" / "binder-view.html"
VIEW_HTML_ROOT = REPO_ROOT / "binder-view.html"
VIEW_TEMPLATE = REPO_ROOT / "scripts" / "view-template.html"
TWIN_HTML = REPO_ROOT / "index.html"
TWIN_TEMPLATE = REPO_ROOT / "scripts" / "twin-template.html"

REQUIRED_FIELDS = ("seed", "incantation", "name", "agent_id")


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML-ish frontmatter from a markdown file.

    Supports the subset of YAML we use: scalars, quoted strings, lists.
    Returns (metadata_dict, body_after_frontmatter).
    """
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    raw = text[4:end]
    body = text[end + 5 :]

    meta: dict[str, object] = {}
    for line in raw.splitlines():
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$", line)
        if not match:
            continue
        key, value = match.group(1), match.group(2).strip()
        meta[key] = _parse_value(value)
    return meta, body


def _parse_value(value: str) -> object:
    """Parse a single YAML scalar (string, int, list)."""
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_value(item.strip()) for item in inner.split(",")]
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return value
    return value


def build_card_payload(meta: dict, body: str, source_path: Path) -> dict:
    """Construct the federation-shaped JSON for a single card."""
    return {
        "version": "1.1.2",
        "seed": str(meta["seed"]),
        "incantation": meta["incantation"],
        "name": meta["name"],
        "agent_id": meta["agent_id"],
        "source": meta.get("source", "obsidian-binder"),
        "tags": meta.get("tags", []),
        "created": meta.get("created"),
        "notes_excerpt": _excerpt(body),
        "_meta": {
            "owner": "obsidian-binder",
            "source_file": f"vault/cards/{source_path.name}",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    }


def _excerpt(body: str, max_chars: int = 280) -> str:
    """First non-heading paragraph of the markdown body, trimmed."""
    text = body.strip()
    for paragraph in text.split("\n\n"):
        cleaned = paragraph.strip()
        if cleaned and not cleaned.startswith("#"):
            single = re.sub(r"\s+", " ", cleaned)
            if len(single) > max_chars:
                return single[: max_chars - 1] + "…"
            return single
    return ""


def main() -> int:
    if not VAULT_CARDS.is_dir():
        print(f"No vault/cards/ directory at {VAULT_CARDS}", file=sys.stderr)
        return 1

    OUTPUT_CARDS.mkdir(exist_ok=True)
    seeds: dict[str, str] = {}
    payloads: list[dict] = []
    errors: list[str] = []
    cards_built = 0

    for md_path in sorted(VAULT_CARDS.glob("*.md")):
        text = md_path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)

        missing = [f for f in REQUIRED_FIELDS if f not in meta]
        if missing:
            errors.append(f"{md_path.name}: missing frontmatter fields {missing}")
            continue

        seed = str(meta["seed"])
        payload = build_card_payload(meta, body, md_path)
        out_path = OUTPUT_CARDS / f"{seed}.json"
        out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        seeds[seed] = f"cards/{seed}.json"
        payloads.append({**payload, "vault_file": md_path.name, "_full_body": body, "_frontmatter": meta})
        cards_built += 1

    if errors:
        for e in errors:
            print(f"WARN: {e}", file=sys.stderr)

    index = {
        "version": "1.1.2",
        "owner": "obsidian-binder",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "card_count": len(seeds),
        "seeds": seeds,
    }
    SEED_INDEX.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    write_view_html(payloads)
    write_twin_html()
    print(f"Built {cards_built} cards → seed-index.json + cards/*.json + binder-view.html + index.html (web twin)")
    return 0


def write_twin_html() -> None:
    """Generate index.html — Obsidian-style web twin for users without Obsidian."""
    notes: dict[str, dict] = {}
    wiki_resolve: dict[str, str] = {}

    def add_note(path_key: str, title: str, kind: str, raw: str) -> None:
        meta, body = parse_frontmatter(raw)
        notes[path_key] = {
            "title": title,
            "frontmatter": meta,
            "body": body,
            "kind": kind,
        }
        # Wiki-link resolution: by title, by path stem, by full path
        wiki_resolve[title] = path_key
        wiki_resolve[Path(path_key).name] = path_key

    # README at vault root
    readme = VAULT_ROOT / "README.md"
    if readme.exists():
        add_note("README", "Vault Home", "home", readme.read_text(encoding="utf-8"))

    # Cards
    if VAULT_CARDS.is_dir():
        for md in sorted(VAULT_CARDS.glob("*.md")):
            stem = md.stem
            add_note(f"cards/{stem}", stem, "card", md.read_text(encoding="utf-8"))

    # Essays
    if VAULT_ESSAYS.is_dir():
        for md in sorted(VAULT_ESSAYS.glob("*.md")):
            stem = md.stem
            meta, _ = parse_frontmatter(md.read_text(encoding="utf-8"))
            title = meta.get("title", stem) if isinstance(meta.get("title"), str) else stem
            add_note(f"essays/{stem}", str(title), "essay", md.read_text(encoding="utf-8"))

    # Compute backlinks: scan each note body for [[wikilinks]]
    backlinks: dict[str, list[dict]] = {p: [] for p in notes}
    wiki_re = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
    for path_key, note in notes.items():
        for m in wiki_re.finditer(note["body"]):
            target_raw = m.group(1).strip()
            target_clean = target_raw.split("/")[-1].replace(".md", "")
            target = wiki_resolve.get(target_clean) or wiki_resolve.get(target_raw)
            if target and target != path_key and target in backlinks:
                # Capture surrounding line as snippet
                start = max(0, m.start() - 80)
                end = min(len(note["body"]), m.end() + 80)
                snippet = re.sub(r"\s+", " ", note["body"][start:end]).strip()
                backlinks[target].append({"from": path_key, "snippet": snippet})

    vault_data = {"notes": notes, "wikiResolve": wiki_resolve, "backlinks": backlinks}
    template = TWIN_TEMPLATE.read_text(encoding="utf-8")
    html = template.replace("/*__VAULT__*/{}", json.dumps(vault_data, ensure_ascii=False))
    TWIN_HTML.write_text(html, encoding="utf-8")


def write_view_html(payloads: list[dict]) -> None:
    """Inject the card payloads into a self-contained HTML view inside the vault."""
    template = VIEW_TEMPLATE.read_text(encoding="utf-8")
    cards_json = json.dumps(payloads, indent=2)
    generated = datetime.now(timezone.utc).isoformat()
    html = template.replace("/*__CARDS__*/[]", cards_json).replace(
        "__GENERATED__", generated
    ).replace("__COUNT__", str(len(payloads)))
    VIEW_HTML.write_text(html, encoding="utf-8")
    # Mirror to repo root so the web twin's iframe (rendered at /) resolves.
    # Obsidian reads the vault/ copy; GitHub Pages serves the root copy.
    VIEW_HTML_ROOT.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
