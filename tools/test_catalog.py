#!/usr/bin/env python3
"""Generate per-component test suites and bind sanitized baseline evidence."""

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Dict, List, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools import assimilation  # noqa: E402


ROOT = assimilation.ROOT

BASELINES = [
    {
        "component": "RAPP",
        "suite": "kernel pin",
        "command_argv": ["python3", "-m", "pytest", "tests/test_kernel_pin_local.py", "-q"],
        "runtime": "Python 3.12",
        "operating_system": "Darwin",
        "exit_code": 0,
        "passed": 3,
        "failed": 0,
        "status": "pass",
    },
    {
        "component": "RAPP",
        "suite": "Node contracts",
        "command_argv": ["node", "tests/run-tests.mjs"],
        "runtime": "Node.js",
        "operating_system": "Darwin",
        "exit_code": 0,
        "passed": 23,
        "failed": 0,
        "status": "pass",
    },
    {
        "component": "rapp-dynamic-workflows",
        "suite": "source baseline",
        "command_argv": ["python3", "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider"],
        "runtime": "Python 3.12",
        "operating_system": "Darwin",
        "exit_code": 0,
        "passed": 138,
        "failed": 0,
        "status": "pass",
    },
    {
        "component": "rapp-ultracode",
        "suite": "source baseline",
        "command_argv": ["python3", "tools/wrappers/ultracode_local_rdw.py", "--run"],
        "runtime": "Python 3.12",
        "operating_system": "Darwin",
        "exit_code": 0,
        "passed": 40,
        "failed": 0,
        "status": "pass",
    },
    {
        "component": "rapp-map",
        "suite": "source-cache full-history offline gates",
        "command_argv": ["bash", ".github/scripts/run-offline-gates.sh"],
        "runtime": "Python 3.12 and Node.js",
        "operating_system": "Darwin",
        "exit_code": 0,
        "status": "pass",
        "evidence_kind": "independent-source-cache-baseline",
    },
    {
        "component": "rapp-map",
        "suite": "assimilated wrapper",
        "command_argv": ["python3", "tools/wrappers/rapp_map_offline.py", "--run"],
        "cwd": ".",
        "runtime": "Python 3.12 and Node.js",
        "operating_system": "Darwin",
        "exit_code": 3,
        "status": "blocked-private-boundary",
        "reason": "Required assimilated estate input is privacy-withheld.",
        "evidence_kind": "target-wrapper-state",
    },
    {
        "component": "rapp-1",
        "suite": "conformance",
        "command_argv": ["python3", "conformance.py"],
        "runtime": "Python 3.12",
        "operating_system": "Darwin",
        "exit_code": 1,
        "passed": 16,
        "failed": 2,
        "status": "known-upstream-failure",
        "reason": "Changed live twin artifact.",
    },
    {
        "component": "RAPP-Bible",
        "suite": "source baseline",
        "command_argv": ["python3", "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider"],
        "runtime": "Python 3.12",
        "operating_system": "Darwin",
        "exit_code": 1,
        "passed": 5,
        "failed": 12,
        "status": "known-upstream-failure",
        "reason": "One PII failure and eleven stale mirror failures.",
    },
    {
        "component": "rapp-spine",
        "suite": "source baseline",
        "command_argv": ["python3", "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider"],
        "runtime": "Python 3.12",
        "operating_system": "Darwin",
        "exit_code": 1,
        "passed": 52,
        "failed": 1,
        "status": "known-upstream-failure",
        "reason": "Stale generated crawl/coverage artifact.",
    },
    {
        "component": "rapp-spine",
        "suite": "assimilated wrapper",
        "command_argv": ["python3", "tools/wrappers/rapp_spine_offline.py", "--run"],
        "cwd": ".",
        "runtime": "Python 3.12",
        "operating_system": "Darwin",
        "exit_code": 3,
        "status": "blocked-private-boundary",
        "reason": "Required assimilated estate/spine inputs are privacy-withheld.",
        "evidence_kind": "target-wrapper-state",
    },
    {
        "component": "rapp-body",
        "suite": "verifier",
        "command_argv": ["node", "tools/verify-chain.mjs"],
        "runtime": "Node.js",
        "operating_system": "Darwin",
        "exit_code": 1,
        "status": "known-upstream-failure",
        "reason": "Current rapp/1 frames are checked against legacy rapp-frame/2.0 expectations.",
    },
]


