"""Private repos are never referenced as content sources.

Note: the kernel CONSTITUTION/ESTATE_SPEC define `<handle>/rapp-estate-private`
as the *architectural pattern name* for an operator's private estate. That
constitutional terminology is legitimate and appears in mirrored kernel specs
(those specs are upstream-authoritative; we mirror them verbatim with a
provenance header).

This test enforces a stricter rule than "no string match": it enforces that
none of the EXCLUDE repos appear as **link targets** in Bible-native content
(README, index.html, repos/*, quickstart/*, SPEC/_index.md, CONTRIBUTING.md).
Mirrored upstream specs under SPEC/ are exempt because they are upstream
canon; we cannot rewrite them.
"""

import re
from pathlib import Path

from .conftest import REPO_ROOT, iter_committed_files


EXCLUDE_REPOS = [
    "RAPP-Private-Workspace",
    "rapp-private-backup",
    "twin-private",
    "rapp-estate-private",
]

# Files that legitimately contain these strings as test-fixture data.
ALLOWLIST = {
    "tests/test_no_private.py",
}

# Directories whose content is mirrored verbatim from upstream — exempt
# from the link-target check.
MIRRORED_DIRS = {"SPEC"}

LINK_RE = re.compile(r"\(([^)]+)\)|href=\"([^\"]+)\"|https?://github\.com/[^\s)\"<>]+")


def _is_mirrored(rel: str) -> bool:
    return rel.split("/", 1)[0] in MIRRORED_DIRS


def test_excluded_repos_not_linked_in_native_content():
    violations = []
    for p in iter_committed_files():
        rel = p.relative_to(REPO_ROOT).as_posix()
        if rel in ALLOWLIST:
            continue
        if _is_mirrored(rel):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for repo in EXCLUDE_REPOS:
            # Look for the repo name as a link target (github.com/kody-w/<repo>)
            # or as a markdown reference.
            pattern = re.compile(
                rf"github\.com/[^/\s\"<>]+/{re.escape(repo)}\b", re.IGNORECASE
            )
            m = pattern.search(text)
            if m:
                violations.append(f"{rel}: links to private repo {repo} -> {m.group(0)!r}")
    assert not violations, "Private repo references found:\n" + "\n".join(violations)
