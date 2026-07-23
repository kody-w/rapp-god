"""se_dashboard_render_agent — the Workflow Toolkit rapplication renderer.

The rapplication's UI is hydrated DETERMINISTICALLY: this agent calls
the other BWAT agents directly with static inputs (no LLM in the loop,
no follow-up questions), assembles their JSON outputs into a self-
contained HTML dashboard, writes it to disk, and returns the file path.

The SE opens the file in their browser. Re-running this agent
re-renders the page; refresh the browser tab to see updated state.

The rapplication directory in the neighborhood is:
    rapplications/workflow-dashboard/
        ├── app.json         ← rapplication metadata
        ├── rappid.json      ← variant rappid
        ├── README.md        ← "run DashboardRender to hydrate"
        └── (the rendered HTML is written to ~/.bwat-data/<handle>/
             workflow-dashboard.html — local-only, never in the repo)

Hydration sources (all called with static inputs, no LLM):
  ProjectPinger.perform(action='team_status')   → cross-team view
  ProjectPinger.perform(action='status')        → personal portfolio
  ProjectPinger.perform(action='find_blockers') → personal blockers
  ProjectPinger.perform(action='team_blockers') → team blockers
  Twin.perform(action='next_move')                  → the owner's nudge
  Pm.perform(action='status_report', lookback_days=7) → activity report

Lives in the this neighborhood's rar — installed automatically when
an operator joins.
"""

from __future__ import annotations

import importlib
import json
import os
import subprocess
from datetime import datetime, timezone

try:
    from agents.basic_agent import BasicAgent
except ImportError:
    from basic_agent import BasicAgent


def _now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _gh_handle() -> str | None:
    try:
        p = subprocess.run(
            ["gh", "api", "user", "--jq", ".login"],
            capture_output=True, text=True,
        )
        if p.returncode == 0 and p.stdout.strip():
            return p.stdout.strip()
    except Exception:
        pass
    return None


def _local_data_root(handle: str) -> str:
    base = os.path.expanduser(
        os.environ.get("NB_DATA_HOME", "~/.brainstem/neighborhoods/__SLUG__")
    )
    return os.path.join(base, handle)


def _load_agent(class_name: str, module_hint: str):
    try:
        mod = importlib.import_module(module_hint)
        return getattr(mod, class_name, None)
    except Exception:
        return None


def _call(class_name: str, module_hint: str, **kwargs) -> dict:
    """Call a sibling agent with static inputs; return parsed JSON dict."""
    cls = _load_agent(class_name, module_hint)
    if cls is None:
        return {"ok": False, "error": f"{class_name} not loaded; run Joiner."}
    try:
        raw = cls().perform(**kwargs)
        return json.loads(raw) if isinstance(raw, str) else raw
    except Exception as e:
        return {"ok": False, "error": f"{class_name}.perform failed: {e}"}


