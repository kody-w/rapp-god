from __future__ import annotations

import json
import re
import secrets
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .agent_files import MAX_AGENT_BYTES, validate_agent_filename
from .config import Config
from .errors import (
    AuthenticationFailure,
    Conflict,
    ConnectionFailure,
    NotFound,
    RemoteFailure,
    UsageError,
)
from .jsonio import DuplicateKeyError, NonFiniteNumberError, loads

_MAX_SSE_LINE_BYTES = 1024 * 1024
_MAX_SSE_EVENT_BYTES = 4 * 1024 * 1024
_MAX_JSON_BYTES = 4 * 1024 * 1024
_MAX_AGENT_BYTES = MAX_AGENT_BYTES
_MAX_ERROR_BYTES = 64 * 1024
_MAX_JSON_REQUEST_BYTES = 1024 * 1024


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@dataclass(frozen=True, slots=True)
class Response:
    status: int
    headers: Mapping[str, str]
    body: bytes

    def json(self) -> Any:
        if not self.body:
            return None
        try:
            return loads(self.body.decode("utf-8"))
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
            DuplicateKeyError,
            NonFiniteNumberError,
        ) as exc:
            raise RemoteFailure(
                "remote endpoint returned an invalid JSON response",
                details={"status": self.status},
            ) from exc


