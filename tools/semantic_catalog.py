#!/usr/bin/env python3
"""Generate fail-closed semantic catalogs from exact imported provenance."""

import argparse
import ast
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import sys
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools import assimilation  # noqa: E402


ROOT = assimilation.ROOT


def load_jsonl(relative: str) -> List[Dict[str, object]]:
    with (ROOT / relative).open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def generation_for(destination: str) -> Optional[str]:
    match = re.search(r"/generations/([^/]+)", destination)
    if match:
        return match.group(1)
    match = re.search(r"/channels/([^/]+)$", destination)
    return match.group(1) if match else None


def compatibility_for(repository: str) -> List[str]:
    mapping = {
        "rapp-1": ["rapp1-identity/rev-5", "rapp1-frame/rev-5", "rapp1-egg/rev-5"],
        "rapp-mcp": ["rapp-mcp-client/1"],
        "rapp-static-mcp": [
            "rapp-static-mcp-catalog/1",
            "rapp-static-mcp-python-agent-frame/1",
            "rapp-static-mcp-browser-cell/1",
        ],
        "openrappter": ["openrappter-legacy/1"],
        "CommunityRAPP": ["communityrapp-legacy/1"],
        "rapp-dataverse": ["rapp-dataverse-legacy/1"],
        "rapp-neighborhood-protocol": ["rapp-neighborhood/1"],
    }
    if repository in mapping:
        return mapping[repository]
    if "brainstem" in repository.lower() or repository == "RAPP":
        return ["rapp1-chat-http/1", "rapp-agent-python/1"]
    return []


def component_record(source: Dict[str, object]) -> Dict[str, object]:
    repository = str(source["repository"]).split("/", 1)[1]
    destination = str(source["destination"])
    role = (
        "native-observatory"
        if source["disposition"] == "native-evolved"
        else assimilation.classify(repository)[1]
    )
    lifecycle = "active"
    currentness = "unknown"
    authority_status = "non-authoritative-import"
    canonical_for: List[str] = []
    replaced_by: Optional[str] = None
    if destination.startswith("archive/retired/"):
        lifecycle, currentness = "retired", "retired"
    elif destination.startswith("archive/"):
        lifecycle, currentness = "archived", "historical-evidence"
    elif "placeholder" in destination:
        lifecycle, currentness = "placeholder", "non-current"
    elif repository.startswith("openrappter"):
        lifecycle, currentness = "stale-snapshot", "stale"
    elif "/channels/" in destination:
        lifecycle, currentness = "release-channel", "moving"
    if repository == "rapp-1":
        authority_status = "technical-structural-authority"
        currentness = "pinned"
        canonical_for = ["rapp/1 rev-5 technical protocol"]
    elif repository == "RAPP":
        if (ROOT / destination / "CONSTITUTION.md").is_file():
            authority_status = "federal-governance-scoped"
            currentness = "pinned-implementation-baseline"
            canonical_for = [
                "ratification",
                "estate-owner-decisions",
                "governance-lifecycle",
            ]
        else:
            authority_status = "federal-governance-content-withheld"
            currentness = "quarantined"
    elif repository == "rapp-installer":
        authority_status = "observed-production-head"
        currentness = "production-head"
    if repository in {"rapp-eternity", "rapp-moment"}:
        lifecycle = "retired"
        currentness = "retired"
        replaced_by = "rapp/1 rev-5"
    return {
        "repository": source["repository"],
        "destination": destination,
        "domain": "." if destination == "." else destination.split("/", 1)[0],
        "role": role,
        "lifecycle": lifecycle,
        "currentness": currentness,
        "authority_status": authority_status,
        "authoritative": bool(canonical_for),
        "canonical_for": canonical_for,
        "replaced_by": replaced_by,
        "generation": generation_for(destination),
        "compatibility": compatibility_for(repository),
        "ownership": {
            "source_owner": "kody-w",
            "target_curator": "rapp-god",
            "publish_owner": "upstream-owner",
        },
        "publish_status": "owner-gated-no-target-publish",
        "source_commit": source["source_commit"],
        "source_tree": source["source_tree"],
        "file_count": source["file_count"],
        "logical_bytes": source["logical_bytes"],
        "license_status": source["license"]["status"],
        "disposition": source["disposition"],
    }


