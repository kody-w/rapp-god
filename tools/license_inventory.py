#!/usr/bin/env python3
"""Generate path-scoped component license records without relicensing imports."""

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Dict, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools import assimilation  # noqa: E402


ROOT = assimilation.ROOT
LICENSE_NAME = re.compile(
    r"^(licen[cs]e(?:[-_.](?:docs?|code|data|odbl|mit|apache|gpl|bsd|cc0|"
    r"[a-z0-9.-]+))?|copying(?:\.[a-z0-9.-]+)?|notice(?:\.[a-z0-9.-]+)?|"
    r"unlicense(?:\.[a-z0-9.-]+)?)$",
    re.IGNORECASE,
)


def load_jsonl(relative: str):
    return [
        json.loads(line)
        for line in (ROOT / relative).read_text(encoding="utf-8").splitlines()
        if line
    ]


def license_kind(filename: str) -> str:
    lower = filename.lower()
    if "odbl" in lower:
        return "data-odbl"
    if "docs" in lower:
        return "documentation"
    if "code" in lower:
        return "code"
    if "data" in lower:
        return "data"
    if lower.startswith("notice"):
        return "notice"
    if lower.startswith("copying"):
        return "copying"
    return "general"


def detect_text(data: bytes) -> Optional[str]:
    text = data[:65536].decode("utf-8", "ignore").lower()
    patterns = [
        ("MIT", "permission is hereby granted, free of charge"),
        ("Apache-2.0", "apache license"),
        ("GPL", "gnu general public license"),
        ("ODbL", "open database license"),
        ("CC0", "cc0"),
        ("BSD", "redistribution and use in source and binary forms"),
    ]
    matches = [label for label, marker in patterns if marker in text]
    return matches[0] if len(matches) == 1 else None


def outputs():
    lock = json.loads((ROOT / "provenance/sources.lock.json").read_text())
    components = {
        str(source["repository"]): {
            "repository": source["repository"],
            "destination": source["destination"],
            "source_commit": source["source_commit"],
            "source_tree": source["source_tree"],
            "grants": [],
        }
        for source in lock["sources"]
    }
    components["kody-w/rapp-installer@brainstem-v0.6.9"] = {
        "repository": "kody-w/rapp-installer@brainstem-v0.6.9",
        "destination": assimilation.GRAIL_DESTINATION,
        "source_commit": assimilation.GRAIL_COMMIT,
        "source_tree": assimilation.GRAIL_TREE,
        "grants": [],
    }
    mappings = load_jsonl("provenance/files.jsonl")
    for mapping in mappings:
        if not mapping.get("destination") or not mapping.get("source_path"):
            continue
        source_path = str(mapping["source_path"])
        if not LICENSE_NAME.fullmatch(Path(source_path).name):
            continue
        repository = (
            "kody-w/rapp-installer@brainstem-v0.6.9"
            if mapping.get("authority_alias")
            else str(mapping["source_repository"])
        )
        destination = ROOT / str(mapping["destination"])
        parent = str(Path(source_path).parent)
        components[repository]["grants"].append(
            {
                "license_file": source_path,
                "destination": mapping["destination"],
                "scope": "component-root" if parent == "." else "path-subtree",
                "scope_path": "." if parent == "." else parent,
                "kind": license_kind(Path(source_path).name),
                "detected_license": detect_text(destination.read_bytes()),
                "sha256": mapping["sha256"],
                "source": "tracked-file",
            }
        )
    root_license = ROOT / "LICENSE"
    if root_license.is_file():
        data = root_license.read_bytes()
        components["kody-w/rapp-god"]["grants"].append(
            {
                "license_file": "LICENSE",
                "destination": "LICENSE",
                "scope": "component-root",
                "scope_path": ".",
                "kind": "general",
                "detected_license": detect_text(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "source": "native-tracked-file",
            }
        )
    if (ROOT / "provenance/archive-members.jsonl").exists():
        for member in load_jsonl("provenance/archive-members.jsonl"):
            member_path = str(member["member_path"])
            if not LICENSE_NAME.fullmatch(Path(member_path).name):
                continue
            repository = str(member["repository"])
            components[repository]["grants"].append(
                {
                    "license_file": str(member["container_locator"]) + "!" + member_path,
                    "destination": None,
                    "scope": "archive-member-subtree",
                    "scope_path": str(Path(member_path).parent),
                    "kind": license_kind(Path(member_path).name),
                    "detected_license": None,
                    "sha256": member["sha256"],
                    "source": "unextracted-archive-member",
                }
            )
    records = []
    for repository, component in sorted(components.items()):
        grants = sorted(
            component["grants"],
            key=lambda row: (str(row["scope"]), str(row["license_file"])),
        )
        root_grants = [row for row in grants if row["scope"] == "component-root"]
        records.append(
            {
                "repository": repository,
                "destination": component["destination"],
                "source_commit": component["source_commit"],
                "source_tree": component["source_tree"],
                "status": (
                    "explicit-root-license"
                    if root_grants
                    else "path-scoped-license-only"
                    if grants
                    else "no-explicit-license-all-rights-reserved"
                ),
                "root_grant_count": len(root_grants),
                "path_scoped_grant_count": len(grants) - len(root_grants),
                "grants": grants,
                "root_mit_applies": repository == "kody-w/rapp-god",
                "target_root_mit_relicenses_component": False,
            }
        )
    data = assimilation.jsonl_bytes(records)
    summary = {
        "schema": "rapp-god-license-inventory/1",
        "components": len(records),
        "explicit_root_license": sum(
            row["status"] == "explicit-root-license" for row in records
        ),
        "path_scoped_only": sum(
            row["status"] == "path-scoped-license-only" for row in records
        ),
        "no_explicit_license": sum(
            row["status"] == "no-explicit-license-all-rights-reserved"
            for row in records
        ),
        "inventory": "provenance/licenses.jsonl",
        "root_license_boundary": "COMPONENT_LICENSES.md",
    }
    return {
        "provenance/licenses.jsonl": data,
        "provenance/license-summary.json": assimilation.json_bytes(summary),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generated = outputs()
    if args.check:
        mismatches = [
            path
            for path, data in generated.items()
            if not (ROOT / path).exists() or (ROOT / path).read_bytes() != data
        ]
        if mismatches:
            raise SystemExit("license inventory differs: " + ", ".join(mismatches))
        print("Scoped license inventory is deterministic.")
    else:
        for path, data in generated.items():
            assimilation.write_generated(path, data)
        print("Generated scoped license inventory.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
