"""Strict structural normalization for the target-owned RAPP/1 façade."""

from typing import Any, Dict


class CompatibilityError(ValueError):
    http_status = 422

    def __init__(self):
        super().__init__("malformed-request")
        self.code = "malformed-request"
        self.step = None

    def as_422(self) -> Dict[str, Any]:
        return {"error": {"code": self.code, "step": self.step}}


def normalize_request(value: Any) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise CompatibilityError()
    allowed = {"user_input", "session_id", "idempotency_key"}
    if "user_input" not in value or not isinstance(value["user_input"], str):
        raise CompatibilityError()
    for optional in ("session_id", "idempotency_key"):
        if optional in value and not isinstance(value[optional], str):
            raise CompatibilityError()
    return {key: value[key] for key in ("user_input", "session_id", "idempotency_key") if key in value}


def normalize_success(response: Any, agent_logs: Any, session_id: Any) -> Dict[str, Any]:
    if not isinstance(response, str):
        raise CompatibilityError()
    if not isinstance(agent_logs, list) or not all(
        isinstance(entry, str) for entry in agent_logs
    ):
        raise CompatibilityError()
    if not isinstance(session_id, str):
        raise CompatibilityError()
    return {
        "response": response,
        "agent_logs": agent_logs,
        "session_id": session_id,
    }