def _render_html(handle: str, data: dict) -> str:
    """Pure-Python HTML render. Self-contained. No external CSS/JS."""
    ts = data["rendered_at"]
    team = data["team_status"]
    personal = data["personal_status"]
    blockers = data["personal_blockers"]
    team_blockers = data["team_blockers"]
    nudge = data["bill_nudge"]
    pm_report = data["pm_report"]

    def esc(s):
        s = "" if s is None else str(s)
        return (s.replace("&", "&amp;").replace("<", "&lt;")
                 .replace(">", "&gt;").replace('"', "&quot;"))

    def panel(title, body_html, subtitle=""):
        sub = f'<div class="sub">{esc(subtitle)}</div>' if subtitle else ""
        return (
            f'<section class="panel">'
            f'<header><h2>{esc(title)}</h2>{sub}</header>'
            f'<div class="body">{body_html}</div>'
            f'</section>'
        )

    # ─ team status ─
    team_body = ""
    if team.get("ok"):
        per_se = team.get("per_se") or []
        if per_se:
            rows = "".join(
                f'<tr><td><b>{esc(s["se"])}</b></td>'
                f'<td>{s["project_count"]}</td>'
                f'<td>{esc(", ".join(f"{k}:{v}" for k,v in s.get("by_status", {}).items()) or "—")}</td></tr>'
                for s in per_se
            )
            team_body = (
                f'<table><thead><tr><th>SE</th><th># projects</th>'
                f'<th>By status</th></tr></thead><tbody>{rows}</tbody></table>'
            )
        else:
            team_body = '<p class="empty">No SEs have minted front doors yet.</p>'
    else:
        team_body = f'<p class="error">{esc(team.get("error", "unknown error"))}</p>'

    # ─ personal portfolio ─
    personal_body = ""
    if personal.get("ok"):
        projects = personal.get("projects") or []
        if projects:
            cards = "".join(
                f'<div class="card status-{esc((p.get("status") or "unknown").replace(" ", "-"))}">'
                f'<div class="slug">{esc(p["slug"])}</div>'
                f'<div class="meta">'
                f'  <span class="badge">{esc(p.get("status") or "unknown")}</span>'
                f'  <span class="touched">{esc((p.get("last_touched") or "")[:10])}</span>'
                f'</div>'
                + (f'<div class="blockers">⚠ {esc(", ".join(p["blockers"]) if isinstance(p.get("blockers"), list) else p["blockers"])}</div>' if p.get("blockers") else "")
                + '</div>'
                for p in projects
            )
            personal_body = f'<div class="cards">{cards}</div>'
        else:
            personal_body = (
                '<p class="empty">No customer projects yet. '
                'Run <code>EngagementFactory</code> to start one.</p>'
            )
    else:
        personal_body = f'<p class="error">{esc(personal.get("error", "unknown error"))}</p>'

    # ─ blockers ─
    blockers_body = ""
    if blockers.get("ok"):
        items = blockers.get("blocked") or []
        if items:
            rows = "".join(
                f'<li><b>{esc(b["slug"])}</b>: {esc(", ".join(b["blockers"]) if isinstance(b.get("blockers"), list) else b["blockers"])}</li>'
                for b in items
            )
            blockers_body = f'<ul>{rows}</ul>'
        else:
            blockers_body = '<p class="empty">No personal blockers.</p>'
    else:
        blockers_body = f'<p class="error">{esc(blockers.get("error", ""))}</p>'

    # ─ team blockers ─
    team_blockers_body = ""
    if team_blockers.get("ok"):
        items = team_blockers.get("blocked") or []
        if items:
            rows = "".join(
                f'<li><b>{esc(b["se"])}/{esc(b["slug"])}</b>: '
                f'{esc(", ".join(b["blockers"]) if isinstance(b.get("blockers"), list) else b["blockers"])}</li>'
                for b in items
            )
            team_blockers_body = f'<ul>{rows}</ul>'
        else:
            team_blockers_body = '<p class="empty">No team blockers.</p>'
    else:
        team_blockers_body = f'<p class="error">{esc(team_blockers.get("error", ""))}</p>'

    # ─ the owner's nudge ─
    nudge_body = (
        f'<blockquote class="bill">{esc(nudge.get("next_move") or "—")}</blockquote>'
        f'<p class="sub">backlog: {nudge.get("backlog_size", 0)} items</p>'
        if nudge.get("ok") else
        f'<p class="error">{esc(nudge.get("error", ""))}</p>'
    )

    # ─ PM activity ─
    pm_body = ""
    if pm_report.get("ok"):
        md = pm_report.get("report_markdown") or ""
        # cheap markdown → html (just bullets + headers, our format)
        html_lines = []
        for line in md.split("\n"):
            line = esc(line)
            if line.startswith("## "):
                html_lines.append(f"<h3>{line[3:]}</h3>")
            elif line.startswith("### "):
                html_lines.append(f"<h4>{line[4:]}</h4>")
            elif line.startswith("- "):
                html_lines.append(f"<li>{line[2:]}</li>")
            elif line.strip():
                html_lines.append(f"<p>{line}</p>")
        pm_body = (
            "<ul>" + "".join(l for l in html_lines if l.startswith("<li>")) + "</ul>"
            if any(l.startswith("<li>") for l in html_lines) else
            "".join(html_lines)
        )
    else:
        pm_body = f'<p class="error">{esc(pm_report.get("error", ""))}</p>'

    style = """
:root {
  color-scheme: light dark;
  --bg: #0d1117; --fg: #e6edf3; --muted: #7d8590;
  --accent: #ffd866; --panel: #161b22; --bord: rgba(255,255,255,0.08);
  --ok: #56d364; --warn: #f97583; --info: #79c0ff;
}
@media (prefers-color-scheme: light) {
  :root { --bg: #ffffff; --fg: #1f2328; --muted: #59636e;
          --accent: #b8860b; --panel: #f6f8fa; --bord: rgba(0,0,0,0.08); }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--fg);
       font-family: -apple-system, system-ui, Segoe UI, sans-serif;
       padding: 24px; line-height: 1.5; }
h1 { margin: 0 0 4px; font-size: 1.6rem; }
.lede { color: var(--muted); margin: 0 0 24px; font-size: 0.9rem; }
.lede b { color: var(--fg); }
.grid { display: grid; gap: 16px; grid-template-columns: 1fr 1fr; }
@media (max-width: 800px) { .grid { grid-template-columns: 1fr; } }
.panel { background: var(--panel); border: 1px solid var(--bord);
         border-radius: 10px; padding: 16px 18px; }
.panel header { margin-bottom: 12px; border-bottom: 1px solid var(--bord);
                padding-bottom: 8px; }
.panel h2 { margin: 0; font-size: 1rem; }
.panel .sub { color: var(--muted); font-size: 0.78rem; margin-top: 2px; }
.panel.full { grid-column: 1 / -1; }
table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--bord); }
th { color: var(--muted); font-weight: 500; font-size: 0.75rem; text-transform: uppercase; }
.cards { display: grid; gap: 10px; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); }
.card { background: rgba(255,255,255,0.03); border: 1px solid var(--bord);
        border-left: 3px solid var(--info);
        border-radius: 6px; padding: 10px 12px; font-size: 0.85rem; }
.card.status-active { border-left-color: var(--ok); }
.card.status-blocked { border-left-color: var(--warn); }
.card.status-shipped { border-left-color: var(--accent); }
.card .slug { font-weight: 600; font-family: ui-monospace, monospace; }
.card .meta { display: flex; justify-content: space-between; align-items: center;
              margin-top: 6px; font-size: 0.72rem; }
.badge { background: rgba(255,255,255,0.08); padding: 1px 7px; border-radius: 999px; }
.touched { color: var(--muted); font-family: ui-monospace, monospace; }
.blockers { margin-top: 6px; color: var(--warn); font-size: 0.78rem; }
.empty { color: var(--muted); font-style: italic; }
.error { color: var(--warn); }
ul { padding-left: 20px; margin: 4px 0; }
li { margin: 3px 0; font-size: 0.85rem; }
blockquote.bill { margin: 0; padding: 12px 14px; background: rgba(255,216,102,0.08);
                  border-left: 3px solid var(--accent); border-radius: 4px;
                  font-style: italic; }
code { background: rgba(255,255,255,0.06); padding: 1px 5px; border-radius: 3px;
       font-size: 0.85em; }
footer { color: var(--muted); font-size: 0.72rem; margin-top: 24px;
         text-align: center; }
"""

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<title>Workflow Toolkit — {esc(handle)}</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>{style}</style>
</head><body>
<h1>🛠 Workflow Toolkit — {esc(handle)}</h1>
<p class="lede">BWAT dashboard. Hydrated <b>{esc(ts)}</b> from your local
brainstem agents — no LLM round-trip. Re-run
<code>DashboardRender</code> and refresh this tab to update.</p>