class BrainstemClient:
    def __init__(self, config: Config, *, service_name: str = "Brainstem") -> None:
        self.config = config
        self.service_name = service_name
        self._opener = build_opener(_NoRedirect)

    def request(
        self,
        method: str,
        path: str,
        *,
        payload: Any | None = None,
        headers: Mapping[str, str] | None = None,
        body: bytes | None = None,
        max_bytes: int = _MAX_JSON_BYTES,
    ) -> Response:
        if payload is not None and body is not None:
            raise ValueError("payload and body are mutually exclusive")
        request_headers = {
            "Accept": "application/json",
            "User-Agent": "rapp-cli/0.1",
        }
        if self.config.secret:
            request_headers["X-Brainstem-Secret"] = self.config.secret
        if headers:
            request_headers.update(headers)
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            if len(body) > _MAX_JSON_REQUEST_BYTES:
                raise UsageError("JSON request exceeds the 1 MiB CLI limit")
            request_headers["Content-Type"] = "application/json"

        request = Request(
            self._url(path),
            data=body,
            headers=request_headers,
            method=method.upper(),
        )
        try:
            with self._opener.open(request, timeout=self.config.timeout) as response:
                return Response(
                    status=response.status,
                    headers=dict(response.headers.items()),
                    body=self._read_limited(response, max_bytes),
                )
        except HTTPError as exc:
            payload = self._error_payload(exc)
            message = self._error_message(payload, exc.reason)
            details = {"status": exc.code}
            if exc.code in {401, 403}:
                raise AuthenticationFailure(message, details=details) from exc
            if exc.code == 404:
                raise NotFound(message, details=details) from exc
            if exc.code == 409:
                raise Conflict(message, details=details) from exc
            raise RemoteFailure(message, details=details) from exc
        except TimeoutError as exc:
            raise ConnectionFailure(
                f"{self.service_name} request timed out after {self.config.timeout:g} seconds",
                details={"url": self.config.brainstem_url},
            ) from exc
        except URLError as exc:
            raise ConnectionFailure(
                f"cannot reach {self.service_name} at {self.config.brainstem_url}: {exc.reason}",
                details={"url": self.config.brainstem_url},
            ) from exc

    def get_json(self, path: str) -> Any:
        return self.request("GET", path).json()

    def post_json(self, path: str, payload: Any) -> Any:
        return self.request("POST", path, payload=payload).json()

    def delete_json(self, path: str) -> Any:
        return self.request("DELETE", path).json()

    def get_bytes(self, path: str) -> bytes:
        return self.request(
            "GET",
            path,
            headers={"Accept": "application/octet-stream"},
            max_bytes=_MAX_AGENT_BYTES,
        ).body

    def export_agent(self, filename: str) -> bytes:
        return self.get_bytes(f"/agents/export/{quote(filename, safe='')}")

    def remove_agent(self, filename: str) -> Any:
        return self.delete_json(self.agent_path(filename))

    def import_agent(
        self,
        filename: str,
        payload: bytes,
        *,
        sha256: str | None = None,
        source_revision: str | None = None,
    ) -> Any:
        filename = validate_agent_filename(filename)
        if sha256 is not None:
            if not re.fullmatch(r"[0-9a-fA-F]{64}", sha256):
                raise UsageError("agent SHA-256 must contain exactly 64 hexadecimal characters")
            sha256 = sha256.lower()
        boundary = f"rapp-cli-{secrets.token_hex(16)}"
        parts: list[bytes] = []

        def add_field(name: str, value: str) -> None:
            parts.extend(
                [
                    f"--{boundary}\r\n".encode(),
                    f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                    value.encode(),
                    b"\r\n",
                ]
            )

        if sha256:
            add_field("sha256", sha256)
        if source_revision:
            add_field("source_revision", source_revision)
        parts.extend(
            [
                f"--{boundary}\r\n".encode(),
                (
                    f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
                ).encode(),
                b"Content-Type: text/x-python\r\n\r\n",
                payload,
                b"\r\n",
                f"--{boundary}--\r\n".encode(),
            ]
        )
        multipart_bytes = sum(len(part) for part in parts)
        if multipart_bytes > _MAX_AGENT_BYTES:
            raise UsageError("complete agent multipart request exceeds the Brainstem 16 MiB limit")
        return self.request(
            "POST",
            "/agents/import",
            body=b"".join(parts),
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        ).json()

    def stream_events(self, path: str, payload: Any) -> Iterator[dict[str, Any]]:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        if len(body) > _MAX_JSON_REQUEST_BYTES:
            raise UsageError("JSON request exceeds the 1 MiB CLI limit")
        headers = {
            "Accept": "text/event-stream",
            "Content-Type": "application/json",
            "User-Agent": "rapp-cli/0.1",
        }
        if self.config.secret:
            headers["X-Brainstem-Secret"] = self.config.secret
        request = Request(self._url(path), data=body, headers=headers, method="POST")
        try:
            with self._opener.open(request, timeout=self.config.timeout) as response:
                content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip()
                if content_type.casefold() != "text/event-stream":
                    raise RemoteFailure(
                        f"{self.service_name} returned {content_type or 'no content type'} "
                        "instead of text/event-stream"
                    )
                event_name = "message"
                event_id: str | None = None
                data_lines: list[str] = []
                event_bytes = 0
                while True:
                    raw_line = response.readline(_MAX_SSE_LINE_BYTES + 1)
                    if not raw_line:
                        break
                    if len(raw_line) > _MAX_SSE_LINE_BYTES:
                        raise RemoteFailure(
                            f"{self.service_name} stream contained an oversized line"
                        )
                    try:
                        line = raw_line.decode("utf-8").rstrip("\r\n")
                    except UnicodeDecodeError as exc:
                        raise RemoteFailure(
                            f"{self.service_name} stream contained invalid UTF-8"
                        ) from exc
                    if not line:
                        if data_lines or event_name != "message" or event_id is not None:
                            yield self._parse_event(event_name, event_id, data_lines)
                        event_name = "message"
                        event_id = None
                        data_lines = []
                        event_bytes = 0
                        continue
                    if line.startswith(":"):
                        continue
                    field, separator, value = line.partition(":")
                    value = value[1:] if separator and value.startswith(" ") else value
                    if field == "data":
                        event_bytes += len(raw_line)
                        if event_bytes > _MAX_SSE_EVENT_BYTES:
                            raise RemoteFailure(
                                f"{self.service_name} stream contained an oversized event"
                            )
                        data_lines.append(value)
                    elif field == "event":
                        event_name = value or "message"
                    elif field == "id" and "\x00" not in value:
                        event_id = value
                if data_lines or event_name != "message" or event_id is not None:
                    yield self._parse_event(event_name, event_id, data_lines)
        except HTTPError as exc:
            payload = self._error_payload(exc)
            message = self._error_message(payload, exc.reason)
            if exc.code in {401, 403}:
                raise AuthenticationFailure(message, details={"status": exc.code}) from exc
            if exc.code == 409:
                raise Conflict(message, details={"status": exc.code}) from exc
            raise RemoteFailure(message, details={"status": exc.code}) from exc
        except (TimeoutError, URLError) as exc:
            reason = getattr(exc, "reason", exc)
            raise ConnectionFailure(
                f"{self.service_name} stream failed at {self.config.brainstem_url}: {reason}",
                details={"url": self.config.brainstem_url},
            ) from exc

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{self.config.brainstem_url}{path}"

    @staticmethod
    def agent_path(filename: str) -> str:
        return f"/agents/{quote(filename, safe='')}"

    @staticmethod
    def _parse_event(
        event_name: str,
        event_id: str | None,
        data_lines: list[str],
    ) -> dict[str, Any]:
        data = "\n".join(data_lines)
        try:
            parsed = loads(data)
        except (json.JSONDecodeError, DuplicateKeyError, NonFiniteNumberError):
            parsed = data
        return {
            "event": event_name,
            "id": event_id,
            "data": parsed,
        }

    @staticmethod
    def _error_payload(exc: HTTPError) -> Any:
        try:
            try:
                body = exc.read(_MAX_ERROR_BYTES + 1)
            finally:
                exc.close()
        except OSError:
            return None
        if len(body) > _MAX_ERROR_BYTES:
            return None
        try:
            return loads(body.decode("utf-8"))
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
            DuplicateKeyError,
            NonFiniteNumberError,
        ):
            return None

    @staticmethod
    def _error_message(payload: Any, fallback: Any) -> str:
        if isinstance(payload, dict):
            for key in ("error", "message", "detail"):
                value = payload.get(key)
                if isinstance(value, str) and value:
                    return value
        return str(fallback or "remote request failed")

    def _read_limited(self, response: Any, limit: int) -> bytes:
        body = response.read(limit + 1)
        if len(body) > limit:
            raise RemoteFailure(
                f"{self.service_name} response exceeded the allowed size",
                details={"max_bytes": limit},
            )
        return body
