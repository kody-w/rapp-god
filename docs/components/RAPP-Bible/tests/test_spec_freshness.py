"""Mirrored specs match (after PII sanitization) what upstream serves.

This test is informational on first commit and uses an allowlist for known
drift sources. Specifically: the sanitization filter in
scripts/mirror_sync.py rewrites customer names, so any spec that contained
such a name upstream will legitimately differ from raw upstream HEAD.

Pass criterion: every mirrored file either matches upstream byte-for-byte
(after sanitization is re-applied), or its drift is purely the result of
PII sanitization.
"""

import hashlib
import sys
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from .conftest import REPO_ROOT

# Import the sync module to reuse the sanitize_pii function.
sys.path.insert(0, str(REPO_ROOT))
from scripts.mirror_sync import MIRRORS, sanitize_pii, RAW_URL, strip_provenance  # noqa: E402


def _fetch(url: str) -> bytes | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "rapp-bible-test/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            if resp.status != 200:
                return None
            return resp.read()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        return None


@pytest.mark.parametrize("repo,upstream_path,dest_rel", MIRRORS)
def test_mirrored_spec_matches_sanitized_upstream(repo, upstream_path, dest_rel):
    url = RAW_URL.format(repo=repo, path=upstream_path)
    raw = _fetch(url)
    if raw is None:
        pytest.skip(f"upstream unreachable: {url}")

    upstream_sanitized = sanitize_pii(raw.decode("utf-8", errors="replace"))
    upstream_sha = hashlib.sha256(upstream_sanitized.encode("utf-8")).hexdigest()

    local_path = REPO_ROOT / dest_rel
    assert local_path.exists(), f"mirrored spec missing: {dest_rel}"
    local_text = strip_provenance(local_path.read_text(encoding="utf-8"))
    local_sha = hashlib.sha256(local_text.encode("utf-8")).hexdigest()

    assert local_sha == upstream_sha, (
        f"drift in {dest_rel}: local={local_sha[:12]} upstream={upstream_sha[:12]}. "
        f"Re-run `python3 scripts/mirror_sync.py` to refresh."
    )
