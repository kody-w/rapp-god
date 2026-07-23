#!/usr/bin/env python3
"""Import and index the frozen public RAPP source census.

Source checkouts are read-only inputs.  Imports are performed with
``git archive | tar``; this module never runs code from an imported component.
The generated ledgers are sufficient for offline integrity verification.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
INPUT_ROOT = ROOT / ".rapp-god-input"
DEFAULT_CACHE = INPUT_ROOT / "sources"

PUBLIC_COUNT = 370
PRIVATE_QUARANTINE_COUNT = 142
SELECTED_COUNT = 198
EXTERNAL_SELECTED_COUNT = 197
EXTERNAL_FILE_COUNT = 42175
EXTERNAL_LOGICAL_BYTES = 1904914693
NATIVE_FILE_COUNT = 284
NATIVE_LOGICAL_BYTES = 10387190

NATIVE_REPOSITORY = "rapp-god"
EMPTY_REPOSITORIES = {
    "BigNerdRanch",
    "LPTHW",
    "Treehouse",
    "copilotsdktown",
    "inventwithpython",
}
FALSE_POSITIVE_REPOSITORY = "PowerApps"
FULL_SCAN_ADDITIONS = {
    "AI-Agent-Templates",
    "BlazingBeard.github.io",
    "lisppy",
    "static-sharepoint",
}
CENSUS_EXCLUSIONS = {
    "AIGames",
    "AINexus",
    "RepriseClone",
    "agent-ranker",
    "aideate",
    "first-principles-to-mars",
    "github-issues-registry",
    "lisppy-shepherd",
    "mars-barn-opus-1",
    "mars-chain-node",
    "static-salesforce",
    "tinyrenderer",
}

EXTERNAL_REPOSITORIES = tuple(
    """
