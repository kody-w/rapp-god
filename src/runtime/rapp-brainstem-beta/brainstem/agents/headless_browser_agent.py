"""headless_browser_agent.py — give the brainstem a headless browser.

A drop-in cartridge: when the brainstem needs to look at a LIVE web page — one that
needs JavaScript, or just to fetch the rendered content / grab a screenshot — it calls
this agent. Uses Playwright + headless Chromium. No window ever appears.

Self-contained: the brainstem auto-installs the `playwright` pip package on load; this
agent installs the Chromium binary on first use if it's missing.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

try:
    from agents.basic_agent import BasicAgent
except ImportError:
    from basic_agent import BasicAgent

# Screenshots land in the brainstem's scratch area, never in the repo.
_SHOTS = Path(os.environ.get("BRAINSTEM_HOME", str(Path.home() / ".brainstem"))) / "browser"


def _run_in_browser(url, mode, wait_selector, max_chars):
    """Drive headless Chromium in a SUBPROCESS so there's never a Playwright/asyncio-loop
    conflict with the Flask host, and the browser is fully isolated. Returns (ok, payload)."""
    import json
    runner = r'''
import sys, json, time, pathlib
from playwright.sync_api import sync_playwright
a = json.loads(sys.argv[1])
def go(p):
    b = p.chromium.launch(headless=True)
    try:
        pg = b.new_page()
        pg.goto(a["url"], wait_until="domcontentloaded", timeout=30000)
        if a.get("wait_selector"):
            try: pg.wait_for_selector(a["wait_selector"], timeout=10000)
            except Exception: pass
        title = pg.title()
        m = a["mode"]
        if m == "html":
            out = pg.content()
        elif m == "links":
            links = pg.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
            out = "\n".join(dict.fromkeys(links))
        elif m == "screenshot":
            d = pathlib.Path(a["shots"]); d.mkdir(parents=True, exist_ok=True)
            fn = d / ("shot-%d.png" % int(time.time()))
            pg.screenshot(path=str(fn), full_page=True)
            out = "Screenshot saved: %s" % fn
        else:
            out = pg.inner_text("body")
        return title, out[: a["max_chars"]]
    finally:
        b.close()
with sync_playwright() as p:
    try:
        title, out = go(p)
    except Exception as e:
        # Chromium binary may be missing — install once, retry.
        if "Executable doesn't exist" in str(e) or "playwright install" in str(e):
            import subprocess
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], timeout=600)
            title, out = go(p)
        else:
            raise
print(json.dumps({"title": title, "out": out}))
'''
    args = {"url": url, "mode": mode, "wait_selector": wait_selector,
            "max_chars": max_chars, "shots": str(_SHOTS)}
    r = subprocess.run([sys.executable, "-c", runner, json.dumps(args)],
                       capture_output=True, text=True, timeout=90)
    if r.returncode != 0:
        return False, (r.stderr or r.stdout or "browser subprocess failed").strip()[-500:]
    try:
        d = json.loads(r.stdout.strip().splitlines()[-1])
        return True, d
    except Exception:
        return False, (r.stdout or "no output")[-500:]


class HeadlessBrowserAgent(BasicAgent):
    def __init__(self):
        self.name = "Headless Browser"
        self.metadata = {
            "name": self.name,
            "description": (
                "Browse the live web with a HEADLESS browser (full Chromium — runs JavaScript, "
                "no visible window). Use whenever you need the REAL, rendered content of a web page: "
                "read an article, a JS-rendered site, scrape its text or links, or capture a screenshot. "
                "Give a URL and say what you want back. Not for general questions — only when you need "
                "to actually open a page."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The page to open (http(s):// will be added if you omit the scheme).",
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["text", "html", "links", "screenshot"],
                        "description": (
                            "What to return. 'text' = the visible rendered text (default). "
                            "'html' = full HTML. 'links' = the page's links. "
                            "'screenshot' = save a PNG and return its file path."
                        ),
                    },
                    "wait_selector": {
                        "type": "string",
                        "description": "Optional CSS selector to wait for before reading (for slow/JS pages).",
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Cap on the returned content length (default 6000).",
                    },
                },
                "required": ["url"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def perform(self, **kwargs):
        url = (kwargs.get("url") or "").strip()
        if not url:
            return "Provide a 'url' to browse."
        if not url.startswith(("http://", "https://", "file://")):
            url = "https://" + url
        mode = (kwargs.get("mode") or "text").strip().lower()
        if mode not in ("text", "html", "links", "screenshot"):
            mode = "text"
        try:
            max_chars = int(kwargs.get("max_chars") or 6000)
        except (TypeError, ValueError):
            max_chars = 6000

        try:
            import playwright  # noqa: F401
        except ImportError:
            # Self-heal: install the pip package (the Chromium binary is installed on first
            # browse by the subprocess). Lazy here so loading the cartridge stays instant.
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", "playwright"], timeout=300)
            try:
                import importlib
                importlib.invalidate_caches()
                import playwright  # noqa: F401
            except ImportError:
                return ("Could not install Playwright automatically. Run: "
                        "pip install playwright && python -m playwright install chromium")

        ok, payload = _run_in_browser(url, mode, kwargs.get("wait_selector"), max_chars)
        if not ok:
            return f"Browse failed for {url}: {payload}"
        return f"[{payload.get('title', '')}] {url}\n\n{payload.get('out', '')}"
