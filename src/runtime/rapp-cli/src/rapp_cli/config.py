from __future__ import annotations

import ipaddress
import math
import os
import stat as stat_module
from collections.abc import Mapping
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from .errors import UsageError
from .filesystem import is_reparse_point
from .jsonio import DuplicateKeyError, NonFiniteNumberError, loads

DEFAULT_BRAINSTEM_URL = "http://127.0.0.1:7071"
DEFAULT_TIMEOUT = 30.0
_MAX_CONFIG_BYTES = 1024 * 1024


def _config_home(env: Mapping[str, str]) -> Path:
    if env.get("XDG_CONFIG_HOME"):
        return Path(env["XDG_CONFIG_HOME"]).expanduser()
    if os.name == "nt" and env.get("APPDATA"):
        return Path(env["APPDATA"]).expanduser()
    return Path.home() / ".config"


def default_config_path(env: Mapping[str, str] | None = None) -> Path:
    values = os.environ if env is None else env
    configured = values.get("RAPP_CONFIG_FILE") or values.get("RAPP_CONFIG")
    if configured:
        return Path(configured).expanduser()
    return _config_home(values) / "rapp" / "config.json"


def normalize_base_url(value: str, *, allow_insecure_http: bool = False) -> str:
    candidate = value.strip()
    try:
        parsed = urlsplit(candidate)
    except ValueError as exc:
        raise UsageError(f"invalid Brainstem URL: {exc}") from exc
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise UsageError("Brainstem URL must be an absolute http:// or https:// URL")
    if parsed.username or parsed.password:
        raise UsageError("Brainstem URL must not contain credentials")
    if parsed.query or parsed.fragment:
        raise UsageError("Brainstem URL must not contain a query string or fragment")
    try:
        port = parsed.port
    except ValueError as exc:
        raise UsageError(f"invalid Brainstem URL port: {exc}") from exc
    if port is not None and port == 0:
        raise UsageError("Brainstem URL port must be between 1 and 65535")
    if parsed.scheme == "http" and not allow_insecure_http:
        hostname = parsed.hostname.lower()
        is_loopback = hostname == "localhost"
        if not is_loopback:
            try:
                is_loopback = ipaddress.ip_address(hostname).is_loopback
            except ValueError:
                is_loopback = False
        if not is_loopback:
            raise UsageError(
                "plaintext HTTP is allowed only for loopback; use HTTPS or --allow-insecure-http"
            )
    path = parsed.path.rstrip("/")
    return urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))


def _positive_timeout(value: Any) -> float:
    if isinstance(value, bool):
        raise UsageError("timeout must be a positive number")
    try:
        timeout = float(value)
    except (TypeError, ValueError) as exc:
        raise UsageError("timeout must be a positive number") from exc
    if not math.isfinite(timeout) or timeout <= 0 or timeout > 3600:
        raise UsageError("timeout must be greater than 0 and no more than 3600 seconds")
    return timeout


def _read_config(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as handle:
            info = os.fstat(handle.fileno())
            if not stat_module.S_ISREG(info.st_mode):
                raise UsageError(f"config path must be a regular file: {path}")
            if info.st_size > _MAX_CONFIG_BYTES:
                raise UsageError(f"config file {path} exceeds 1 MiB")
            raw = handle.read(_MAX_CONFIG_BYTES + 1)
        if len(raw) > _MAX_CONFIG_BYTES:
            raise UsageError(f"config file {path} exceeds 1 MiB")
        payload = loads(raw.decode("utf-8"))
    except FileNotFoundError:
        return {}
    except OSError as exc:
        raise UsageError(f"cannot read config file {path}: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise UsageError(f"config file {path} is not UTF-8 text") from exc
    except DuplicateKeyError as exc:
        raise UsageError(f"config file {path} has duplicate fields: {exc}") from exc
    except NonFiniteNumberError as exc:
        raise UsageError(f"config file {path} contains {exc}") from exc
    except JSONDecodeError as exc:
        raise UsageError(
            f"config file {path} is not valid JSON",
            details={"line": exc.lineno, "column": exc.colno},
        ) from exc
    if not isinstance(payload, dict):
        raise UsageError(f"config file {path} must contain a JSON object")
    unknown = sorted(set(payload) - {"brainstem_url", "timeout", "brainstem_secret_file"})
    if unknown:
        raise UsageError(f"config file {path} contains unknown fields: {', '.join(unknown)}")
    return payload


def _read_secret_file(path: Path) -> str:
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        if is_reparse_point(path):
            raise UsageError(f"Brainstem secret file {path} must not be a reparse point")
        fd = os.open(path, flags)
    except UsageError:
        raise
    except OSError as exc:
        raise UsageError(f"cannot read Brainstem secret file {path}: {exc}") from exc
    with os.fdopen(fd, "rb") as handle:
        info = os.fstat(handle.fileno())
        if not stat_module.S_ISREG(info.st_mode):
            raise UsageError(f"Brainstem secret file {path} must be a regular file")
        if os.name == "posix" and stat_module.S_IMODE(info.st_mode) & 0o077:
            raise UsageError(
                f"Brainstem secret file {path} must not be readable by group or others"
            )
        raw = handle.read(64 * 1024 + 1)
    if len(raw) > 64 * 1024:
        raise UsageError(f"Brainstem secret file {path} is too large")
    try:
        secret = raw.decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise UsageError(f"Brainstem secret file {path} is not UTF-8 text") from exc
    if not secret:
        raise UsageError(f"Brainstem secret file {path} is empty")
    return secret


@dataclass(frozen=True, slots=True)
class Config:
    brainstem_url: str
    timeout: float
    secret: str | None
    config_path: Path

    @classmethod
    def load(
        cls,
        *,
        config_path: str | Path | None = None,
        brainstem_url: str | None = None,
        timeout: float | None = None,
        secret: str | None = None,
        secret_file: str | Path | None = None,
        allow_insecure_http: bool = False,
        env: Mapping[str, str] | None = None,
    ) -> Config:
        values = os.environ if env is None else env
        path = Path(config_path).expanduser() if config_path else default_config_path(values)
        file_values = _read_config(path)

        url_value = (
            brainstem_url
            or values.get("RAPP_ENDPOINT")
            or values.get("RAPP_BRAINSTEM_URL")
            or file_values.get("brainstem_url")
            or DEFAULT_BRAINSTEM_URL
        )
        timeout_value = (
            timeout
            if timeout is not None
            else values.get("RAPP_TIMEOUT", file_values.get("timeout", DEFAULT_TIMEOUT))
        )

        resolved_secret = secret or values.get("RAPP_BRAINSTEM_SECRET")
        secret_path = secret_file or values.get("RAPP_BRAINSTEM_SECRET_FILE")
        if resolved_secret is None and secret_path is None:
            secret_path = file_values.get("brainstem_secret_file")
        if secret_path is not None and not isinstance(secret_path, (str, Path)):
            raise UsageError("brainstem_secret_file in config must be a string path")
        if resolved_secret is None and secret_path:
            resolved_secret = _read_secret_file(Path(secret_path).expanduser())

        if not isinstance(url_value, str):
            raise UsageError("brainstem_url in config must be a string")
        if resolved_secret is not None and not isinstance(resolved_secret, str):
            raise UsageError("Brainstem secret must be a string")

        return cls(
            brainstem_url=normalize_base_url(
                url_value,
                allow_insecure_http=allow_insecure_http,
            ),
            timeout=_positive_timeout(timeout_value),
            secret=resolved_secret,
            config_path=path,
        )
