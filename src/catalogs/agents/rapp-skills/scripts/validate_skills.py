#!/usr/bin/env python3
"""Validate the repository's Agent Skills without third-party dependencies."""

from __future__ import annotations

import re
import sys
from pathlib import Path


NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ALLOWED_FIELDS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
    "disable-model-invocation",
}


def scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    if not lines or lines[0] != "---":
        return [f"{path}: frontmatter must start on line 1"]

    try:
        end = lines.index("---", 1)
    except ValueError:
        return [f"{path}: missing closing frontmatter delimiter"]

    fields: dict[str, str] = {}
    for line_number, line in enumerate(lines[1:end], start=2):
        if not line or line[0].isspace():
            continue
        match = re.match(r"^([a-zA-Z0-9-]+):(?:[ \t]*(.*))?$", line)
        if not match:
            errors.append(f"{path}:{line_number}: invalid frontmatter entry")
            continue
        key, value = match.group(1), scalar(match.group(2) or "")
        if key not in ALLOWED_FIELDS:
            errors.append(f"{path}:{line_number}: unsupported field {key!r}")
        if key in fields:
            errors.append(f"{path}:{line_number}: duplicate field {key!r}")
        fields[key] = value

    name = fields.get("name", "")
    description = fields.get("description", "")

    if not name:
        errors.append(f"{path}: missing required field 'name'")
    elif len(name) > 64 or not NAME_RE.fullmatch(name):
        errors.append(f"{path}: invalid Agent Skills name {name!r}")
    elif name != path.parent.name:
        errors.append(
            f"{path}: name {name!r} must match directory {path.parent.name!r}"
        )

    if not description:
        errors.append(f"{path}: missing required field 'description'")
    elif len(description) > 1024:
        errors.append(f"{path}: description exceeds 1024 characters")

    compatibility = fields.get("compatibility", "")
    if len(compatibility) > 500:
        errors.append(f"{path}: compatibility exceeds 500 characters")

    if not any(line.strip() for line in lines[end + 1 :]):
        errors.append(f"{path}: Markdown body is empty")
    if len(lines) > 500:
        errors.append(f"{path}: SKILL.md exceeds the recommended 500-line limit")

    return errors


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    skills = sorted(
        path for path in root.rglob("SKILL.md") if ".git" not in path.parts
    )
    if not skills:
        print(f"No SKILL.md files found under {root}", file=sys.stderr)
        return 1

    errors = [error for path in skills for error in validate(path)]
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    print(f"Validated {len(skills)} skill(s):")
    for path in skills:
        print(f"- {path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