def load_jsonl(relative: str):
    return [
        json.loads(line)
        for line in (ROOT / relative).read_text(encoding="utf-8").splitlines()
        if line
    ]


def evidence_outputs(sources: Dict[str, Dict[str, object]]):
    outputs = {}
    records = []
    for baseline in BASELINES:
        repository = "kody-w/" + str(baseline["component"])
        source = sources[repository]
        slug = "{}-{}".format(
            str(baseline["component"]).lower().replace("_", "-"),
            str(baseline["suite"]).lower().replace(" ", "-"),
        )
        path = "provenance/test-evidence/{}.json".format(slug)
        evidence = {
            "schema": "rapp-god-sanitized-test-evidence/1",
            "evidence_kind": baseline.get(
                "evidence_kind", "independent-source-baseline-summary"
            ),
            "component": baseline["component"],
            "suite": baseline["suite"],
            "command_argv": baseline["command_argv"],
            "source_commit": source["source_commit"],
            "source_tree": source["source_tree"],
            "runtime": baseline["runtime"],
            "operating_system": baseline["operating_system"],
            "exit_code": baseline["exit_code"],
            "status": baseline["status"],
            "passed": baseline.get("passed"),
            "failed": baseline.get("failed"),
            "reason": baseline.get("reason"),
            "sanitized": True,
            "contains_raw_log": False,
        }
        data = assimilation.json_bytes(evidence)
        outputs[path] = data
        records.append(
            {
                **baseline,
                "repository": repository,
                "source_commit": source["source_commit"],
                "source_tree": source["source_tree"],
                "cwd": baseline.get("cwd", source["destination"]),
                "evidence": {
                    "path": path,
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "sanitized": True,
                },
            }
        )
    return outputs, records


def suite_classification(path: str):
    lower = path.lower()
    unsafe = any(
        token in lower
        for token in ("deploy", "installer", "plant", "cloud", "live", "e2e")
    )
    return {
        "safety": "unsafe-not-allowlisted" if unsafe else "review-required",
        "network": "possible" if unsafe else "unknown",
        "credentials": "possible" if unsafe else "unknown",
        "destructive": bool(unsafe),
    }


def detect_suites(
    source: Dict[str, object], paths: Sequence[str]
) -> List[Dict[str, object]]:
    suites = []
    lower_paths = [path.lower() for path in paths]
    has_python_tests = any(
        "/tests/" in "/" + path and path.endswith(".py") for path in lower_paths
    )
    if has_python_tests:
        suites.append(
            {
                "id": "pytest",
                "command_argv": [
                    "python3",
                    "-m",
                    "pytest",
                    "tests",
                    "-q",
                    "-p",
                    "no:cacheprovider",
                ],
                "cwd": source["destination"],
                "runtime": "python",
                "operating_systems": ["any"],
                "dependencies": ["pytest", "component-local"],
                "expected_result": "unexecuted-review-required",
                "evidence": None,
                **suite_classification("tests"),
            }
        )
    package_paths = [
        path for path in paths if Path(path).name.lower() == "package.json"
    ]
    for package_path in package_paths[:1]:
        try:
            package = json.loads(
                (ROOT / str(source["destination"]) / package_path).read_text()
            )
        except (OSError, json.JSONDecodeError):
            package = {}
        if isinstance(package.get("scripts"), dict) and "test" in package["scripts"]:
            suites.append(
                {
                    "id": "npm-test",
                    "command_argv": ["npm", "test", "--", "--runInBand"],
                    "cwd": str(Path(str(source["destination"])) / Path(package_path).parent),
                    "runtime": "node",
                    "operating_systems": ["any"],
                    "dependencies": ["npm-lock-or-component-manifest"],
                    "expected_result": "unexecuted-review-required",
                    "evidence": None,
                    **suite_classification(str(package["scripts"]["test"])),
                }
            )
    scripts = sorted(
        path
        for path in paths
        if (
            Path(path).name.lower().startswith(("verify", "check"))
            or "/verify" in path.lower()
            or "/check" in path.lower()
        )
        and Path(path).suffix.lower() in {".py", ".sh", ".js", ".mjs"}
    )
    for number, path in enumerate(scripts[:5], 1):
        suffix = Path(path).suffix.lower()
        interpreter = {
            ".py": "python3",
            ".sh": "bash",
            ".js": "node",
            ".mjs": "node",
        }[suffix]
        suites.append(
            {
                "id": "verify-script-{}".format(number),
                "command_argv": [interpreter, path],
                "cwd": source["destination"],
                "runtime": interpreter,
                "operating_systems": ["any"],
                "dependencies": ["component-local"],
                "expected_result": "unexecuted-review-required",
                "evidence": None,
                **suite_classification(path),
            }
        )
    return suites