AI-Agent-Templates
AI-Agent-Templates-Pilot
BlazingBeard.github.io
CommunityRAPP
CrystalRAPP
RAPP
RAPP-Bible
RAPP-Network
RAPPAIClaudeCodePlayground
RAPP_Desktop
RAPP_Hub
RAPP_Sense_Store
RAPP_Store
RAPP_hippo
RAPPcards
RAPPsquared
RAR
RappterNest
ShadowRAPP
VoidRAPP
ai-agent-templates-mirror
aibast-agents-library
ant-farm
billwhalen-agent-team
braintrust-template
cowork-cookbook-rapp
double-jump
echo-brainstem
ez-rapp
heimdall
homebrew-tap
kody-twin
kody-w-twin
kody-w.github.io
leviathan
lisppy
localFirstTools
localFirstTools-main
localtoolsdev
lumen-brainstem
mars-barn
mars-barn-opus
microsoft-365-team
microsoft-se-team-neighborhood
neighborhood-example
obsidian-binder
openrappter
openrappter-alpha
openrappter-beta
openrappter-canary
openrappter-nightly
openrappter-release-train
pkstop-central-park-bandshell
pkstop-national-mall
pkstop-pike-place-market
pkstop-santa-monica-pier
pkstop-the-bean
private-workspace-template
public-art-collective
racon
rapp-1
rapp-agents
rapp-alpha
rapp-base
rapp-base-template
rapp-basket
rapp-bench
rapp-beta
rapp-body
rapp-brainstem
rapp-brainstem-beta
rapp-brainstem-sdk
rapp-brainstem-walkthrough
rapp-burrow
rapp-canary
rapp-carts
rapp-claude-skills
rapp-cli
rapp-commons
rapp-cortex
rapp-dataverse
rapp-demos
rapp-distro
rapp-docs
rapp-doorman
rapp-drift-lint
rapp-dynamic-workflows
rapp-ecosystem-brain
rapp-egg-hub
rapp-estate
rapp-eternity
rapp-flight
rapp-flight-deck
rapp-frame-net
rapp-go
rapp-god-forum
rapp-heir
rapp-hippocampus
rapp-holo
rapp-hologram
rapp-installer
rapp-installer-canary
rapp-installer-dev
rapp-kite
rapp-kited-twin
rapp-lantern
rapp-leviathan-hub
rapp-map
rapp-mcp
rapp-messaging
rapp-moment
rapp-moonshots
rapp-neighborhood-protocol
rapp-nervous-system
rapp-nightly
rapp-oneclick-deploy
rapp-plant-smoke-20260505-233637
rapp-platform
rapp-play-pokemon
rapp-postflight
rapp-quests
rapp-release-train
rapp-resident
rapp-rings
rapp-roadmap
rapp-sdk
rapp-sealed
rapp-second-brain
rapp-shape-aibast
rapp-skills
rapp-snap
rapp-spinal-cord
rapp-spine
rapp-stack-cubby
rapp-static-apis
rapp-static-mcp
rapp-store-archive
rapp-support
rapp-test-neighbor
rapp-trademarks
rapp-train
rapp-twin
rapp-twin-in-residence
rapp-ultracode
rapp-version-selector
rapp-video
rapp-vneighborhood
rapp-vscode-extension
rapp-vui
rapp-zoo
rapp_docs
rapp_orion
rappbook-admin
rappter-cli
rappter-distro
rappter-factory
rappter-mmo
rappter-plays-pokemon
rappter-vui
rappterbook
rappterbook-agent
rappterbook-agent-dna
rappterbook-agent-exchange
rappterbook-api
rappterbook-autopilot
rappterbook-commons
rappterbook-engine-test
rappterbook-first-bond
rappterbook-governance
rappterbook-impossible-product
rappterbook-knowledge-graph
rappterbook-market-maker
rappterbook-mars-barn
rappterbook-phantom
rappterbook-seedmaker
rappterbook-social-graph
rappterbook-v2
rappterbook-v2-state
rappterbook-vm
rappterbox
rappterhub
rappterverse
rappterverse-data
red-binder
rio
rionet
sim-art-collective
sim-demo-twin
static-sharepoint
tide-brainstem
twin
twin-binder
twin-egg-hatcher
vbrainstem
vneighborhood-design-studio
vneighborhood-research-lab
wildhaven-ai-homes-twin
""".split()
)

GRAIL_DIRECTORY = "rapp-installer-grail-v0.6.9"
GRAIL_DESTINATION = "vendor/grail/rapp-installer-brainstem-v0.6.9"
GRAIL_COMMIT = "bded0e1d5044d293f465e3850758f4b012d95078"
GRAIL_TREE = "3449fc34df0c4cd103792bf5a4adab34e0fd858e"
GRAIL_FILE_COUNT = 54
GRAIL_LOGICAL_BYTES = 810426

ORPHAN_GITLINK = {
    "repository": "rappterbook-agent",
    "path": "openclaw",
    "object": "39a60142bb4a8a0effba17d6d93bfbc05939f462",
}

SECRET_PATTERNS = {
    "github-token": r"gh[pousr]_[A-Za-z0-9]{36,255}",
    "aws-access-key": r"AKIA[0-9A-Z]{16}",
    "private-key": r"BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY",
    "openai-key": r"sk-(proj-)?[A-Za-z0-9_-]{32,}",
    "slack-token": r"xox[baprs]-[A-Za-z0-9-]{20,}",
}
ALLOWED_SECRET_FINDINGS = {
    ("RAPP", "private-key", "tests/test_rapp1_owner_actions.py"),
    ("kody-w.github.io", "openai-key", "learnwithkody/demos/336-50-ways-chatgpt.html"),
    ("rapp-stack-cubby", "private-key", "SECURITY.md"),
    ("rapp-stack-cubby", "private-key", "STACK_LOCK.json"),
    (
        "rapp-stack-cubby",
        "private-key",
        "cubbies/kody-w/agents/rapp_stack_cubby_agent.py",
    ),
    (
        "rapp-stack-cubby",
        "private-key",
        "cubbies/kody-w/rapplications/rapp-stack/singleton/rapp_stack_cubby_agent.py",
    ),
    ("rapp-stack-cubby", "private-key", "docs/canon/IDENTITY_AND_TRUST.md"),
    ("rapp-stack-cubby", "private-key", "docs/canon/TWIN_CHAT.md"),
    ("rapp-stack-cubby", "private-key", "src/rapp_stack_cubby/protocols/crypto.py"),
    ("rapp-stack-cubby", "private-key", "tests/packaging/test_source_archive.py"),
    ("rappterbook", "aws-access-key", "tests/test_pii_scan.py"),
    ("rappterbook", "private-key", "TESTS.md"),
    ("rappterbook", "private-key", "tests/test_pii_scan.py"),
    ("rappterverse-data", "private-key", "tests/governance/test_scanners.py"),
}

ANATOMY_PLACEHOLDERS = {
    "rapp-basket",
    "rapp-body",
    "rapp-burrow",
    "rapp-cortex",
    "rapp-hippocampus",
    "rapp-nervous-system",
    "rapp-spinal-cord",
    "rapp-spine",
}
RELEASE_CHANNELS = {
    "rapp-alpha",
    "rapp-beta",
    "rapp-canary",
    "rapp-nightly",
    "rapp-release-train",
    "rapp-installer-canary",
    "rapp-installer-dev",
    "rapp-rings",
}
RUNTIME_COMPONENTS = {
    "RAPP",
    "echo-brainstem",
    "lumen-brainstem",
    "rapp-base",
    "rapp-base-template",
    "rapp-brainstem",
    "rapp-brainstem-beta",
    "rapp-brainstem-sdk",
    "rapp-cli",
    "rapp-commons",
    "rapp-platform",
    "rapp-sdk",
    "rapp-stack-cubby",
    "tide-brainstem",
    "vbrainstem",
}
CODEC_COMPONENTS = {
    "rapp-egg-hub",
    "rapp-frame-net",
    "rapp-messaging",
    "rapp-moment",
    "rapp-sealed",
    "rapp-snap",
}
AGENT_CATALOGS = {
    "AI-Agent-Templates",
    "AI-Agent-Templates-Pilot",
    "RAR",
    "ai-agent-templates-mirror",
    "aibast-agents-library",
    "braintrust-template",
    "microsoft-365-team",
    "rapp-agents",
    "rapp-claude-skills",
    "rapp-doorman",
    "rapp-ecosystem-brain",
    "rapp-shape-aibast",
    "rapp-skills",
}
WORKFLOW_COMPONENTS = {
    "billwhalen-agent-team",
    "double-jump",
    "rapp-dynamic-workflows",
    "rapp-flight-deck",
    "rapp-quests",
    "rapp-train",
    "rapp-ultracode",
}
DOC_COMPONENTS = {
    "RAPP-Bible",
    "rapp-docs",
    "rapp-map",
    "rapp-roadmap",
    "rapp-support",
    "rapp-trademarks",
}
INTEGRATION_COMPONENTS = {
    "rapp-dataverse",
    "rapp-mcp",
    "rapp-oneclick-deploy",
    "rapp-static-mcp",
    "rapp-vscode-extension",
    "static-sharepoint",
}
NETWORK_COMPONENTS = {
    "RAPP-Network",
    "microsoft-se-team-neighborhood",
    "rapp-flight",
    "rapp-kite",
    "rapp-vneighborhood",
    "rionet",
}
SERVICE_COMPONENTS = {
    "RAPP_Hub",
    "rapp-god-forum",
    "rapp-leviathan-hub",
    "rapp-static-apis",
    "rappterhub",
    "rio",
}
EXAMPLE_COMPONENTS = {
    "CommunityRAPP",
    "RAPPAIClaudeCodePlayground",
    "cowork-cookbook-rapp",
    "neighborhood-example",
    "private-workspace-template",
    "rapp-brainstem-walkthrough",
    "rapp-demos",
    "rapp-plant-smoke-20260505-233637",
    "rapp-test-neighbor",
}
INSTANCE_COMPONENTS = {
    "RappterNest",
    "heimdall",
    "kody-twin",
    "kody-w-twin",
    "obsidian-binder",
    "pkstop-central-park-bandshell",
    "pkstop-national-mall",
    "pkstop-pike-place-market",
    "pkstop-santa-monica-pier",
    "pkstop-the-bean",
    "public-art-collective",
    "rapp-estate",
    "rapp-kited-twin",
    "rapp-resident",
    "rapp-twin",
    "rapp-twin-in-residence",
    "red-binder",
    "sim-art-collective",
    "sim-demo-twin",
    "twin",
    "twin-binder",
    "twin-egg-hatcher",
    "vneighborhood-design-studio",
    "vneighborhood-research-lab",
    "wildhaven-ai-homes-twin",
}
ARCHIVE_GENERATIONS = {
    "BlazingBeard.github.io",
    "localFirstTools",
    "localFirstTools-main",
    "localtoolsdev",
    "rapp_docs",
    "rapp_orion",
}

RECLASSIFIED_FROM = {
    "rapp-body": "archive/placeholders/catalog/rapp-body",
    "rapp-spine": "archive/placeholders/catalog/rapp-spine",
    "rapp-basket": "archive/placeholders/catalog/rapp-basket",
    "rapp-burrow": "archive/placeholders/catalog/rapp-burrow",
    "rapp-eternity": "products/components/rapp-eternity",
    "RAPP_Hub": "services/RAPP_Hub",
    "rapp-flight-deck": "src/workflows/rapp-flight-deck",
    "rapp-train": "src/workflows/rapp-train",
    "rapp-quests": "src/workflows/rapp-quests",
    "CommunityRAPP": "examples/components/CommunityRAPP",
    "rapp-resident": "instances/examples/rapp-resident",
    "rio": "services/rio",
}


def run(
    args: Sequence[str],
    cwd: Optional[Path] = None,
    capture: bool = True,
    check: bool = True,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        list(args),
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        check=check,
    )


def git_text(repo: Path, *args: str) -> str:
    return run(("git", "-C", str(repo), *args)).stdout.decode("utf-8", "strict").strip()


def classify(repository: str) -> Tuple[str, str]:
    """Return a deterministic semantic destination and component role."""
    if repository == "rapp-1":
        return "authority/protocol/rapp-1", "structural-protocol-authority"
    if repository == "rapp-installer":
        return "vendor/upstream/rapp-installer-main", "observed-installer-upstream"
    pass_two = {
        "rapp-body": ("observatory/components/rapp-body", "component-observatory"),
        "rapp-spine": ("observatory/components/rapp-spine", "component-observatory"),
        "rapp-basket": ("src/runtime/rapp-basket", "runtime"),
        "rapp-burrow": ("src/runtime/rapp-burrow", "runtime"),
        "rapp-eternity": (
            "archive/retired/protocols/rapp-eternity",
            "retired-protocol",
        ),
        "RAPP_Hub": (
            "archive/generations/catalogs/RAPP_Hub",
            "historical-catalog-generation",
        ),
        "rapp-flight-deck": (
            "src/release/control/rapp-flight-deck",
            "release-control",
        ),
        "rapp-train": ("src/release/control/rapp-train", "release-control"),
        "rapp-quests": ("src/experiences/rapp-quests", "experience"),
        "CommunityRAPP": ("services/CommunityRAPP", "service"),
        "rapp-resident": ("services/rapp-resident", "service"),
        "rio": ("products/rio", "product"),
    }
    if repository in pass_two:
        return pass_two[repository]
    if repository in ANATOMY_PLACEHOLDERS:
        return "archive/placeholders/catalog/" + repository, "anatomy-placeholder"
    if repository in ARCHIVE_GENERATIONS:
        family = "local-first-tools" if repository.startswith("local") else "historical"
        return "archive/generations/{}/{}".format(family, repository), "historical-generation"
    if repository in RELEASE_CHANNELS:
        return "src/release/channels/" + repository, "release-channel"
    if repository == "rapp-distro" or repository == "rappter-distro" or repository == "homebrew-tap":
        return "src/release/distribution/" + repository, "distribution"
    if repository in {"rapp-version-selector", "rapp-postflight"}:
        return "src/release/control/" + repository, "release-control"
    if repository in RUNTIME_COMPONENTS:
        return "src/runtime/" + repository, "runtime"
    if repository in CODEC_COMPONENTS:
        return "src/codecs/" + repository, "codec-or-envelope"
    if repository in AGENT_CATALOGS:
        return "src/catalogs/agents/" + repository, "agent-catalog"
    if repository in NETWORK_COMPONENTS:
        return "src/network/" + repository, "network-or-neighborhood"
    if repository in WORKFLOW_COMPONENTS:
        return "src/workflows/" + repository, "workflow-runtime"
    if repository in {"rapp-neighborhood-protocol"}:
        return "src/protocol/" + repository, "protocol"
    if repository in {"rapp-bench", "rapp-drift-lint"}:
        return "tests/components/" + repository, "test-or-conformance"
    if repository in DOC_COMPONENTS:
        return "docs/components/" + repository, "documentation-or-governance"
    if repository in INTEGRATION_COMPONENTS:
        return "integrations/" + repository, "integration"
    if repository in SERVICE_COMPONENTS:
        return "services/" + repository, "service"
    if repository in EXAMPLE_COMPONENTS:
        return "examples/components/" + repository, "example-or-fixture"
    if repository in INSTANCE_COMPONENTS:
        return "instances/examples/" + repository, "instance-twin-or-neighborhood"
    if repository.startswith("openrappter"):
        if repository == "openrappter":
            return "products/openrappter/core", "product"
        return "products/openrappter/release/channels/" + repository, "product-release-channel"
    if repository == "rappterbook":
        return "products/rappterbook/generations/v1/rappterbook", "social-product-generation"
    if repository in {"rappterbook-v2", "rappterbook-v2-state"}:
        return "products/rappterbook/generations/v2/" + repository, "social-product-generation"
    if repository.startswith("rappterbook-"):
        return "products/rappterbook/components/" + repository, "social-product-component"
    if repository.startswith("rappterverse"):
        return "products/rappterverse/" + repository, "social-product"
    if repository.startswith("rappter-") or repository in {
        "rappbook-admin",
        "rappterbox",
    }:
        return "products/rappter/" + repository, "product"
    if repository in {
        "RAPP_Desktop",
        "RAPP_Sense_Store",
        "RAPP_Store",
        "RAPPcards",
        "rapp-carts",
        "rapp-store-archive",
    }:
        return "products/storefronts/" + repository, "product-or-storefront"
    if repository in {
        "CrystalRAPP",
        "RAPP_hippo",
        "RAPPsquared",
        "ShadowRAPP",
        "VoidRAPP",
        "ant-farm",
        "ez-rapp",
        "mars-barn",
        "mars-barn-opus",
        "rapp-go",
        "rapp-holo",
        "rapp-hologram",
        "rapp-play-pokemon",
        "rapp-video",
        "rapp-vui",
        "rapp-zoo",
    }:
        return "src/experiences/" + repository, "experience"
    if repository in {"rapp-heir", "rapp-moonshots"}:
        return "migrations/experiments/" + repository, "migration-or-experiment"
    if repository in {"kody-w.github.io", "leviathan", "lisppy", "racon"}:
        return "products/ecosystem/" + repository, "ecosystem-product"
    return "products/components/" + repository, "product-component"


def parse_tree(repo: Path) -> List[Dict[str, object]]:
    raw = run(("git", "-C", str(repo), "ls-tree", "-rz", "-l", "--full-tree", "HEAD")).stdout
    entries: List[Dict[str, object]] = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        meta, path_bytes = record.split(b"\t", 1)
        mode, object_type, object_id, size = meta.split(b" ", 3)
        size = size.strip()
        path = path_bytes.decode("utf-8", "surrogateescape")
        if path.startswith("/") or ".." in Path(path).parts or ".git" in Path(path).parts:
            raise RuntimeError("unsafe source path in {}: {!r}".format(repo.name, path))
        entries.append(
            {
                "source_mode": mode.decode("ascii"),
                "source_type": object_type.decode("ascii"),
                "source_blob": object_id.decode("ascii"),
                "size": None if size == b"-" else int(size),
                "source_path": path,
            }
        )
    return entries


def file_bytes(path: Path, mode: str) -> bytes:
    if mode == "120000":
        return os.fsencode(os.readlink(str(path)))
    return path.read_bytes()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_id(data: bytes) -> str:
    header = "blob {}\0".format(len(data)).encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def jsonl_bytes(rows: Iterable[Dict[str, object]]) -> bytes:
    return b"".join(
        (
            json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        for row in rows
    )


def write_generated(relative: str, data: bytes) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    candidate = path.with_name(path.name + ".new")
    candidate.write_bytes(data)
    candidate.replace(path)


def archive_extract(repo: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    archive = subprocess.Popen(
        ["git", "-C", str(repo), "archive", "--format=tar", "HEAD"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    extract = subprocess.run(
        ["tar", "-xf", "-", "-C", str(destination)],
        stdin=archive.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert archive.stdout is not None
    archive.stdout.close()
    archive_stderr = archive.stderr.read() if archive.stderr else b""
    archive_rc = archive.wait()
    if archive_rc or extract.returncode:
        raise RuntimeError(
            "archive import failed for {}: {} {}".format(
                repo.name,
                archive_stderr.decode("utf-8", "replace"),
                extract.stderr.decode("utf-8", "replace"),
            )
        )


def ensure_exact_archive(repo: Path, destination: Path, entries: Sequence[Dict[str, object]]) -> int:
    """Undo archive attribute filters and restore any export-omitted tracked blob."""
    repaired = 0
    for entry in entries:
        mode = str(entry["source_mode"])
        if mode == "160000":
            continue
        path = destination / str(entry["source_path"])
        current = None
        if os.path.lexists(str(path)):
            try:
                current = file_bytes(path, mode)
            except (OSError, ValueError):
                current = None
        if current is not None and git_blob_id(current) == entry["source_blob"]:
            continue
        raw = run(
            ("git", "-C", str(repo), "cat-file", "blob", str(entry["source_blob"]))
        ).stdout
        if git_blob_id(raw) != entry["source_blob"]:
            raise RuntimeError("source object verification failed for {}".format(entry["source_path"]))
        path.parent.mkdir(parents=True, exist_ok=True)
        if os.path.lexists(str(path)):
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(str(path))
            else:
                path.unlink()
        if mode == "120000":
            os.symlink(os.fsdecode(raw), str(path))
        else:
            path.write_bytes(raw)
            path.chmod(0o755 if mode == "100755" else 0o644)
        repaired += 1
    return repaired


def secret_scan(cache: Path) -> List[Dict[str, str]]:
    findings = []
    unknown = []
    scans = [(name, cache / name) for name in EXTERNAL_REPOSITORIES]
    scans.append(("rapp-installer@brainstem-v0.6.9", cache / GRAIL_DIRECTORY))
    for label, repo in scans:
        scan_name = repo.name if label.endswith("v0.6.9") else label
        for pattern_name, pattern in SECRET_PATTERNS.items():
            result = run(
                ("git", "-C", str(repo), "grep", "-IlE", pattern, "HEAD", "--"),
                check=False,
            )
            for raw_path in result.stdout.decode("utf-8", "surrogateescape").splitlines():
                path = raw_path[5:] if raw_path.startswith("HEAD:") else raw_path
                key = (scan_name, pattern_name, path)
                finding = {
                    "repository": label,
                    "path": path,
                    "pattern": pattern_name,
                    "disposition": "contextual-test-doc-or-false-positive",
                }
                findings.append(finding)
                if key not in ALLOWED_SECRET_FINDINGS:
                    unknown.append(finding)
    if unknown:
        paths = ["{repository}:{path} ({pattern})".format(**item) for item in unknown]
        raise RuntimeError("unreviewed high-confidence secret candidates:\n" + "\n".join(paths))
    return sorted(findings, key=lambda item: (item["repository"], item["path"], item["pattern"]))


def license_info(entries: Sequence[Dict[str, object]], repository: str) -> Dict[str, object]:
    pattern = re.compile(r"(^|/)(licen[cs]e|copying|notice)(\.[^/]*)?$", re.IGNORECASE)
    files = sorted(str(entry["source_path"]) for entry in entries if pattern.search(str(entry["source_path"])))
    if repository == "rapp-1":
        return {
            "status": "no-explicit-license",
            "files": files,
            "note": "Unlicensed structural authority; no downstream license grant.",
        }
    if files:
        return {
            "status": "upstream-terms-preserved",
            "files": files,
            "note": "Consult the preserved component license and notice files.",
        }
    return {
        "status": "no-explicit-license",
        "files": [],
        "note": "No explicit license detected; all rights reserved pending owner action.",
    }


def repository_metadata(repo: Path) -> Dict[str, object]:
    head = run(("git", "-C", str(repo), "rev-parse", "--verify", "HEAD"), check=False)
    if head.returncode:
        branch = run(
            ("git", "-C", str(repo), "symbolic-ref", "--short", "HEAD"), check=False
        ).stdout.decode("utf-8", "replace").strip()
        return {
            "commit": None,
            "tree": None,
            "default_branch": branch or None,
            "file_count": 0,
            "logical_bytes": 0,
            "entries": [],
        }
    entries = parse_tree(repo)
    return {
        "commit": git_text(repo, "rev-parse", "HEAD"),
        "tree": git_text(repo, "rev-parse", "HEAD^{tree}"),
        "default_branch": git_text(repo, "branch", "--show-current"),
        "file_count": len(entries),
        "logical_bytes": sum(int(entry["size"] or 0) for entry in entries),
        "entries": entries,
    }


def source_authority_note(repository: str) -> str:
    if repository == "rapp-1":
        return "RAPP/1 rev-5 structural authority only; not authenticated section-13 acceptance."
    if repository == "rapp-installer":
        return "Observed current installer upstream; not the immutable LTS grail."
    if repository == "RAPP":
        return "Target-owned implementation baseline; explicitly not yet fully RAPP/1 conformant."
    return "Imported implementation or evidence; subordinate to federal governance and pinned authorities."


def selected_record(
    repository: str, meta: Dict[str, object], destination: str, disposition: str
) -> Dict[str, object]:
    return {
        "repository": "kody-w/" + repository,
        "visibility": "public",
        "source_commit": meta["commit"],
        "source_tree": meta["tree"],
        "default_branch": meta["default_branch"],
        "destination": destination,
        "disposition": disposition,
        "file_count": meta["file_count"],
        "logical_bytes": meta["logical_bytes"],
        "authority_note": source_authority_note(repository),
        "license": license_info(meta["entries"], repository),
    }


def imported_mappings(
    repository: str,
    meta: Dict[str, object],
    destination: str,
    disposition: str = "imported-exact",
    source_ref: str = "default-branch",
    authority_alias: bool = False,
) -> List[Dict[str, object]]:
    rows = []
    for source in meta["entries"]:
        row = {
            "source_repository": "kody-w/" + repository,
            "source_commit": meta["commit"],
            "source_tree": meta["tree"],
            "source_ref": source_ref,
            "source_path": source["source_path"],
            "source_mode": source["source_mode"],
            "source_type": source["source_type"],
            "source_blob": source["source_blob"],
            "size": source["size"],
            "authority_alias": authority_alias,
        }
        if source["source_mode"] == "160000":
            row.update(
                {
                    "sha256": None,
                    "destination": None,
                    "disposition": "external-pin-not-fetched",
                }
            )
        else:
            target = ROOT / destination / str(source["source_path"])
            data = file_bytes(target, str(source["source_mode"]))
            if git_blob_id(data) != source["source_blob"]:
                raise RuntimeError(
                    "destination differs from source blob: {}/{}".format(
                        repository, source["source_path"]
                    )
                )
            row.update(
                {
                    "sha256": sha256(data),
                    "destination": str(Path(destination) / str(source["source_path"])),
                    "disposition": disposition,
                }
            )
        rows.append(row)
    return rows


def is_protocol(path: str) -> bool:
    lower = path.lower()
    base = Path(lower).name
    return (
        "protocol" in lower
        or "schema" in lower
        or base.startswith("spec.")
        or base.endswith(".schema.json")
        or "/specs/" in "/" + lower
    )


def is_agent(path: str) -> bool:
    lower = path.lower()
    base = Path(lower).name
    return (
        base.endswith("_agent.py")
        or "/agents/" in "/" + lower
        or "/.github/agents/" in "/" + lower
        or base.endswith(".agent.md")
    )


def is_test(path: str) -> bool:
    lower = path.lower()
    base = Path(lower).name
    return (
        "/test" in "/" + lower
        or "conformance" in lower
        or "/fixture" in "/" + lower
        or base.startswith("test_")
        or base.endswith("_test.py")
        or base.endswith(".test.js")
        or base.endswith(".test.ts")
    )


def is_doc(path: str) -> bool:
    lower = path.lower()
    base = Path(lower).name
    return (
        "/docs/" in "/" + lower
        or base.startswith("readme")
        or Path(base).suffix in {".md", ".rst", ".adoc"}
    )


def is_example(path: str) -> bool:
    lower = path.lower()
    return any(token in "/" + lower for token in ("/example", "/demo", "/sample", "/walkthrough"))


def is_workflow(path: str) -> bool:
    lower = path.lower()
    return "/.github/workflows/" in "/" + lower or "/workflows/" in "/" + lower


ASSET_SUFFIXES = {
    ".7z",
    ".avi",
    ".bin",
    ".bmp",
    ".docx",
    ".eot",
    ".gif",
    ".gz",
    ".ico",
    ".jpeg",
    ".jpg",
    ".mov",
    ".mp3",
    ".mp4",
    ".otf",
    ".pdf",
    ".png",
    ".pptx",
    ".sqlite",
    ".svg",
    ".tar",
    ".tgz",
    ".ttf",
    ".wav",
    ".webm",
    ".webp",
    ".woff",
    ".woff2",
    ".xlsx",
    ".zip",
}


def is_asset(path: str) -> bool:
    lower = path.lower()
    return (
        Path(lower).suffix in ASSET_SUFFIXES
        or any(token in "/" + lower for token in ("/assets/", "/state/", "/data/", "/fixtures/"))
    )


def index_outputs(mappings: Sequence[Dict[str, object]]) -> Dict[str, bytes]:
    selected = [
        row
        for row in mappings
        if not row.get("authority_alias")
        and row.get("destination")
        and row.get("source_path")
        and row.get("source_mode") != "160000"
    ]

    def records(predicate, extra=None):
        result = []
        for row in selected:
            path = str(row["source_path"])
            if not predicate(path):
                continue
            item = {
                "repository": row["source_repository"],
                "source_path": path,
                "destination": row["destination"],
                "sha256": row["sha256"],
                "size": row["size"],
            }
            if extra:
                item.update(extra(row))
            result.append(item)
        return sorted(result, key=lambda item: (str(item["repository"]), str(item["source_path"])))

    indexes = {
        "catalog/indexes/protocols-schemas.jsonl": records(is_protocol),
        "catalog/indexes/agents.jsonl": records(is_agent),
        "catalog/indexes/tests-conformance.jsonl": records(is_test),
        "catalog/indexes/docs.jsonl": records(is_doc),
        "catalog/indexes/examples.jsonl": records(is_example),
        "catalog/indexes/workflows.jsonl": records(
            is_workflow, lambda _: {"activation": "inactive-imported"}
        ),
        "catalog/indexes/assets.jsonl": records(is_asset),
    }
    return {path: jsonl_bytes(rows) for path, rows in indexes.items()}


def observatory_baseline() -> Dict[str, object]:
    tracked = git_text(ROOT, "ls-tree", "-r", "--name-only", "HEAD").splitlines()
    immutable_prefixes = ("versions/", "snapshot/")
    rows = []
    for path in tracked:
        if not path.startswith(immutable_prefixes):
            continue
        mode = git_text(ROOT, "ls-tree", "HEAD", "--", path).split()[0]
        data = run(("git", "-C", str(ROOT), "show", "HEAD:" + path)).stdout
        rows.append({"path": path, "mode": mode, "sha256": sha256(data), "size": len(data)})
    return {
        "schema": "rapp-god-observatory-baseline/1",
        "native_commit": git_text(ROOT, "rev-parse", "HEAD"),
        "immutable_existing_paths": rows,
        "public_abi_paths": [
            "api/v1/badge.json",
            "api/v1/status.json",
            "manifest.json",
            "registry.json",
            "snapshot",
            "versions",
        ],
        "policy": "Existing frames and snapshots are immutable; registry/API paths remain stable.",
    }


def generate_catalog(
    selected: Sequence[Dict[str, object]], mappings: Sequence[Dict[str, object]]
) -> None:
    components = []
    domains: Dict[str, Dict[str, object]] = {}
    for record in selected:
        repository = str(record["repository"]).split("/", 1)[1]
        destination = str(record["destination"])
        domain = "." if destination == "." else destination.split("/", 1)[0]
        role = "native-observatory" if repository == NATIVE_REPOSITORY else classify(repository)[1]
        component = {
            "repository": record["repository"],
            "destination": destination,
            "domain": domain,
            "role": role,
            "disposition": record["disposition"],
            "source_commit": record["source_commit"],
            "source_tree": record["source_tree"],
            "file_count": record["file_count"],
            "logical_bytes": record["logical_bytes"],
            "license_status": record["license"]["status"],
        }
        components.append(component)
        summary = domains.setdefault(domain, {"domain": domain, "component_count": 0, "repositories": []})
        summary["component_count"] = int(summary["component_count"]) + 1
        summary["repositories"].append(record["repository"])
    components.sort(key=lambda item: str(item["repository"]).lower())
    domain_rows = []
    for domain in sorted(domains):
        summary = domains[domain]
        summary["repositories"] = sorted(summary["repositories"])
        domain_rows.append(summary)
    write_generated("catalog/components.jsonl", jsonl_bytes(components))
    write_generated(
        "catalog/domains.json",
        json_bytes({"schema": "rapp-god-domains/1", "domains": domain_rows}),
    )
    for path, data in index_outputs(mappings).items():
        write_generated(path, data)
    test_counts: Dict[str, int] = {}
    for row in mappings:
        if not row.get("authority_alias") and is_test(str(row["source_path"])):
            repo = str(row["source_repository"])
            test_counts[repo] = test_counts.get(repo, 0) + 1
    write_generated(
        "catalog/test-plan.json",
        json_bytes(
            {
                "schema": "rapp-god-test-plan/1",
                "policy": "Imported tests remain beside components and are indexed, not executed by root CI.",
                "root_integrity_command": "python3 -m unittest tests.test_assimilation -v",
                "component_test_file_counts": [
                    {"repository": repo, "indexed_test_files": test_counts[repo]}
                    for repo in sorted(test_counts)
                ],
            }
        ),
    )


def verify_exact_root(
    destination: Path, entries: Sequence[Dict[str, object]]
) -> None:
    for entry in entries:
        if entry["source_mode"] == "160000":
            continue
        path = destination / str(entry["source_path"])
        if not os.path.lexists(str(path)):
            raise RuntimeError("reclassification source root is incomplete: {}".format(path))
        data = file_bytes(path, str(entry["source_mode"]))
        if git_blob_id(data) != entry["source_blob"]:
            raise RuntimeError("reclassification source root is modified: {}".format(path))


def import_all(
    cache: Path,
    repair_existing: bool = False,
    reclassify_existing: bool = False,
) -> None:
    if not cache.is_dir():
        raise RuntimeError("source cache does not exist: {}".format(cache))
    if len(EXTERNAL_REPOSITORIES) != EXTERNAL_SELECTED_COUNT:
        raise RuntimeError("embedded selected source count drifted")
    cache_repositories = sorted(
        path.name
        for path in cache.iterdir()
        if path.is_dir() and path.name != GRAIL_DIRECTORY
    )
    if len(cache_repositories) != PUBLIC_COUNT:
        raise RuntimeError(
            "expected {} public cache repositories, found {}".format(
                PUBLIC_COUNT, len(cache_repositories)
            )
        )
    missing = sorted(set(EXTERNAL_REPOSITORIES) - set(cache_repositories))
    if missing:
        raise RuntimeError("selected repositories absent from cache: " + ", ".join(missing))

    findings = secret_scan(cache)
    write_generated(
        "provenance/secret-scan.json",
        json_bytes(
            {
                "schema": "rapp-god-secret-scan/1",
                "scope": "197 selected public default branches plus pinned LTS grail",
                "result": "no-high-confidence-secret",
                "finding_count": len(findings),
                "note": "Values are intentionally omitted; findings are reviewed fixtures, scanner code, documentation, or substring false positives.",
                "findings": findings,
            }
        ),
    )

    metadata: Dict[str, Dict[str, object]] = {}
    print("Reading frozen source metadata...", flush=True)
    for name in cache_repositories:
        metadata[name] = repository_metadata(cache / name)

    external_file_count = sum(int(metadata[name]["file_count"]) for name in EXTERNAL_REPOSITORIES)
    external_bytes = sum(int(metadata[name]["logical_bytes"]) for name in EXTERNAL_REPOSITORIES)
    if (external_file_count, external_bytes) != (EXTERNAL_FILE_COUNT, EXTERNAL_LOGICAL_BYTES):
        raise RuntimeError(
            "frozen source totals differ: got {} files / {} bytes".format(
                external_file_count, external_bytes
            )
        )

    if reclassify_existing:
        for name, old_destination in sorted(RECLASSIFIED_FROM.items()):
            new_destination, _ = classify(name)
            old_target = ROOT / old_destination
            new_target = ROOT / new_destination
            if old_target.exists():
                if new_target.exists():
                    raise RuntimeError(
                        "both old and new reclassification roots exist for {}".format(name)
                    )
                verify_exact_root(old_target, metadata[name]["entries"])
                shutil.rmtree(str(old_target))

    destinations: Dict[str, str] = {}
    for name in EXTERNAL_REPOSITORIES:
        destination, _ = classify(name)
        if destination in destinations:
            raise RuntimeError(
                "destination collision: {} and {} -> {}".format(
                    destinations[destination], name, destination
                )
            )
        destinations[destination] = name
        target = ROOT / destination
        if target.exists() and not repair_existing:
            raise RuntimeError("refusing to overwrite existing import destination: {}".format(target))

    print("Importing 197 exact trees with git archive | tar...", flush=True)
    mappings: List[Dict[str, object]] = []
    selected: List[Dict[str, object]] = []
    repaired_total = 0
    for number, name in enumerate(EXTERNAL_REPOSITORIES, 1):
        destination, _ = classify(name)
        target = ROOT / destination
        if not target.exists():
            archive_extract(cache / name, target)
        repaired_total += ensure_exact_archive(
            cache / name, target, metadata[name]["entries"]
        )
        mappings.extend(imported_mappings(name, metadata[name], destination))
        selected.append(selected_record(name, metadata[name], destination, "imported-exact"))
        if number % 10 == 0 or number == EXTERNAL_SELECTED_COUNT:
            print("  imported {}/{}".format(number, EXTERNAL_SELECTED_COUNT), flush=True)

    grail_repo = cache / GRAIL_DIRECTORY
    grail_meta = repository_metadata(grail_repo)
    if (
        grail_meta["commit"],
        grail_meta["tree"],
        grail_meta["file_count"],
        grail_meta["logical_bytes"],
    ) != (GRAIL_COMMIT, GRAIL_TREE, GRAIL_FILE_COUNT, GRAIL_LOGICAL_BYTES):
        raise RuntimeError("pinned grail checkout does not match immutable metadata")
    grail_target = ROOT / GRAIL_DESTINATION
    if grail_target.exists():
        if not repair_existing:
            raise RuntimeError(
                "refusing to overwrite existing import destination: {}".format(grail_target)
            )
    else:
        archive_extract(grail_repo, grail_target)
    repaired_total += ensure_exact_archive(
        grail_repo, grail_target, grail_meta["entries"]
    )
    mappings.extend(
        imported_mappings(
            "rapp-installer",
            grail_meta,
            GRAIL_DESTINATION,
            disposition="immutable-authority-fixture",
            source_ref="brainstem-v0.6.9",
            authority_alias=True,
        )
    )

    native_meta = metadata[NATIVE_REPOSITORY]
    if (native_meta["file_count"], native_meta["logical_bytes"]) != (
        NATIVE_FILE_COUNT,
        NATIVE_LOGICAL_BYTES,
    ):
        raise RuntimeError("native baseline totals differ from frozen census")
    selected.append(selected_record(NATIVE_REPOSITORY, native_meta, ".", "native-evolved"))
    selected.sort(key=lambda item: str(item["repository"]).lower())
    if len(selected) != SELECTED_COUNT:
        raise RuntimeError("selected lock count drifted")

    repo_rows = []
    for name in cache_repositories:
        meta = metadata[name]
        if name == NATIVE_REPOSITORY:
            decision = "native-evolved"
            reason = "Native append-only observatory; evolved in place rather than recursively imported."
        elif name in EXTERNAL_REPOSITORIES:
            decision = "included"
            if name in FULL_SCAN_ADDITIONS:
                reason = "Included by the full tracked-content scan."
            else:
                reason = "Included by the frozen public RAPP census."
        elif name == FALSE_POSITIVE_REPOSITORY:
            decision = "false-positive"
            reason = "PowerApps substring/fork false positive; explicitly excluded."
        elif name in EMPTY_REPOSITORIES:
            decision = "empty"
            reason = "Public default branch has no tracked tree entries."
        elif name in CENSUS_EXCLUSIONS:
            decision = "excluded"
            reason = "Explicitly outside the frozen selected set after content review."
        else:
            decision = "excluded"
            reason = "No qualifying RAPP relationship in the frozen public census."
        repo_rows.append(
            {
                "repository": "kody-w/" + name,
                "visibility": "public",
                "source_commit": meta["commit"],
                "source_tree": meta["tree"],
                "default_branch": meta["default_branch"],
                "file_count": meta["file_count"],
                "logical_bytes": meta["logical_bytes"],
                "decision": decision,
                "reason": reason,
            }
        )

    mappings.sort(
        key=lambda row: (
            str(row["source_repository"]).lower(),
            str(row["source_ref"]),
            str(row["source_path"]),
        )
    )
    write_generated("provenance/repositories.jsonl", jsonl_bytes(repo_rows))
    write_generated(
        "provenance/private-summary.json",
        json_bytes(
            {
                "schema": "rapp-god-private-quarantine/1",
                "count": PRIVATE_QUARANTINE_COUNT,
                "disposition": "quarantined-not-imported",
                "reason": "Private source payloads and per-repository private capture metadata are not imported. Existing public observatory history may contain public textual references requiring owner remediation.",
                "existing_public_history": "unresolved-owner-remediation-no-rewrite",
            }
        ),
    )
    write_generated(
        "provenance/sources.lock.json",
        json_bytes(
            {
                "schema": "rapp-god-sources-lock/1",
                "owner": "kody-w",
                "selected_count": SELECTED_COUNT,
                "external_import_count": EXTERNAL_SELECTED_COUNT,
                "external_file_count": EXTERNAL_FILE_COUNT,
                "external_logical_bytes": EXTERNAL_LOGICAL_BYTES,
                "sources": selected,
            }
        ),
    )
    write_generated("provenance/files.jsonl", jsonl_bytes(mappings))
    write_generated(
        "provenance/external-pins.json",
        json_bytes(
            {
                "schema": "rapp-god-external-pins/1",
                "pins": [
                    {
                        "source_repository": "kody-w/" + ORPHAN_GITLINK["repository"],
                        "source_path": ORPHAN_GITLINK["path"],
                        "object": ORPHAN_GITLINK["object"],
                        "disposition": "external-pin-not-fetched",
                        "reason": "Orphan gitlink with no .gitmodules; third-party content is not fetched.",
                    }
                ],
            }
        ),
    )
    write_generated(
        "provenance/observatory-baseline.json", json_bytes(observatory_baseline())
    )
    generate_catalog(selected, mappings)
    print(
        "Assimilation complete: {} selected repositories, {} external entries, {} bytes; "
        "{} archive-filtered blobs restored.".format(
            SELECTED_COUNT, EXTERNAL_FILE_COUNT, EXTERNAL_LOGICAL_BYTES, repaired_total
        )
    )


def plan() -> None:
    rows = []
    for repository in EXTERNAL_REPOSITORIES:
        destination, role = classify(repository)
        rows.append((destination.split("/", 1)[0], repository, destination, role))
    counts: Dict[str, int] = {}
    for domain, _, _, _ in rows:
        counts[domain] = counts.get(domain, 0) + 1
    print("Selected external repositories:", len(rows))
    for domain in sorted(counts):
        print("  {:12} {}".format(domain, counts[domain]))
    for _, repository, destination, role in rows:
        print("{}\t{}\t{}".format(repository, destination, role))


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("plan", help="print the deterministic semantic placement plan")
    subparsers.add_parser("check", help="run the complete offline generated/import integrity gate")
    import_parser = subparsers.add_parser("import", help="perform the one-time exact bulk import")
    import_parser.add_argument(
        "--cache",
        type=Path,
        default=Path(os.environ.get("RAPP_SOURCE_CACHE", str(DEFAULT_CACHE))),
        help="read-only directory containing the 370 shallow public checkouts",
    )
    import_parser.add_argument(
        "--repair-existing",
        action="store_true",
        help="verify/repair existing component roots and regenerate ledgers",
    )
    import_parser.add_argument(
        "--reclassify-existing",
        action="store_true",
        help="verify/remove only known old roots and reimport them at pass-two destinations",
    )
    args = parser.parse_args()
    if args.command == "plan":
        plan()
    elif args.command == "check":
        from tools.check_assimilation import IntegrityChecker

        IntegrityChecker().run_all()
        print("Assimilation integrity verified.")
    else:
        import_all(
            args.cache.resolve(),
            repair_existing=args.repair_existing or args.reclassify_existing,
            reclassify_existing=args.reclassify_existing,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
