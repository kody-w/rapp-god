"""index.html parses as valid HTML and contains the repo + spec lists."""

import html.parser

from .conftest import REPO_ROOT


class _Collector(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags: list[str] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)

    def error(self, message):
        # Older Python versions; current html.parser uses stricter behavior
        self.errors.append(message)


def test_index_html_parses_and_has_content():
    path = REPO_ROOT / "index.html"
    text = path.read_text(encoding="utf-8")
    parser = _Collector()
    parser.feed(text)
    parser.close()

    assert not parser.errors, f"html parse errors: {parser.errors}"
    # Basic structure
    for required_tag in ("html", "head", "body", "title", "main"):
        assert required_tag in parser.tags, f"missing <{required_tag}>"
    # Content: must reference the SPEC index and at least one core repo
    assert "SPEC/_index.md" in text
    assert "repos/_index.md" in text
    # Must reference every Tier-1 repo page
    for repo in ("RAPP.md", "RAPP-Network.md", "RAPP_Store.md",
                 "RAR.md", "RAPP_Sense_Store.md", "rapp-installer.md",
                 "rapp-mcp.md"):
        assert f"repos/{repo}" in text, f"index.html missing link to repos/{repo}"
