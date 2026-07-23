"""No customer/engagement names appear in committed Bible content.

The PII scan covers all committed files EXCEPT:
- This test file (which lists the patterns).
- scripts/mirror_sync.py and scripts/build_repo_pages.py (which contain
  the same patterns as the *filter* that strips them — not as content).
"""

import re

from .conftest import REPO_ROOT, iter_committed_files


# Case-insensitive substrings. Words like "MSC" need word-boundary handling
# because they can appear inside unrelated identifiers; we treat MSC separately.
BANNED_PATTERNS = [
    re.compile(r"marriott", re.IGNORECASE),
    re.compile(r"fujifilm", re.IGNORECASE),
    re.compile(r"sonosite", re.IGNORECASE),
    re.compile(r"bchydro", re.IGNORECASE),
    re.compile(r"bc.?hydro", re.IGNORECASE),
    re.compile(r"unilever", re.IGNORECASE),
    re.compile(r"manpowergroup", re.IGNORECASE),
    re.compile(r"\bMSC\b"),
]

# Files that legitimately contain the banned patterns *as patterns* for
# filtering or testing purposes. These are infrastructure, not content.
ALLOWLIST = {
    "tests/test_no_pii.py",
    "scripts/mirror_sync.py",
    "scripts/build_repo_pages.py",
}


def test_no_pii_in_committed_content():
    violations = []
    for p in iter_committed_files():
        rel = p.relative_to(REPO_ROOT).as_posix()
        if rel in ALLOWLIST:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pat in BANNED_PATTERNS:
            m = pat.search(text)
            if m:
                violations.append(f"{rel}: matched {pat.pattern!r} -> {m.group(0)!r}")
    assert not violations, "PII found in committed files:\n" + "\n".join(violations)
