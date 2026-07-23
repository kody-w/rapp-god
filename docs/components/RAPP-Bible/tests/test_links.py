"""Internal links resolve; external GitHub links point at real repos.

Strategy:
- Extract all markdown `[text](url)` links from every .md file.
- Relative links: assert the target file exists (resolve relative to the
  source file's directory). Anchors (#section) are stripped before
  checking. Pure anchor links are skipped.
- Absolute GitHub URLs of the form https://github.com/<owner>/<repo>(/...)?:
  call `gh api repos/<owner>/<repo>` and assert 200. Cache results per
  repo to avoid wasting API budget.
- All other external URLs are skipped (we don't try to crawl the web).

Allow up to 1 broken external GitHub link as a warning before failing.
"""

import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

from .conftest import REPO_ROOT, iter_committed_files


MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
GH_REPO = re.compile(r"^https?://github\.com/([^/]+)/([^/#?]+)")

_repo_cache: dict[tuple[str, str], bool] = {}


def gh_repo_exists(owner: str, repo: str) -> bool:
    key = (owner, repo)
    if key in _repo_cache:
        return _repo_cache[key]
    try:
        proc = subprocess.run(
            ["gh", "api", f"repos/{owner}/{repo}", "--silent"],
            capture_output=True, text=True, timeout=15,
        )
        ok = proc.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        ok = False
    _repo_cache[key] = ok
    return ok


def _strip_anchor(url: str) -> str:
    return url.split("#", 1)[0]


# Mirrored content (verbatim from upstream) and auto-extracted README
# summaries can contain relative links that refer to files in the *upstream*
# repo, not the Bible. We exempt those directories from the internal-link
# check — upstream owns its own link hygiene.
NATIVE_CONTENT_DIRS = {".", "quickstart", "tests", "scripts", ".github"}


def _is_native(rel: str) -> bool:
    head = rel.split("/", 1)[0]
    return head in NATIVE_CONTENT_DIRS or "/" not in rel


def test_internal_links_resolve():
    """Native Bible content (README, quickstart, SPEC/_index.md, repos/_index.md)
    must have all internal links resolve. Mirrored content (SPEC/<area>/*.md)
    and auto-generated per-repo pages (repos/<name>.md, which embed upstream
    README excerpts) are exempt — upstream owns link hygiene.
    """
    # Files that must have clean internal links
    NATIVE_FILES = {
        "README.md",
        "CONTRIBUTING.md",
        "SPEC/_index.md",
        "repos/_index.md",
    }
    broken_internal: list[str] = []
    for p in iter_committed_files():
        if p.suffix.lower() != ".md":
            continue
        rel = p.relative_to(REPO_ROOT).as_posix()
        is_quickstart = rel.startswith("quickstart/")
        if rel not in NATIVE_FILES and not is_quickstart:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in MD_LINK.finditer(text):
            url = m.group(1).strip()
            if not url or url.startswith("#"):
                continue
            scheme = urlsplit(url).scheme
            if scheme in ("http", "https", "mailto", "tel"):
                continue
            target = _strip_anchor(url)
            if not target:
                continue
            resolved = (p.parent / target).resolve()
            if not resolved.exists():
                broken_internal.append(f"{rel}: -> {url} (resolved: {resolved})")
    assert not broken_internal, "Broken internal links:\n" + "\n".join(broken_internal)


def test_external_github_repo_links_resolve():
    """External GitHub repo links in *native Bible content* must resolve.

    Mirrored upstream specs (under SPEC/) are exempt — they can legitimately
    reference private or yet-to-be-created upstream repos. Auto-generated
    repo pages (repos/<name>.md) are also exempt because they embed first-
    paragraph excerpts from upstream READMEs.
    """
    NATIVE_DIRS_FOR_EXTERNAL = {"quickstart"}
    NATIVE_FILES_FOR_EXTERNAL = {"README.md", "CONTRIBUTING.md", "index.html",
                                  "SPEC/_index.md", "repos/_index.md"}
    broken: list[str] = []
    for p in iter_committed_files():
        if p.suffix.lower() not in (".md", ".html"):
            continue
        rel = p.relative_to(REPO_ROOT).as_posix()
        head = rel.split("/", 1)[0]
        if rel not in NATIVE_FILES_FOR_EXTERNAL and head not in NATIVE_DIRS_FOR_EXTERNAL:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # Extract URLs from both markdown links and bare href= attributes.
        urls: set[str] = set()
        for m in MD_LINK.finditer(text):
            urls.add(m.group(1).strip())
        # Bare GitHub URLs (no markdown wrapper)
        for m in re.finditer(r"https?://github\.com/[^\s)\"<>]+", text):
            urls.add(m.group(0))
        for url in urls:
            mm = GH_REPO.match(url)
            if not mm:
                continue
            owner = mm.group(1)
            repo = mm.group(2)
            # Strip common URL suffixes (.git for clone URLs, trailing punctuation)
            for suffix in (".git", ".", ","):
                if repo.endswith(suffix):
                    repo = repo[: -len(suffix)]
            # GitHub-internal paths that aren't actual repos
            if owner in ("user-attachments", "actions", "marketplace"):
                continue
            # Skip if it's referencing the Bible itself
            if (owner, repo) == ("kody-w", "RAPP-Bible"):
                continue
            if not gh_repo_exists(owner, repo):
                broken.append(f"{rel}: {url} -> repos/{owner}/{repo} not found")

    # Allow up to 1 broken external link as a warning.
    if 0 < len(broken) <= 1:
        print(f"WARNING: 1 broken external link tolerated:\n{broken[0]}")
        return
    assert not broken, "Broken external GitHub repo links:\n" + "\n".join(broken)