def grail_component() -> Dict[str, object]:
    return {
        "repository": "kody-w/rapp-installer@brainstem-v0.6.9",
        "destination": assimilation.GRAIL_DESTINATION,
        "domain": "vendor",
        "role": "immutable-lts-grail",
        "lifecycle": "immutable-lts",
        "currentness": "pinned",
        "authority_status": "kernel-authority",
        "authoritative": True,
        "canonical_for": ["brainstem.py", "basic_agent.py", "VERSION"],
        "replaced_by": None,
        "generation": "0.6.9",
        "compatibility": ["rapp1-chat-http/1", "rapp-agent-python/1"],
        "ownership": {
            "source_owner": "kody-w",
            "target_curator": "rapp-god",
            "publish_owner": "upstream-owner",
        },
        "publish_status": "immutable-no-target-publish",
        "source_commit": assimilation.GRAIL_COMMIT,
        "source_tree": assimilation.GRAIL_TREE,
        "file_count": assimilation.GRAIL_FILE_COUNT,
        "logical_bytes": assimilation.GRAIL_LOGICAL_BYTES,
        "license_status": "no-explicit-license",
        "disposition": "synthetic-immutable-authority-component",
    }


def protocol_family(path: str) -> str:
    lower = path.lower()
    if any(token in lower for token in ("rappid", "identity", "estate", "lineage")):
        return "identity"
    if "egg" in lower:
        return "egg"
    if any(token in lower for token in ("frame", "moment", "eternity")):
        return "frame-event"
    if "mcp" in lower:
        return "mcp"
    if "neighborhood" in lower:
        return "neighborhood"
    if "agent" in lower:
        return "agent-abi"
    if any(token in lower for token in ("release", "ring", "channel")):
        return "release"
    return "general"


def protocol_rows(
    mappings: Sequence[Dict[str, object]], components: Dict[str, Dict[str, object]]
) -> List[Dict[str, object]]:
    rows = []
    for mapping in mappings:
        if mapping["source_mode"] == "160000" or not assimilation.is_protocol(
            str(mapping["source_path"])
        ):
            continue
        component = components.get(str(mapping["source_repository"]))
        if mapping.get("authority_alias"):
            component = components["kody-w/rapp-installer@brainstem-v0.6.9"]
        assert component
        stale = "ecosystem-spec" in str(mapping["source_path"]).lower()
        rows.append(
            {
                "repository": component["repository"],
                "source_path": mapping["source_path"],
                "destination": mapping["destination"],
                "sha256": mapping["sha256"],
                "size": mapping["size"],
                "family": protocol_family(str(mapping["source_path"])),
                "lifecycle": "stale-imported-evidence" if stale else component["lifecycle"],
                "currentness": "stale" if stale else component["currentness"],
                "authority_status": (
                    "non-authoritative-import"
                    if stale
                    else component["authority_status"]
                ),
                "authoritative": False if stale else component["authoritative"],
                "accepted_as_rapp1_registry": False,
            }
        )
    return sorted(rows, key=lambda row: (str(row["repository"]), str(row["source_path"])))


def read_mapping(mapping: Dict[str, object], limit: int = 2_000_000) -> Optional[bytes]:
    if not mapping.get("destination") or int(mapping.get("size") or 0) > limit:
        return None
    path = ROOT / str(mapping["destination"])
    try:
        return assimilation.file_bytes(path, str(mapping["source_mode"]))
    except OSError:
        return None


