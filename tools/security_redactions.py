#!/usr/bin/env python3
"""Reconcile the file ledger with published security redactions.

The 2026-07-23 import carried a re-leaked (already revoked) Azure key, two
captured authenticated M365 sessions, and customer PII into a public
repository. Commits 93344d02, 0d2d9b6b, 68a5ec17, 5ae06fc2 and 5a16d4c6
changed or deleted those published bytes. They did not reconcile
``provenance/files.jsonl``, so every exactness oracle here has been red ever
since: the ledger still demanded the unredacted upstream blob at each
destination, and ``git_tree_id`` proofs could not be told apart from genuine
corruption.

A redaction is not a re-import. ``source_blob``/``source_path``/``source_mode``
stay exactly as captured, because ``check_assimilation`` rebuilds the pinned
upstream tree OID from those fields; rewriting them to the redacted bytes
would silently forge that proof and claim upstream shipped a key that it never
shipped. What changes is the disposition plus explicit ``published_*`` fields
recording what this public repository actually serves.

The decision table below is the reviewed remediation scope. ``--check`` fails
if the tree or the ledger drifts from it in either direction, so a later pass
cannot quietly redact one more file, nor quietly restore a leaked one.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools import assimilation  # noqa: E402


ROOT = assimilation.ROOT
LEDGER = "provenance/files.jsonl"

REDACTED = "redacted-security-boundary"
REMOVED = "removed-security-boundary"
TARGET_AUTHORED = "target-authored-remediation"
IMPORTED_EXACT = "imported-exact"

REMEDIATED_DISPOSITIONS = (REDACTED, REMOVED, TARGET_AUTHORED)

REASONS = {
    "revoked-azure-key": (
        "A re-leaked, already-revoked Azure key was published as exact "
        "upstream bytes. Rotation remains an owner action; publication does "
        "not."
    ),
    "captured-m365-session": (
        "A captured authenticated Microsoft 365 session snapshot was vendored "
        "into a public tree. No session artifact is republished."
    ),
    "customer-pii": (
        "Customer names and private rosters were published, and one denylist "
        "was itself the disclosure. Terms are injected at run time, never "
        "committed."
    ),
}

AZURE = "93344d022f1dcd17cd2920538f56e1ae38c10084"
PII = "0d2d9b6b2743027a7e23c55086c0484d2b2e5fde"
M365_SHAPE = "68a5ec17736cfc86afdbe1cbcfbb690953c1fbeb"
M365_RAR = "5ae06fc234cf4083fd585f8ff445a41883f33a80"
M365_AIBAST = "5a16d4c6a3a3f13937e99ce091b0b08d6013cd43"

_ARCHIVED_KEY_COPIES = (
    "archive/generations/local-first-tools/{generation}/{area}/{app}.html"
)
_KEY_GENERATIONS = ("localFirstTools", "localtoolsdev")
_KEY_AREAS = (
    "chrome-extension-build/apps/ai-tools",
    "exhibitions/ai-research",
    "v2/apps/experimental_ai",
)
_KEY_APPS = ("apl2ai-watch-app", "aplai-direct-app", "aplai-unified-app")


def _decisions():
    table = {}
    for generation in _KEY_GENERATIONS:
        for area in _KEY_AREAS:
            for app in _KEY_APPS:
                path = _ARCHIVED_KEY_COPIES.format(
                    generation=generation, area=area, app=app
                )
                table[path] = (REDACTED, AZURE, "revoked-azure-key")
    table[
        "archive/generations/local-first-tools/localFirstTools/my-agent-app/.env"
    ] = (REMOVED, AZURE, "revoked-azure-key")

    for path in (
        "docs/components/RAPP-Bible/SPEC/network/SPEC.md",
        "docs/components/RAPP-Bible/scripts/build_repo_pages.py",
        "docs/components/RAPP-Bible/scripts/mirror_sync.py",
        "docs/components/RAPP-Bible/tests/test_no_pii.py",
        "src/catalogs/agents/RAR/staging/@kody-w/project_twin_agent.py",
        "src/catalogs/agents/rapp-agents/tests/test_double_down_agent.py",
        "src/network/RAPP-Network/README.md",
        "src/network/RAPP-Network/SPEC.md",
        "src/network/RAPP-Network/project_twin_agent.py",
    ):
        table[path] = (REDACTED, PII, "customer-pii")
    table["docs/components/RAPP-Bible/scripts/pii_terms.py"] = (
        TARGET_AUTHORED,
        PII,
        "customer-pii",
    )

    for path in (
        "src/catalogs/agents/RAR/agents/@kody-w/transcript2prototype_agent.py",
        "src/catalogs/agents/RAR/api/v1/agent/kody-w__transcript2prototype.py",
    ):
        table[path] = (REDACTED, M365_RAR, "captured-m365-session")
    table[
        "src/catalogs/agents/rapp-shape-aibast/tools/"
        "localfirst_chat_animation_studio_tool.html"
    ] = (REDACTED, M365_SHAPE, "captured-m365-session")
    table[
        "src/catalogs/agents/rapp-shape-aibast/tools/tool_assets/"
        "snapshot-1760370929454.html"
    ] = (REMOVED, M365_SHAPE, "captured-m365-session")
    table[
        "src/catalogs/agents/aibast-agents-library/tools/"
        "localfirst_chat_animation_studio_tool.html"
    ] = (REDACTED, M365_AIBAST, "captured-m365-session")
    table[
        "src/catalogs/agents/aibast-agents-library/tools/tool_assets/"
        "snapshot-1760370929454.html"
    ] = (REMOVED, M365_AIBAST, "captured-m365-session")
    return table


DECISIONS = _decisions()

TARGET_AUTHORED_PATHS = tuple(
    sorted(path for path, entry in DECISIONS.items() if entry[0] == TARGET_AUTHORED)
)


def published_mode(path: Path) -> str:
    info = os.lstat(str(path))
    if stat.S_ISLNK(info.st_mode):
        return "120000"
    return "100755" if info.st_mode & stat.S_IXUSR else "100644"


def published_facts(destination: str):
    """Describe what this public repository actually serves at ``destination``."""
    path = ROOT / destination
    if not os.path.lexists(str(path)):
        return None
    mode = published_mode(path)
    data = assimilation.file_bytes(path, mode)
    return {
        "published_blob": assimilation.git_blob_id(data),
        "published_mode": mode,
        "published_sha256": hashlib.sha256(data).hexdigest(),
        "published_size": len(data),
    }


def load_ledger():
    return [
        json.loads(line)
        for line in (ROOT / LEDGER).read_text(encoding="utf-8").splitlines()
        if line
    ]


def target_authored_row(destination: str, commit: str, reason: str):
    facts = published_facts(destination)
    if facts is None:
        raise SystemExit("target-authored remediation file is absent: " + destination)
    row = {
        "authority_alias": False,
        "destination": destination,
        "disposition": TARGET_AUTHORED,
        "remediation_commit": commit,
        "remediation_reason": reason,
        "sha256": None,
        "size": None,
        "source_blob": None,
        "source_commit": None,
        "source_mode": None,
        "source_path": None,
        "source_ref": None,
        "source_repository": None,
        "source_tree": None,
        "source_type": None,
    }
    row.update(facts)
    return row


def reconcile(rows):
    """Return the ledger with every reviewed remediation recorded."""
    seen = set()
    reconciled = []
    for row in rows:
        destination = row.get("destination")
        decision = DECISIONS.get(destination) if destination else None
        if decision is None or row.get("disposition") == TARGET_AUTHORED:
            reconciled.append(row)
            continue
        disposition, commit, reason = decision
        if disposition == TARGET_AUTHORED:
            reconciled.append(row)
            continue
        seen.add(destination)
        updated = dict(row)
        updated["disposition"] = disposition
        updated["remediation_commit"] = commit
        updated["remediation_reason"] = reason
        facts = published_facts(str(destination))
        if disposition == REMOVED:
            if facts is not None:
                raise SystemExit(
                    "declared removed but still published: " + str(destination)
                )
            updated.update(
                {
                    "published_blob": None,
                    "published_mode": None,
                    "published_sha256": None,
                    "published_size": None,
                }
            )
        else:
            if facts is None:
                raise SystemExit(
                    "declared redacted but absent: " + str(destination)
                )
            if facts["published_blob"] == row["source_blob"]:
                raise SystemExit(
                    "declared redacted but still the upstream bytes: "
                    + str(destination)
                )
            updated.update(facts)
        reconciled.append(updated)

    for destination in TARGET_AUTHORED_PATHS:
        if any(row.get("destination") == destination for row in reconciled):
            continue
        _, commit, reason = DECISIONS[destination]
        new_row = target_authored_row(destination, commit, reason)
        component = destination.rsplit("/", 1)[0]
        insert_at = len(reconciled)
        for index, row in enumerate(reconciled):
            existing = row.get("destination")
            if not existing or not str(existing).startswith(component + "/"):
                continue
            if str(existing) > destination:
                insert_at = index
                break
            insert_at = index + 1
        reconciled.insert(insert_at, new_row)
        seen.add(destination)

    undeclared = sorted(set(DECISIONS) - seen)
    if undeclared:
        raise SystemExit(
            "reviewed remediation has no ledger destination: "
            + ", ".join(undeclared)
        )
    return reconciled


def census(rows):
    counts = {name: 0 for name in REMEDIATED_DISPOSITIONS}
    for row in rows:
        disposition = row.get("disposition")
        if disposition in counts:
            counts[disposition] += 1
    return counts


def check(rows) -> None:
    """Fail if the ledger, the decision table, or the tree disagree."""
    declared = dict(DECISIONS)
    found = {}
    for row in rows:
        disposition = row.get("disposition")
        destination = row.get("destination")
        if disposition not in REMEDIATED_DISPOSITIONS:
            if destination in declared:
                raise SystemExit(
                    "reviewed remediation is not recorded in the ledger: "
                    + str(destination)
                )
            continue
        if destination not in declared:
            raise SystemExit(
                "ledger records an unreviewed remediation: " + str(destination)
            )
        expected_disposition, commit, reason = declared[str(destination)]
        if disposition != expected_disposition:
            raise SystemExit(
                "{}: ledger says {} but the reviewed decision is {}".format(
                    destination, disposition, expected_disposition
                )
            )
        if row.get("remediation_commit") != commit:
            raise SystemExit("wrong remediation commit for " + str(destination))
        if row.get("remediation_reason") != reason:
            raise SystemExit("wrong remediation reason for " + str(destination))
        facts = published_facts(str(destination))
        if disposition == REMOVED:
            if facts is not None:
                raise SystemExit(
                    "recorded as removed but still published: " + str(destination)
                )
            if row.get("published_blob") is not None:
                raise SystemExit(
                    "removed record must not carry published bytes: "
                    + str(destination)
                )
            if not row.get("source_blob"):
                raise SystemExit(
                    "removed record must keep its upstream provenance: "
                    + str(destination)
                )
        else:
            if facts is None:
                raise SystemExit("recorded remediation is absent: " + str(destination))
            for key, value in facts.items():
                if row.get(key) != value:
                    raise SystemExit(
                        "{} drifted from the published tree at {}".format(
                            key, destination
                        )
                    )
            if disposition == REDACTED:
                if not row.get("source_blob"):
                    raise SystemExit(
                        "redaction must keep its upstream provenance: "
                        + str(destination)
                    )
                if row["published_blob"] == row["source_blob"]:
                    raise SystemExit(
                        "recorded as redacted but still the upstream bytes: "
                        + str(destination)
                    )
            else:
                if row.get("source_blob") is not None:
                    raise SystemExit(
                        "target-authored remediation must claim no upstream "
                        "source: " + str(destination)
                    )
        found[str(destination)] = disposition

    unrecorded = sorted(set(declared) - set(found))
    if unrecorded:
        raise SystemExit(
            "reviewed remediation missing from the ledger: " + ", ".join(unrecorded)
        )
    counts = census(rows)
    print(
        "Reconciled {} redacted, {} removed, and {} target-authored "
        "remediation record(s); upstream provenance preserved.".format(
            counts[REDACTED], counts[REMOVED], counts[TARGET_AUTHORED]
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.check == args.apply:
        raise SystemExit("choose exactly one of --check or --apply")
    rows = load_ledger()
    if args.check:
        check(rows)
        return 0
    reconciled = reconcile(rows)
    assimilation.write_generated(LEDGER, assimilation.jsonl_bytes(reconciled))
    counts = census(reconciled)
    print(
        "Recorded {} redacted, {} removed, and {} target-authored "
        "remediation record(s) in {}.".format(
            counts[REDACTED], counts[REMOVED], counts[TARGET_AUTHORED], LEDGER
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
