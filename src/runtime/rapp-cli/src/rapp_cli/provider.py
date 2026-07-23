from __future__ import annotations

from typing import Any

from .errors import RemoteFailure


def raise_provider_error(payload: Any) -> None:
    if not isinstance(payload, dict):
        return
    error = payload.get("error")
    if isinstance(error, str) and error:
        raise RemoteFailure(error)
    if isinstance(error, dict):
        message = error.get("message") or error.get("code") or "Brainstem operation failed"
        raise RemoteFailure(str(message))


def require_provider_object(payload: Any, operation: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise RemoteFailure(f"Brainstem {operation} response must be a JSON object")
    raise_provider_error(payload)
    return payload


def require_provider_success(payload: Any, operation: str) -> dict[str, Any]:
    response = require_provider_object(payload, operation)
    if "status" in response and response["status"] != "ok":
        raise RemoteFailure(
            f"Brainstem {operation} response reported non-ok status",
            details={"status": response["status"]},
        )
    return response
