"""Where the PII roster comes from — deliberately NOT from this repo.

This repo is PUBLIC. A redaction list of real customer names, committed here,
publishes the very roster it exists to suppress: the denylist becomes the
disclosure. So the terms live outside the tree and are injected at run time.

Sources, in order:
  1. $RAPP_PII_TERMS   -- comma-separated. In CI: ${{ secrets.PII_TERMS }}.
  2. ./.pii-terms      -- one term per line, gitignored, local only.

If neither is configured this module RAISES. That is the whole point: a
sanitiser that silently sanitises nothing, or a test that vacuously passes
because its banned-list is empty, is worse than having none at all -- it
reports "clean" while publishing everything. Fail closed, loudly.
"""

from __future__ import annotations

import os
from pathlib import Path


class PIIRosterNotConfigured(RuntimeError):
    """Raised when no roster is available. Never swallow this."""


_MESSAGE = (
    "No PII roster configured, so redaction would silently do nothing.\n"
    "  Set RAPP_PII_TERMS='term1,term2,...' (CI: ${{ secrets.PII_TERMS }})\n"
    "  or create an untracked ./.pii-terms with one term per line.\n"
    "Refusing to run with an empty roster (fail closed)."
)


def load_terms() -> list[str]:
    raw = os.environ.get("RAPP_PII_TERMS", "")
    terms = [t.strip() for t in raw.split(",") if t.strip()]
    if not terms:
        f = Path(__file__).resolve().parent.parent / ".pii-terms"
        if f.is_file():
            terms = [ln.strip() for ln in f.read_text().splitlines()
                     if ln.strip() and not ln.startswith("#")]
    if not terms:
        raise PIIRosterNotConfigured(_MESSAGE)
    return terms


def load_patterns(word_boundary: tuple[str, ...] = ()) -> list:
    """Compiled, case-insensitive. Terms in `word_boundary` are anchored with \\b
    so short tokens do not match inside unrelated words."""
    import re
    out = []
    for t in load_terms():
        body = re.escape(t)
        if t in word_boundary or t.isupper() and len(t) <= 4:
            body = r"\b" + body + r"\b"
        out.append(re.compile(body, re.IGNORECASE))
    return out
