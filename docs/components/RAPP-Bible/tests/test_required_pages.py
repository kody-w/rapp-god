"""Required pages exist and are non-trivial."""

from pathlib import Path

from .conftest import REPO_ROOT


REQUIRED = [
    "README.md",
    "index.html",
    "SPEC/_index.md",
    "repos/_index.md",
    "CONTRIBUTING.md",
    "LICENSE",
]


def test_required_pages_exist_and_nontrivial():
    for rel in REQUIRED:
        p = REPO_ROOT / rel
        assert p.exists(), f"missing required file: {rel}"
        size = p.stat().st_size
        assert size > 200, f"{rel} is too small ({size} bytes)"