<div class="grid">
  {panel("👤 Your portfolio", personal_body,
         f'{personal.get("total_projects", 0)} project(s) at {esc(personal.get("local_data_dir", ""))}')}
  {panel("🌐 Team status", team_body,
         f'{team.get("ses_count", 0)} SE(s) with front doors in this neighborhood')}
  {panel("💬 Bill says", nudge_body)}
  {panel("⚠ Your blockers", blockers_body,
         f'{blockers.get("blocked_count", 0)} item(s)')}
  {panel("⚠ Team blockers", team_blockers_body,
         f'{team_blockers.get("blocked_count", 0)} item(s) across the team')}
  {panel("📋 Activity (last 7 days)", pm_body, '', )}
</div>

<footer>
Generated by <code>DashboardRender</code> · this neighborhood ·
data lives at <code>~/.bwat-data/{esc(handle)}/</code> (local only)
</footer>
</body></html>
"""


class DashboardRenderAgent(BasicAgent):
    metadata = {
        "name": "DashboardRender",
        "description": (
            "Renders the Workflow Toolkit rapplication dashboard. Calls the "
            "BWAT agents (ProjectPinger, Twin, Pm) "
            "directly with static inputs — no LLM round-trip, no "
            "follow-up questions, fully deterministic. Writes a "
            "self-contained HTML file to ~/.bwat-data/<handle>/"
            "workflow-dashboard.html and returns the path. Open that file in "
            "a browser. Re-run + refresh to update."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "handle": {
                    "type": "string",
                    "description": "Override auto-detected GitHub handle.",
                },
            },
            "required": [],
        },
    }

    def __init__(self):
        self.name = "DashboardRender"

    def perform(self, **kwargs) -> str:
        handle = (kwargs.get("handle") or "").strip() or _gh_handle()
        if not handle:
            return json.dumps({
                "ok": False,
                "error": (
                    "Couldn't detect handle. Pass handle='your-github-username' "
                    "or run `gh auth login`."
                ),
            })

        # Static-input agent calls — no LLM in the loop.
        data = {
            "handle": handle,
            "rendered_at": _now_iso(),
            "team_status": _call(
                "ProjectPingerAgent",
                "agents.customer_project_pinger_agent",
                action="team_status"),
            "personal_status": _call(
                "ProjectPingerAgent",
                "agents.customer_project_pinger_agent",
                action="status", handle=handle),
            "personal_blockers": _call(
                "ProjectPingerAgent",
                "agents.customer_project_pinger_agent",
                action="find_blockers", handle=handle),
            "team_blockers": _call(
                "ProjectPingerAgent",
                "agents.customer_project_pinger_agent",
                action="team_blockers"),
            "bill_nudge": _call(
                "TwinAgent", "agents.bill_twin_agent",
                action="next_move"),
            "pm_report": _call(
                "PmAgent", "agents.bwat_pm_agent",
                action="status_report", lookback_days=7),
        }

        # Render + write to disk.
        html = _render_html(handle, data)
        out_dir = _local_data_root(handle)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "workflow-dashboard.html")
        with open(out_path, "w") as f:
            f.write(html)

        return json.dumps({
            "schema": "dashboard-render-result/1.0",
            "ok": True,
            "handle": handle,
            "rendered_at": data["rendered_at"],
            "html_path": out_path,
            "html_size_bytes": len(html),
            "open_in_browser": f"file://{out_path}",
            "panels": list(data.keys()),
            "next_step": (
                f"Open file://{out_path} in your browser. Re-run this "
                f"agent and refresh the tab to update. The HTML is "
                f"self-contained — no internet needed once rendered."
            ),
        }, indent=2)