def outputs():
    lock = json.loads((ROOT / "provenance/sources.lock.json").read_text())
    sources = {row["repository"]: row for row in lock["sources"]}
    mappings = load_jsonl("provenance/files.jsonl")
    paths_by_repo = {}
    for row in mappings:
        if row.get("authority_alias") or not row.get("source_repository") or not row.get("source_path"):
            continue
        paths_by_repo.setdefault(row["source_repository"], []).append(row["source_path"])
    evidence, baselines = evidence_outputs(sources)
    baseline_by_repo = {}
    for baseline in baselines:
        baseline_by_repo.setdefault(baseline["repository"], []).append(baseline)
    records = []
    for repository, source in sorted(sources.items()):
        suites = detect_suites(source, paths_by_repo.get(repository, []))
        for baseline in baseline_by_repo.get(repository, []):
            suites.append(
                {
                    "id": "baseline-" + str(baseline["suite"]).lower().replace(" ", "-"),
                    "command_argv": baseline["command_argv"],
                    "cwd": baseline["cwd"],
                    "runtime": baseline["runtime"],
                    "operating_systems": [baseline["operating_system"]],
                    "dependencies": ["component-local", "baseline-runtime"],
                    "safety": "independent-evidence-not-root-allowlisted",
                    "network": "unknown",
                    "credentials": "unknown",
                    "destructive": False,
                    "expected_result": baseline["status"],
                    "evidence": baseline["evidence"],
                }
            )
        records.append(
            {
                "repository": repository,
                "source_commit": source["source_commit"],
                "source_tree": source["source_tree"],
                "destination": source["destination"],
                "detected_suite_count": len(suites),
                "explicit_none": not suites,
                "none_reason": (
                    "No test directory, package test command, or verify/check script detected."
                    if not suites
                    else None
                ),
                "suites": suites,
                "baseline_records": baseline_by_repo.get(repository, []),
            }
        )
    upstream = {
        "schema": "rapp-god-upstream-test-baselines/2",
        "evidence_kind": "independent-source-baseline",
        "policy": "Known failures remain failures; imported suites are not a universal root test run.",
        "records": baselines,
        "all_green": False,
    }
    result = {
        **evidence,
        "provenance/upstream-test-baselines.json": assimilation.json_bytes(upstream),
        "catalog/test-suites.jsonl": assimilation.jsonl_bytes(records),
        "catalog/test-plan.json": assimilation.json_bytes(
            {
                "schema": "rapp-god-test-plan/2",
                "components": len(records),
                "suite_catalog": "catalog/test-suites.jsonl",
                "root_allowlist": [
                    [
                        "python3",
                        "-m",
                        "unittest",
                        "tests.test_assimilation",
                        "tests.test_compat",
                        "tests.test_wrappers",
                        "tests.test_quarantine_matching",
                        "-v",
                    ],
                    ["python3", "tools/check_assimilation.py"],
                ],
                "policy": "Only target-owned allowlisted checks run in root CI.",
            }
        ),
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
            raise SystemExit("test catalogs differ: " + ", ".join(mismatches))
        print("Test catalogs and evidence bindings are deterministic.")
    else:
        for path, data in generated.items():
            assimilation.write_generated(path, data)
        print("Generated test suites for 198 components.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
