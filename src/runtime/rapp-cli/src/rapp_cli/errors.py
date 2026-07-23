from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RappError(Exception):
    """Expected CLI failure with a stable machine-readable code."""

    message: str
    code: str = "RAPP_ERROR"
    exit_code: int = 1
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.message


class UsageError(RappError):
    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            code="INVALID_USAGE",
            exit_code=2,
            details=details or {},
        )


class ConnectionFailure(RappError):
    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            code="CONNECTION_FAILED",
            exit_code=4,
            details=details or {},
        )


class AuthenticationFailure(RappError):
    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            code="AUTHENTICATION_FAILED",
            exit_code=5,
            details=details or {},
        )


class NotFound(RappError):
    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            code="NOT_FOUND",
            exit_code=4,
            details=details or {},
        )


class Conflict(RappError):
    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            code="CONFLICT",
            exit_code=6,
            details=details or {},
        )


class RemoteFailure(RappError):
    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            code="REMOTE_FAILED",
            exit_code=7,
            details=details or {},
        )


class IntegrityFailure(RappError):
    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            code="INTEGRITY_FAILED",
            exit_code=8,
            details=details or {},
        )


class CapabilityUnavailable(RappError):
    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            code="CAPABILITY_UNAVAILABLE",
            exit_code=3,
            details=details or {},
        )


class InternalFailure(RappError):
    def __init__(self, message: str = "unexpected internal CLI failure") -> None:
        super().__init__(
            message=message,
            code="INTERNAL_ERROR",
            exit_code=70,
        )


class ConfirmationRequired(RappError):
    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            code="CONFIRMATION_REQUIRED",
            exit_code=6,
        )


class DoctorFailure(RappError):
    def __init__(self, checks: list[dict[str, Any]], message: str) -> None:
        super().__init__(
            message=message,
            code="DOCTOR_FAILED",
            exit_code=1,
            details={"checks": checks},
        )
