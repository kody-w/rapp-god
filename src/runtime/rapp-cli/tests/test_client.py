from __future__ import annotations

import hashlib
import json
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

import rapp_cli.client as client_module
from rapp_cli.client import BrainstemClient
from rapp_cli.config import Config
from rapp_cli.errors import AuthenticationFailure, RemoteFailure, UsageError


class Handler(BaseHTTPRequestHandler):
    requests: list[dict[str, object]] = []

    def log_message(self, _format, *_args):
        return

    def do_GET(self):
        Handler.requests.append(
            {
                "method": "GET",
                "path": self.path,
                "secret": self.headers.get("X-Brainstem-Secret"),
            }
        )
        if self.path == "/denied":
            self._json(403, {"error": "forbidden"})
            return
        if self.path == "/conflict":
            self._json(409, {"error": "conflict"})
            return
        if self.path == "/invalid":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"not-json")
            return
        if self.path == "/duplicate":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status":"ok","status":"error"}')
            return
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "/health")
            self.end_headers()
            return
        if self.path == "/oversized":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"x" * (4 * 1024 * 1024 + 1))
            return
        self._json(200, {"status": "ok"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        content_type = self.headers.get("Content-Type", "")
        Handler.requests.append(
            {
                "method": "POST",
                "path": self.path,
                "body": json.loads(body) if content_type == "application/json" else body,
                "content_type": content_type,
            }
        )
        if self.path == "/chat/stream":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            self.wfile.write(b": heartbeat\r\n")
            self.wfile.write(b"event: chunk\r\n")
            self.wfile.write(b'data: {"content":\r\n')
            self.wfile.write(b'data: "hello"}\r\n\r\n')
            self.wfile.write(b"data: done\n\n")
            return
        if self.path == "/chat/bad-stream":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            self.wfile.write(b"data: \xff\n\n")
            return
        if self.path == "/chat/empty-data":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            self.wfile.write(b"data:\ndata:\ndata:\n\n")
            return
        self._json(200, {"response": "hello"})

    def _json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@contextmanager
def server():
    Handler.requests = []
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_port}"
    finally:
        httpd.shutdown()
        thread.join(timeout=5)
        httpd.server_close()


def make_client(url, *, secret=None):
    return BrainstemClient(
        Config(
            brainstem_url=url,
            timeout=2,
            secret=secret,
            config_path=None,
        )
    )


def test_json_requests_and_secret_header():
    with server() as url:
        client = make_client(url, secret="secret")
        assert client.get_json("/health") == {"status": "ok"}
        assert client.post_json("/chat", {"user_input": "hi"}) == {"response": "hello"}

    assert Handler.requests[0]["secret"] == "secret"
    assert Handler.requests[1]["body"] == {"user_input": "hi"}


def test_http_auth_error_is_typed():
    with server() as url, pytest.raises(AuthenticationFailure, match="forbidden"):
        make_client(url).get_json("/denied")


def test_http_conflict_is_typed():
    from rapp_cli.errors import Conflict

    with server() as url, pytest.raises(Conflict, match="conflict"):
        make_client(url).get_json("/conflict")


def test_invalid_json_is_typed():
    with server() as url, pytest.raises(RemoteFailure, match="invalid JSON"):
        make_client(url).get_json("/invalid")


def test_duplicate_json_keys_are_rejected():
    with server() as url, pytest.raises(RemoteFailure, match="invalid JSON"):
        make_client(url).get_json("/duplicate")


def test_redirects_are_not_followed():
    with server() as url, pytest.raises(RemoteFailure):
        make_client(url).get_json("/redirect")

    assert [request["path"] for request in Handler.requests] == ["/redirect"]


def test_oversized_response_is_rejected():
    with server() as url, pytest.raises(RemoteFailure, match="allowed size"):
        make_client(url).get_json("/oversized")


def test_sse_stream_is_parsed():
    with server() as url:
        events = list(make_client(url).stream_events("/chat/stream", {"user_input": "hi"}))

    assert events == [
        {"event": "chunk", "id": None, "data": {"content": "hello"}},
        {"event": "message", "id": None, "data": "done"},
    ]


def test_sse_requires_event_stream_content_type():
    with server() as url, pytest.raises(RemoteFailure, match="text/event-stream"):
        list(make_client(url).stream_events("/chat", {"user_input": "hi"}))


def test_sse_rejects_invalid_utf8():
    with server() as url, pytest.raises(RemoteFailure, match="invalid UTF-8"):
        list(make_client(url).stream_events("/chat/bad-stream", {"user_input": "hi"}))


def test_sse_empty_data_lines_count_toward_event_limit(monkeypatch):
    monkeypatch.setattr(client_module, "_MAX_SSE_EVENT_BYTES", 10)

    with server() as url, pytest.raises(RemoteFailure, match="oversized event"):
        list(make_client(url).stream_events("/chat/empty-data", {"user_input": "hi"}))


def test_agent_import_is_multipart(tmp_path):
    source = tmp_path / "hello_agent.py"
    source.write_text("print('hello')\n", encoding="utf-8")

    with server() as url:
        response = make_client(url).import_agent(
            source.name,
            source.read_bytes(),
            sha256="a" * 64,
        )

    request = Handler.requests[-1]
    assert response == {"response": "hello"}
    assert str(request["content_type"]).startswith("multipart/form-data; boundary=")
    assert b'filename="hello_agent.py"' in request["body"]
    assert b"a" * 64 in request["body"]


def test_oversized_json_request_is_rejected_before_network():
    with server() as url, pytest.raises(UsageError, match="1 MiB"):
        make_client(url).post_json("/chat", {"user_input": "x" * (1024 * 1024)})

    assert Handler.requests == []


def test_exactly_16_mib_agent_payload_is_rejected_for_multipart_overhead(monkeypatch):
    requests = []
    client = make_client("http://127.0.0.1:1")
    monkeypatch.setattr(client_module.secrets, "token_hex", lambda _length: "0" * 32)
    monkeypatch.setattr(
        client,
        "request",
        lambda *args, **kwargs: requests.append((args, kwargs)),
    )

    with pytest.raises(UsageError, match="16 MiB"):
        client.import_agent(
            "large_agent.py",
            b"x" * (16 * 1024 * 1024),
            sha256=hashlib.sha256(b"x").hexdigest(),
        )

    assert requests == []


def test_largest_agent_payload_accounts_for_exact_multipart_overhead(monkeypatch):
    requests = []
    client = make_client("http://127.0.0.1:1")
    monkeypatch.setattr(client_module.secrets, "token_hex", lambda _length: "0" * 32)

    def capture_request(method, path, **kwargs):
        requests.append((method, path, kwargs))
        return client_module.Response(status=200, headers={}, body=b"{}")

    monkeypatch.setattr(client, "request", capture_request)
    monkeypatch.setattr(client_module, "_MAX_AGENT_BYTES", 1024 * 1024)
    client.import_agent(
        "boundary_agent.py",
        b"",
        sha256="a" * 64,
        source_revision="revision",
    )
    overhead = len(requests[-1][2]["body"])
    requests.clear()

    accepted_payload = b"x" * 32
    monkeypatch.setattr(
        client_module,
        "_MAX_AGENT_BYTES",
        overhead + len(accepted_payload),
    )
    client.import_agent(
        "boundary_agent.py",
        accepted_payload,
        sha256="a" * 64,
        source_revision="revision",
    )

    assert len(requests[-1][2]["body"]) == overhead + len(accepted_payload)
    with pytest.raises(UsageError, match="complete agent multipart request"):
        client.import_agent(
            "boundary_agent.py",
            accepted_payload + b"x",
            sha256="a" * 64,
            source_revision="revision",
        )
    assert len(requests) == 1
