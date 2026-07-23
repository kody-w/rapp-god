#!/usr/bin/env python3
"""rapp-brain-surgeon — the surgeon sidecar.

A SEPARATE Copilot conversation (the "surgeon") that operates ONLY on a RAPP
Brainstem's agents/*_agent.py cartridges, while the brainstem (the "patient")
stays awake and answering. The human is the LIAISON between the two: drive the
surgeon here, then test the patient ("now play the violin") in the brainstem
chat. This never goes through the brainstem's /chat — no snake eating its tail.

Powered by the GitHub Copilot SDK (`github-copilot-sdk`), which bundles the
Copilot CLI — so the only install is one `pip`.

THE GRAIL RULE: the surgeon physically cannot touch brainstem.py. The Copilot
session's working_directory is the agents/ dir, and a permission "grail-guard"
rejects any write outside agents/ or to brainstem.py. Two independent layers.
"""

import asyncio
import json
import os
from pathlib import Path

from aiohttp import web

import copilot.session_events as ev
from copilot import CopilotClient
from copilot.rpc import PermissionDecisionApproveOnce, PermissionDecisionReject

# ── Config ────────────────────────────────────────────────────────────────────
PORT = int(os.environ.get("SURGEON_PORT", "7072"))
AGENTS = os.path.realpath(
    os.environ.get("BRAINSTEM_AGENTS", os.path.expanduser("~/.brainstem/src/rapp_brainstem/agents"))
)
GRAIL = os.path.realpath(os.path.join(AGENTS, "..", "brainstem.py"))
HERE = Path(__file__).resolve().parent

# ── The grail-guard (proven: the surgeon cannot write brainstem.py) ───────────
def _safe_write(path: str) -> bool:
    if not path:
        return False
    p = os.path.realpath(path if os.path.isabs(path) else os.path.join(AGENTS, path))
    return p != GRAIL and (p == AGENTS or p.startswith(AGENTS + os.sep))


# ── Surgeon: wraps one Copilot session + fans events out to SSE subscribers ───
class Surgeon:
    def __init__(self):
        self.client: CopilotClient | None = None
        self.session = None
        self.subscribers: set[asyncio.Queue] = set()
        self.session_id: str | None = None
        self.sandboxed = False

    def _guard(self, request, invocation=None):
        """Permission handler — the grail-guard."""
        if isinstance(request, ev.PermissionRequestWrite):
            if _safe_write(request.file_name):
                return PermissionDecisionApproveOnce()
            self._emit({"type": "grail_blocked", "detail": f"write to {request.file_name}"})
            return PermissionDecisionReject(
                feedback="GRAIL RULE: writes are confined to agents/. brainstem.py and anything "
                "outside the agents/ sandbox are off-limits."
            )
        if isinstance(request, ev.PermissionRequestShell):
            text = request.full_command_text or ""
            if getattr(request, "has_write_file_redirection", False):
                paths = list(request.possible_paths or [])
                if (not paths) or any(not _safe_write(p) for p in paths) or "brainstem.py" in text:
                    self._emit({"type": "grail_blocked", "detail": f"shell write: {text[:80]}"})
                    return PermissionDecisionReject(
                        feedback="GRAIL RULE: a shell write must stay inside agents/ and never touch brainstem.py."
                    )
            return PermissionDecisionApproveOnce()
        # Reads, path-access, MCP, etc. are safe — only WRITES threaten the grail.
        return PermissionDecisionApproveOnce()

    def _emit(self, payload: dict):
        """Push an event to every connected pane (thread/loop-safe within the loop)."""
        for q in list(self.subscribers):
            try:
                q.put_nowait(payload)
            except Exception:
                pass

    def _on_event(self, event):
        d = getattr(event, "data", event)
        t = type(d).__name__
        if isinstance(d, (ev.AssistantStreamingDeltaData, ev.AssistantMessageDeltaData)):
            self._emit({"type": "delta", "content": getattr(d, "delta_content", "") or ""})
        elif isinstance(d, ev.AssistantMessageData):
            self._emit({"type": "assistant", "content": getattr(d, "content", "") or ""})
        elif isinstance(d, ev.ToolExecutionStartData):
            self._emit({"type": "tool", "phase": "start",
                        "name": getattr(getattr(d, "tool_description", None), "name", "") or t})
        elif isinstance(d, ev.ToolExecutionCompleteData):
            self._emit({"type": "tool", "phase": "done", "name": t})
        elif isinstance(d, ev.SessionWorkspaceFileChangedData):
            self._emit({"type": "file_changed", "detail": str(d)[:200]})
        elif isinstance(d, ev.SessionIdleData):
            self._emit({"type": "idle"})
        elif isinstance(d, ev.SessionErrorData):
            self._emit({"type": "error", "detail": str(d)[:300]})

    def _sandbox_env(self):
        """Build the OS confinement: an sandbox-exec profile that allows file-writes ONLY
        under agents/ (everything else in the brainstem — incl. brainstem.py — is denied),
        and the env that makes the SDK spawn the Copilot CLI through the sandbox wrapper.
        This is the grail guarantee: child shells inherit it, so there's no escape hatch.
        Returns (env, ok). ok=False if confinement can't be established (- refuse to operate)."""
        import copilot, tempfile
        real_cli = os.path.join(os.path.dirname(copilot.__file__), "bin", "copilot")
        wrapper = str(HERE / "sandbox" / "copilot-sandboxed.sh")
        if not (os.path.exists("/usr/bin/sandbox-exec") and os.path.exists(wrapper) and os.path.exists(real_cli)):
            return dict(os.environ), False
        src = os.path.realpath(os.path.join(AGENTS, ".."))
        prof = os.path.join(tempfile.gettempdir(), f"surgeon-{os.getpid()}.sb")
        with open(prof, "w") as f:
            f.write("(version 1)\n(allow default)\n"
                    f'(deny file-write* (subpath "{src}"))\n'
                    f'(allow file-write* (subpath "{os.path.realpath(AGENTS)}"))\n')
        env = dict(os.environ, COPILOT_CLI_PATH=wrapper, SURGEON_SBPROFILE=prof, SURGEON_REAL_CLI=real_cli)
        return env, True

    async def start(self):
        env, ok = self._sandbox_env()
        self.sandboxed = ok
        if not ok:
            # FAIL-SAFE: the grail guarantee depends on OS confinement. No sandbox - no surgery.
            raise RuntimeError(
                "Refusing to operate: OS confinement (macOS sandbox-exec) could not be established, "
                "so the grail (brainstem.py) can't be guaranteed safe. The surgeon only runs confined."
            )
        self.client = CopilotClient(working_directory=AGENTS, env=env)
        await self.client.start()
        await self._new_session()

    async def _new_session(self, resume_id: str | None = None):
        if resume_id:
            self.session = await self.client.resume_session(resume_id, on_permission_request=self._guard)
        else:
            self.session = await self.client.create_session(on_permission_request=self._guard)
        self.session.on(self._on_event)
        self.session_id = getattr(self.session, "session_id", None)
        self._emit({"type": "session", "session_id": self.session_id, "agents": AGENTS, "grail": GRAIL})

    async def send(self, prompt: str):
        if not self.session:
            await self._new_session()
        await self.session.send(prompt)

    async def resume(self, session_id: str):
        await self._new_session(resume_id=session_id)

    async def list_sessions(self):
        try:
            return await self.client.list_sessions()
        except Exception:
            return []

    async def stop(self):
        try:
            if self.session:
                await self.session.disconnect()
            if self.client:
                await self.client.stop()
        except Exception:
            pass


