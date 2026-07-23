#!/usr/bin/env python3
"""Test the headless browser agent. The key assertion: it RENDERS JavaScript (proving it's
a real headless Chromium, not a static fetch). Local file:// pages keep it deterministic.
"""
import importlib.util
import os
import pathlib
import re
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parent.parent
AGENT = REPO / "brainstem" / "agents" / "headless_browser_agent.py"


def _load():
    sys.path.insert(0, str(REPO / "brainstem" / "agents"))  # so `from basic_agent import BasicAgent` resolves
    spec = importlib.util.spec_from_file_location("hba", AGENT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.HeadlessBrowserAgent()


def _page(html):
    f = tempfile.NamedTemporaryFile("w", suffix=".html", delete=False)
    f.write(html)
    f.close()
    return "file://" + f.name


def test_metadata():
    t = _load().to_tool()
    assert t["function"]["parameters"]["required"] == ["url"]
    assert "headless" in t["function"]["description"].lower()
    print("PASS: metadata")


def test_js_rendering():
    a = _load()
    # the visible text ONLY exists after JavaScript runs — a static fetch would miss it
    url = _page('<html><body>STATIC<script>document.body.innerHTML="JS_RENDERED_OK "+(1+1);</script></body></html>')
    res = a.perform(url=url, mode="text")
    print("text:", res[:160].replace("\n", " "))
    assert "JS_RENDERED_OK 2" in res, f"JS not rendered — not a real browser: {res[:300]}"
    print("PASS: real browser renders JS")


def test_links():
    a = _load()
    url = _page('<html><body><a href="https://example.com/a">A</a><a href="https://example.com/b">B</a></body></html>')
    res = a.perform(url=url, mode="links")
    assert "example.com/a" in res and "example.com/b" in res, res[:300]
    print("PASS: links extracted")


def test_screenshot():
    a = _load()
    url = _page('<html><body style="background:#fff"><h1>shot</h1></body></html>')
    res = a.perform(url=url, mode="screenshot")
    m = re.search(r"Screenshot saved: (\S+\.png)", res)
    assert m and os.path.exists(m.group(1)), f"no screenshot: {res[:300]}"
    print("PASS: screenshot saved ->", m.group(1))


def test_bad_url_graceful():
    a = _load()
    res = a.perform(url="http://127.0.0.1:1/nope")
    assert "failed" in res.lower() or "err" in res.lower(), res[:200]
    print("PASS: bad url handled gracefully")


if __name__ == "__main__":
    test_metadata()
    test_js_rendering()
    test_links()
    test_screenshot()
    test_bad_url_graceful()
    print("\nALL BROWSER TESTS PASSED")