def analyze_python(data: Optional[bytes]) -> Dict[str, object]:
    if data is None:
        return {"parse": "not-scanned", "classes": [], "methods": [], "stub": False}
    try:
        tree = ast.parse(data.decode("utf-8"))
    except (UnicodeDecodeError, SyntaxError):
        return {"parse": "invalid-or-non-utf8", "classes": [], "methods": [], "stub": False}
    classes = [node.name for node in tree.body if isinstance(node, ast.ClassDef)]
    methods = sorted(
        {
            child.name
            for node in tree.body
            if isinstance(node, ast.ClassDef)
            for child in node.body
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            and not child.name.startswith("_")
        }
    )
    functions = [
        node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    stub = bool(functions) and all(
        len(node.body) == 1
        and (
            isinstance(node.body[0], ast.Pass)
            or (
                isinstance(node.body[0], ast.Raise)
                and isinstance(node.body[0].exc, ast.Call)
                and getattr(node.body[0].exc.func, "id", "") == "NotImplementedError"
            )
        )
        for node in functions
    )
    return {
        "parse": "ast",
        "classes": classes,
        "methods": methods,
        "stub": stub,
        "has_perform": "perform" in methods,
    }


def agent_rows(mappings: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    candidates = [
        row
        for row in mappings
        if row["source_mode"] != "160000" and assimilation.is_agent(str(row["source_path"]))
    ]
    grouped: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    analyses = {}
    for row in candidates:
        identity = Path(str(row["source_path"])).stem.lower()
        grouped[identity].append(row)
        analyses[id(row)] = (
            analyze_python(read_mapping(row))
            if str(row["source_path"]).lower().endswith(".py")
            else {"parse": "not-python", "classes": [], "methods": [], "stub": False}
        )
    canonical = {}
    for identity, group in grouped.items():
        canonical[identity] = min(
            group,
            key=lambda row: (
                "backup" in str(row["source_path"]).lower(),
                "template" in str(row["source_path"]).lower(),
                len(str(row["source_path"])),
                str(row["source_repository"]),
                str(row["source_path"]),
            ),
        )
    rows = []
    for row in candidates:
        path = str(row["source_path"])
        lower = path.lower()
        identity = Path(path).stem.lower()
        analysis = analyses[id(row)]
        if lower.endswith(".pyc"):
            status = "compiled-pyc"
        elif "backup" in lower or lower.endswith((".bak", ".orig")):
            status = "backup"
        elif "template" in lower:
            status = "template"
        elif analysis.get("stub"):
            status = "stub"
        elif analysis.get("parse") == "ast":
            status = "executable-source"
        else:
            status = "manifest-or-document"
        unique_hashes = {item.get("sha256") for item in grouped[identity]}
        rows.append(
            {
                "identity": identity,
                "repository": row["source_repository"],
                "source_path": path,
                "destination": row["destination"],
                "sha256": row["sha256"],
                "status": status,
                "abi_profile": (
                    "rapp-agent-python/1" if analysis.get("has_perform") else "unknown"
                ),
                "classes": analysis.get("classes", []),
                "capabilities": analysis.get("methods", []),
                "canonical": row is canonical[identity],
                "alias_count": len(grouped[identity]) - 1,
                "conflict": len(unique_hashes) > 1,
                "runnable": False,
                "execution": "owner-gated-unreviewed-import",
            }
        )
    return sorted(rows, key=lambda row: (str(row["identity"]), str(row["repository"]), str(row["source_path"])))


def identity_rows(mappings: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    rows = []
    for mapping in mappings:
        path = str(mapping["source_path"])
        base = Path(path).name.lower()
        if base not in {
            "rappid.json",
            "identity.json",
            "lineage.json",
            "estate.json",
        }:
            continue
        schema = None
        findings = []
        data = read_mapping(mapping, 1_000_000)
        if data:
            try:
                parsed = json.loads(data)
                if isinstance(parsed, dict):
                    schema = parsed.get("schema")
                    if base == "rappid.json" and "rappid" not in parsed:
                        findings.append("missing-rappid-field")
            except (UnicodeDecodeError, json.JSONDecodeError):
                findings.append("invalid-json")
        rows.append(
            {
                "repository": mapping["source_repository"],
                "source_path": path,
                "destination": mapping["destination"],
                "sha256": mapping["sha256"],
                "schema": schema,
                "migration_policy": "never-remint",
                "findings": findings,
                "authoritative": False,
                "disposition": "identity-evidence-review-required",
            }
        )
    return sorted(rows, key=lambda row: (str(row["repository"]), str(row["source_path"])))


def workflow_details(data: Optional[bytes]) -> Tuple[List[str], bool, List[str]]:
    if not data:
        return [], False, []
    text = data.decode("utf-8", "replace")
    jobs = []
    in_jobs = False
    commands = []
    matrix = bool(re.search(r"(?m)^\s+matrix\s*:", text))
    for line in text.splitlines():
        if re.match(r"^jobs\s*:", line):
            in_jobs = True
            continue
        if in_jobs:
            match = re.match(r"^  ([A-Za-z0-9_.-]+)\s*:", line)
            if match:
                jobs.append(match.group(1))
            elif line and not line.startswith((" ", "#")):
                in_jobs = False
        run_match = re.match(r"^\s+run\s*:\s*(.+)$", line)
        if run_match:
            commands.append(run_match.group(1)[:500])
    return sorted(set(jobs)), matrix, commands


def workflow_rows(mappings: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    rows = []
    for mapping in mappings:
        path = str(mapping["source_path"])
        lower = path.lower()
        if not assimilation.is_workflow(path):
            continue
        if "/.github/workflows/" in "/" + lower and Path(lower).suffix in {".yml", ".yaml"}:
            kind = "github-actions"
        elif Path(lower).suffix in {".md", ".rst"} or "/docs/" in "/" + lower:
            kind = "documentation"
        else:
            kind = "template"
        jobs, matrix, commands = workflow_details(read_mapping(mapping))
        rows.append(
            {
                "repository": mapping["source_repository"],
                "source_path": path,
                "destination": mapping["destination"],
                "sha256": mapping["sha256"],
                "kind": kind,
                "jobs": jobs,
                "has_matrix": matrix,
                "commands": commands,
                "grail_workflow": bool(mapping.get("authority_alias")),
                "activation": "inactive-imported",
            }
        )
    return sorted(rows, key=lambda row: (str(row["kind"]), str(row["repository"]), str(row["source_path"])))


def runtime_rows(
    sources: Sequence[Dict[str, object]], mappings: Sequence[Dict[str, object]]
) -> List[Dict[str, object]]:
    by_repo = defaultdict(list)
    for row in mappings:
        if not row.get("authority_alias"):
            by_repo[str(row["source_repository"])].append(str(row["source_path"]).lower())
    rows = []
    for source in sources:
        repository = str(source["repository"])
        paths = by_repo.get(repository, [])
        runtimes = []
        if any(path.endswith(("pyproject.toml", "requirements.txt", "setup.py")) for path in paths):
            runtimes.append("python")
        if any(Path(path).name in {"package.json", "deno.json"} for path in paths):
            runtimes.append("node-or-browser-js")
        if any(path.endswith((".csproj", ".sln")) for path in paths):
            runtimes.append("dotnet")
        if any(Path(path).name == "cargo.toml" for path in paths):
            runtimes.append("rust")
        if any(Path(path).name == "go.mod" for path in paths):
            runtimes.append("go")
        if not runtimes and any(path.endswith((".html", ".css", ".js")) for path in paths):
            runtimes.append("static-web")
        operating_systems = ["any"]
        if any(path.endswith((".ps1", ".cmd", ".bat")) for path in paths):
            operating_systems.append("windows")
        if any(path.endswith(".sh") for path in paths):
            operating_systems.append("unix")
        rows.append(
            {
                "repository": repository,
                "destination": source["destination"],
                "runtimes": runtimes or ["undetected"],
                "operating_systems": sorted(set(operating_systems)),
                "network_default": "unknown-imported",
                "credentials": "component-specific",
                "runnable_from_root": False,
            }
        )
    return sorted(rows, key=lambda row: str(row["repository"]))


def release_overlay(
    sources: Sequence[Dict[str, object]], mappings: Sequence[Dict[str, object]]
) -> Dict[str, object]:
    names = ["rapp-alpha", "rapp-beta", "rapp-nightly"]
    source_by_name = {
        str(row["repository"]).split("/", 1)[1]: row for row in sources
    }
    blobs = {}
    sizes = {}
    for name in names:
        rows = [
            row for row in mappings if row["source_repository"] == "kody-w/" + name
        ]
        blobs[name] = {str(row["source_blob"]) for row in rows if row["source_mode"] != "160000"}
        sizes[name] = {str(row["source_blob"]): int(row["size"] or 0) for row in rows}
    shared = set.intersection(*(blobs[name] for name in names))
    return {
        "schema": "rapp-god-release-overlays/1",
        "channels": [
            {
                "repository": "kody-w/" + name,
                "tree": source_by_name[name]["source_tree"],
                "destination": source_by_name[name]["destination"],
                "ownership": "upstream-channel-owner",
            }
            for name in names
        ],
        "shared_payload": {
            "blob_count": len(shared),
            "logical_bytes": sum(sizes[names[0]].get(blob, 0) for blob in shared),
            "dedupe": "git-object-identity",
        },
        "overlay_policy": "Channels remain exact roots; shared blobs are metadata-deduplicated, never merged by filename.",
    }


def outputs() -> Dict[str, bytes]:
    lock = json.loads((ROOT / "provenance/sources.lock.json").read_text())
    sources = lock["sources"]
    mappings = [
        row
        for row in load_jsonl("provenance/files.jsonl")
        if row.get("destination") and row.get("source_path")
    ]
    components = [component_record(source) for source in sources]
    components.append(grail_component())
    components.sort(key=lambda row: str(row["repository"]))
    component_by_repo = {str(row["repository"]): row for row in components}
    protocols = protocol_rows(mappings, component_by_repo)
    family_counts = Counter(str(row["family"]) for row in protocols)
    protocol_families = [
        {
            "family": family,
            "artifact_count": count,
            "default_authority": "non-authoritative-import",
            "currentness": "explicit-record-required",
        }
        for family, count in sorted(family_counts.items())
    ]
    agents = agent_rows(mappings)
    capabilities = [
        {
            "profile_id": "imported-agent:" + str(row["repository"]) + ":" + str(row["source_path"]),
            "repository": row["repository"],
            "destination": row["destination"],
            "capabilities": row["capabilities"],
            "status": row["status"],
            "reviewed": False,
            "runnable": False,
        }
        for row in agents
    ]
    compat_profiles = json.loads((ROOT / "compat/profiles.json").read_text())["profiles"]
    capabilities.extend(
        {
            "profile_id": row["id"],
            "repository": "target-owned",
            "destination": "compat/profiles.json",
            "capabilities": [row["id"]],
            "status": row["status"],
            "reviewed": True,
            "runnable": row["runnable"],
        }
        for row in compat_profiles
    )
    capabilities.sort(key=lambda row: str(row["profile_id"]))
    workflows = workflow_rows(mappings)
    workflow_outputs = {}
    for kind, filename in {
        "github-actions": "catalog/workflows-github-actions.jsonl",
        "template": "catalog/workflows-templates.jsonl",
        "documentation": "catalog/workflows-docs.jsonl",
    }.items():
        workflow_outputs[filename] = assimilation.jsonl_bytes(
            [row for row in workflows if row["kind"] == kind]
        )
    domains = defaultdict(list)
    for component in components:
        domains[str(component["domain"])].append(str(component["repository"]))
    service_nodes = [
        {
            "id": row["repository"],
            "component": row["destination"],
            "role": row["role"],
            "lifecycle": row["lifecycle"],
            "publish_status": row["publish_status"],
        }
        for row in components
        if row["role"] in {"service", "integration", "network-or-neighborhood"}
    ]
    service_topology = {
        "schema": "rapp-god-service-topology/1",
        "nodes": service_nodes,
        "edges": [
            {
                "from": "kody-w/RAPP",
                "to": "kody-w/rapp-mcp",
                "profile": "rapp-mcp-client/1",
                "status": "adapter-required",
            },
            {
                "from": "kody-w/rapp-ultracode",
                "to": "kody-w/rapp-dynamic-workflows",
                "profile": "local-workspace-overlay",
                "status": "target-owned-overlay",
            },
        ],
        "unresolved_external_dependencies": [
            "GitHub raw/API/Pages",
            "Azure and Dataverse tenant services",
            "model provider credentials",
            "WebRTC signaling and NAT traversal",
        ],
    }
    result = {
        "catalog/components.jsonl": assimilation.jsonl_bytes(components),
        "catalog/domains.json": assimilation.json_bytes(
            {
                "schema": "rapp-god-domains/2",
                "domains": [
                    {
                        "domain": domain,
                        "component_count": len(repositories),
                        "repositories": sorted(repositories),
                    }
                    for domain, repositories in sorted(domains.items())
                ],
            }
        ),
        "catalog/indexes/protocols-schemas.jsonl": assimilation.jsonl_bytes(protocols),
        "catalog/protocol-families.jsonl": assimilation.jsonl_bytes(protocol_families),
        "catalog/agent-identities.jsonl": assimilation.jsonl_bytes(agents),
        "catalog/capabilities.jsonl": assimilation.jsonl_bytes(capabilities),
        "catalog/identity-migrations.jsonl": assimilation.jsonl_bytes(identity_rows(mappings)),
        "catalog/runtime-profiles.jsonl": assimilation.jsonl_bytes(runtime_rows(sources, mappings)),
        "catalog/service-topology.json": assimilation.json_bytes(service_topology),
        "catalog/release-overlays.json": assimilation.json_bytes(
            release_overlay(sources, mappings)
        ),
        "catalog/product-lifecycle.json": assimilation.json_bytes(
            {
                "schema": "rapp-god-product-lifecycle/1",
                "openrappter": {
                    "component": "products/openrappter/core",
                    "lifecycle": "stale-snapshot",
                    "ownership": "upstream-owner",
                    "target_publish": False,
                },
                "retired_protocols": [
                    "rapp-eternity/1.0",
                    "rapp-moment/1.0",
                ],
            }
        ),
        **workflow_outputs,
    }
    return result


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
            raise SystemExit("semantic catalogs differ: " + ", ".join(mismatches))
        print("Semantic catalogs are deterministic.")
    else:
        for path, data in generated.items():
            assimilation.write_generated(path, data)
        print("Generated {} semantic catalog files.".format(len(generated)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