surgeon = Surgeon()


# ── HTTP / SSE ────────────────────────────────────────────────────────────────
async def index(_request):
    return web.FileResponse(HERE / "static" / "index.html")


async def overlay(_request):
    # The one-line injection target: <script src="http://localhost:7072/overlay.js">.
    return web.FileResponse(HERE / "static" / "overlay.js",
                            headers={"Content-Type": "application/javascript",
                                     "Access-Control-Allow-Origin": "*"})


async def health(_request):
    return web.json_response({"ok": True, "agents": AGENTS, "grail": GRAIL,
                              "sandboxed": surgeon.sandboxed, "session_id": surgeon.session_id})


async def send(request):
    body = await request.json()
    prompt = (body.get("prompt") or "").strip()
    if not prompt:
        return web.json_response({"error": "prompt required"}, status=400)
    await surgeon.send(prompt)
    return web.json_response({"ok": True})


async def resume(request):
    body = await request.json()
    sid = (body.get("session_id") or "").strip()
    if not sid:
        return web.json_response({"error": "session_id required"}, status=400)
    await surgeon.resume(sid)
    return web.json_response({"ok": True, "session_id": surgeon.session_id})


async def sessions(_request):
    rows = await surgeon.list_sessions()
    out = []
    for s in rows or []:
        out.append({
            "id": getattr(s, "session_id", getattr(s, "id", "")),
            "summary": getattr(s, "summary", getattr(s, "title", "")) or "",
            "cwd": getattr(s, "cwd", getattr(s, "working_directory", "")) or "",
        })
    return web.json_response({"sessions": out})


async def events(request):
    resp = web.StreamResponse(headers={
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": "*",
    })
    await resp.prepare(request)
    q: asyncio.Queue = asyncio.Queue()
    surgeon.subscribers.add(q)
    # greet with current session context
    await q.put({"type": "session", "session_id": surgeon.session_id, "agents": AGENTS, "grail": GRAIL})
    try:
        while True:
            payload = await q.get()
            await resp.write(f"data: {json.dumps(payload)}\n\n".encode())
    except (asyncio.CancelledError, ConnectionResetError):
        pass
    finally:
        surgeon.subscribers.discard(q)
    return resp


async def _on_startup(_app):
    await surgeon.start()


async def _on_cleanup(_app):
    await surgeon.stop()


def build_app():
    app = web.Application()
    app.router.add_get("/", index)
    app.router.add_get("/overlay.js", overlay)
    app.router.add_get("/health", health)
    app.router.add_get("/events", events)
    app.router.add_post("/send", send)
    app.router.add_post("/resume", resume)
    app.router.add_get("/sessions", sessions)
    app.router.add_static("/static/", HERE / "static")
    app.on_startup.append(_on_startup)
    app.on_cleanup.append(_on_cleanup)
    return app


if __name__ == "__main__":
    print(f"[surgeon] operating on: {AGENTS}")
    print(f"[surgeon] grail (off-limits): {GRAIL}")
    print(f"[surgeon] http://localhost:{PORT}")
    web.run_app(build_app(), host="127.0.0.1", port=PORT, print=None)
