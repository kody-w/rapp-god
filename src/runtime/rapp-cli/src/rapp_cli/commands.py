from __future__ import annotations

import contextlib
import hashlib
import hmac
import math
import os
import platform
import re
import stat as stat_module
import sys
import tempfile
import time
from collections.abc import Sequence
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from .agent_files import (
    read_agent_source as _read_agent_source,
)
from .agent_files import (
    validate_agent_filename as _agent_filename,
)
from .client import BrainstemClient
from .config import Config
from .errors import (
    AuthenticationFailure,
    CapabilityUnavailable,
    ConfirmationRequired,
    Conflict,
    DoctorFailure,
    IntegrityFailure,
    RappError,
    RemoteFailure,
    UsageError,
)
from .jsonio import DuplicateKeyError, NonFiniteNumberError, loads
from .output import Output
from .provider import raise_provider_error as _raise_provider_error
from .provider import require_provider_success
from .rar import RAR_REVISION, RarClient, installability
from .release_train import RINGS, ReleaseTrainClient
from .runtime import locate_brainstem, run_brainstem
from .twin_hatch import hatch_twin as hatch_local_twin
from .twins import default_twins_home, list_twins, show_twin

_MAX_HISTORY_BYTES = 1024 * 1024
_MAX_CHAT_BYTES = 1024 * 1024


@dataclass(frozen=True, slots=True)
class Result:
    data: Any
    message: str | None = None


@dataclass(slots=True)
class Context:
    config: Config
    client: BrainstemClient
    output: Output


def status(ctx: Context, _args: Any) -> Result:
    payload = ctx.client.get_json("/version")
    if not isinstance(payload, dict) or not isinstance(payload.get("version"), str):
        raise RemoteFailure("Brainstem version response is missing a string version")
    data = {
        "status": "reachable",
        "version": payload["version"],
        "endpoint": ctx.config.brainstem_url,
        "probe": "/version",
    }
    return Result(data, f"Brainstem reachable | v{payload['version']}")


def brainstem_health(ctx: Context, _args: Any) -> Result:
    health = ctx.client.get_json("/health")
    if not isinstance(health, dict):
        raise RemoteFailure("Brainstem health response must be a JSON object")
    state = health.get("status", "unknown")
    if state == "unauthenticated":
        raise AuthenticationFailure("Brainstem is running but unauthenticated")
    if health.get("copilot") == "no_access":
        raise AuthenticationFailure("GitHub account does not have Copilot access")
    details = [str(state)]
    if health.get("version"):
        details.append(f"v{health['version']}")
    if health.get("model"):
        details.append(str(health["model"]))
    return Result(health, "Brainstem " + " | ".join(details))


def brainstem_version(ctx: Context, _args: Any) -> Result:
    payload = ctx.client.get_json("/version")
    if not isinstance(payload, dict) or not isinstance(payload.get("version"), str):
        raise RemoteFailure("Brainstem version response is missing a string version")
    return Result(payload, payload["version"])


def brainstem_locate(_ctx: Context, args: Any) -> Result:
    installation = locate_brainstem(args.home)
    payload = installation.to_dict()
    lines = [
        f"home: {payload['home']}",
        f"source: {payload['source']}",
        f"python: {payload['python']}",
    ]
    return Result(payload, "\n".join(lines))


def brainstem_run(ctx: Context, args: Any) -> Result:
    if ctx.output.json_mode:
        raise UsageError("foreground Brainstem launch requires human output")
    installation = locate_brainstem(args.home)
    return_code = run_brainstem(installation)
    if return_code != 0:
        raise RemoteFailure(
            f"Brainstem exited with status {return_code}",
            details={"return_code": return_code},
        )
    return Result({"return_code": 0}, "Brainstem stopped")


def _read_history(path: str | None) -> list[dict[str, str]]:
    if path is None:
        return []
    source = Path(path).expanduser()
    try:
        with source.open("rb") as handle:
            info = os.fstat(handle.fileno())
            if not stat_module.S_ISREG(info.st_mode):
                raise UsageError(f"conversation history must be a regular file: {source}")
            if info.st_size > _MAX_HISTORY_BYTES:
                raise UsageError("conversation history exceeds the 1 MiB CLI limit")
            raw = handle.read(_MAX_HISTORY_BYTES + 1)
        if len(raw) > _MAX_HISTORY_BYTES:
            raise UsageError("conversation history exceeds the 1 MiB CLI limit")
        payload = loads(raw.decode("utf-8"))
    except OSError as exc:
        raise UsageError(f"cannot read conversation history {source}: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise UsageError(f"conversation history {source} is not UTF-8 text") from exc
    except DuplicateKeyError as exc:
        raise UsageError(f"conversation history {source} has duplicate fields: {exc}") from exc
    except NonFiniteNumberError as exc:
        raise UsageError(f"conversation history {source} contains {exc}") from exc
    except JSONDecodeError as exc:
        raise UsageError(
            f"conversation history {source} is not valid JSON",
            details={"line": exc.lineno, "column": exc.colno},
        ) from exc
    if not isinstance(payload, list):
        raise UsageError("conversation history must be a JSON array")
    history: list[dict[str, str]] = []
    for index, turn in enumerate(payload):
        if not isinstance(turn, dict):
            raise UsageError(f"conversation history item {index} must be an object")
        role = turn.get("role")
        content = turn.get("content")
        if role not in {"user", "assistant", "tool"} or not isinstance(content, str):
            raise UsageError(
                f"conversation history item {index} requires a valid role and string content"
            )
        history.append({"role": role, "content": content})
    return history


def chat(ctx: Context, args: Any) -> Result | None:
    message = " ".join(args.message).strip()
    if args.message == ["-"]:
        message = _read_stdin_message()
    if not message:
        if sys.stdin.isatty():
            return _chat_repl(ctx, args)
        message = _read_stdin_message()
    if not message:
        raise UsageError("chat requires a non-empty message or piped stdin")
    history = _read_history(args.history)
    result = _chat_once(ctx, args, message, history)
    return None if args.stream else result


def _read_stdin_message() -> str:
    value = sys.stdin.read(_MAX_CHAT_BYTES + 1)
    if len(value.encode("utf-8")) > _MAX_CHAT_BYTES:
        raise UsageError("piped chat input exceeds the 1 MiB CLI limit")
    return value.strip()


def _chat_once(
    ctx: Context,
    args: Any,
    message: str,
    history: list[dict[str, str]],
) -> Result | None:
    payload: dict[str, Any] = {
        "user_input": message,
        "conversation_history": history,
    }
    if args.session_id:
        payload["session_id"] = args.session_id

    if args.stream:
        saw_delta = False
        done_payload: dict[str, Any] | None = None
        response_text = ""
        for event in ctx.client.stream_events("/chat/stream", payload):
            data = event.get("data")
            if not isinstance(data, dict) or not isinstance(data.get("type"), str):
                raise RemoteFailure("Brainstem stream event is missing a string type")
            event_type = data["type"]
            if event_type == "delta":
                text = data.get("text")
                if not isinstance(text, str):
                    raise RemoteFailure("Brainstem delta event is missing string text")
                saw_delta = saw_delta or bool(text)
                if ctx.output.json_mode:
                    ctx.output.stream_event({"type": "delta", "text": text})
                else:
                    ctx.output.stream_event(text)
                continue
            if event_type == "agent":
                if args.show_agent_logs:
                    logs = data.get("logs")
                    if ctx.output.json_mode:
                        ctx.output.stream_event({"type": "agent", "logs": logs})
                    elif isinstance(logs, str) and logs:
                        ctx.output.diagnostic(f"agent logs: {logs}")
                continue
            if event_type == "error":
                message = data.get("error")
                message = message if isinstance(message, str) else "Brainstem stream failed"
                if data.get("no_copilot_access"):
                    raise AuthenticationFailure(message)
                raise RemoteFailure(message)
            if event_type == "done":
                if done_payload is not None:
                    raise RemoteFailure("Brainstem stream emitted more than one done event")
                response = data.get("response")
                if not isinstance(response, str):
                    raise RemoteFailure("Brainstem done event is missing a string response")
                done_payload = dict(data)
                response_text = response
                logs = done_payload.pop("agent_logs", None)
                if args.show_agent_logs and logs:
                    done_payload["agent_logs"] = [logs] if isinstance(logs, str) else logs
                if ctx.output.json_mode:
                    ctx.output.stream_event(done_payload)
                elif not saw_delta:
                    ctx.output.stream_event(response)
                continue
        if done_payload is None:
            raise RemoteFailure("Brainstem stream ended without a done event")
        if not ctx.output.json_mode:
            ctx.output.stream_event("\n")
        return Result(done_payload, response_text)

    response = ctx.client.post_json("/chat", payload)
    if not isinstance(response, dict):
        raise RemoteFailure("Brainstem chat response must be a JSON object")
    if response.get("no_copilot_access"):
        raise AuthenticationFailure("GitHub account does not have Copilot access")
    _raise_provider_error(response)
    text = response.get("response")
    if not isinstance(text, str):
        raise RemoteFailure("Brainstem chat response is missing a string response")
    normalized = dict(response)
    agent_logs = normalized.pop("agent_logs", None)
    if args.show_agent_logs and agent_logs:
        logs = [agent_logs] if isinstance(agent_logs, str) else agent_logs
        normalized["agent_logs"] = logs
        if not ctx.output.json_mode:
            ctx.output.diagnostic(f"agent logs: {logs}")
    return Result(normalized, text)


def _chat_repl(ctx: Context, args: Any) -> None:
    if ctx.output.json_mode:
        raise UsageError("interactive chat requires human output; omit --json and --jsonl")
    history = _read_history(args.history)
    print("RAPP chat. /help for commands; /exit to leave.", file=ctx.output.stdout)
    while True:
        try:
            message = input("rapp> ").strip()
        except EOFError:
            print(file=ctx.output.stdout)
            return None
        except KeyboardInterrupt:
            print(file=ctx.output.stdout)
            return None
        if not message:
            continue
        if message in {"/exit", "/quit"}:
            return None
        if message == "/reset":
            history = []
            print("history cleared", file=ctx.output.stdout)
            continue
        if message == "/help":
            print("/help  /reset  /status  /exit", file=ctx.output.stdout)
            continue
        if message == "/status":
            result = status(ctx, args)
            ctx.output.success(result.data, message=result.message)
            continue
        if message.startswith("/") and not message.startswith("//"):
            print(f"unknown chat command: {message}", file=ctx.output.stderr)
            continue
        if message.startswith("//"):
            message = message[1:]
        result = _chat_once(ctx, args, message, history)
        text = result.message or ""
        if not args.stream:
            ctx.output.stream_event(text + "\n")
        history.extend(
            [
                {"role": "user", "content": message},
                {"role": "assistant", "content": text},
            ]
        )


def model_list(ctx: Context, _args: Any) -> Result:
    payload = ctx.client.get_json("/models")
    _raise_provider_error(payload)
    if not isinstance(payload, dict) or not isinstance(payload.get("models"), list):
        raise RemoteFailure("Brainstem models response is missing a models array")
    current = payload.get("current")
    if not isinstance(current, str):
        raise RemoteFailure("Brainstem models response is missing the current model")
    if not payload["models"]:
        raise RemoteFailure("Brainstem models response contains no models")
    lines = []
    for model in payload["models"]:
        if not isinstance(model, dict) or not isinstance(model.get("id"), str):
            raise RemoteFailure("Brainstem models response contains an invalid model")
        model_id = model["id"]
        marker = "*" if model_id == current else " "
        lines.append(f"{marker} {model_id}")
    return Result(payload, "\n".join(lines))


def model_set(ctx: Context, args: Any) -> Result:
    payload = ctx.client.post_json("/models/set", {"model": args.model})
    _raise_provider_error(payload)
    if not isinstance(payload, dict):
        raise RemoteFailure("Brainstem model selection response must be a JSON object")
    selected = payload.get("model")
    if not isinstance(selected, str) or not selected:
        raise RemoteFailure("Brainstem model selection response is missing the selected model")
    return Result(payload, f"model: {selected}")


def auth_status(ctx: Context, _args: Any) -> Result:
    payload = ctx.client.get_json("/login/status")
    if not isinstance(payload, dict) or not isinstance(payload.get("pending"), bool):
        raise RemoteFailure("Brainstem login status response is invalid")
    if payload["pending"]:
        details = ["login pending"]
        if isinstance(payload.get("verification_uri"), str):
            details.append(f"open: {payload['verification_uri']}")
        if isinstance(payload.get("user_code"), str):
            details.append(f"code: {payload['user_code']}")
        if isinstance(payload.get("expires_in"), int):
            details.append(f"expires_in: {payload['expires_in']} seconds")
        message = "\n".join(details)
    else:
        message = "no login pending"
    return Result(payload, message)


def auth_poll(ctx: Context, _args: Any) -> Result:
    payload = ctx.client.post_json("/login/poll", {})
    status = _login_poll_status(payload)
    return Result(payload, f"login: {status}")


def _login_poll_status(payload: Any) -> str:
    if not isinstance(payload, dict) or not isinstance(payload.get("status"), str):
        raise RemoteFailure("Brainstem login poll response is invalid")
    status = payload["status"]
    if status == "expired":
        raise RemoteFailure(str(payload.get("error") or "login code expired"))
    if status in {"unauthenticated", "no_copilot_access"}:
        raise AuthenticationFailure(str(payload.get("error") or status))
    if status == "error":
        message = str(payload.get("error") or "login failed")
        if "NO_COPILOT_ACCESS" in message or payload.get("no_copilot_access"):
            raise AuthenticationFailure(message)
        raise RemoteFailure(message)
    if status not in {"pending", "ok"}:
        raise RemoteFailure(f"unknown login status: {status}")
    return status


def auth_login(ctx: Context, args: Any) -> Result:
    if not math.isfinite(args.deadline) or args.deadline <= 0 or args.deadline > 3600:
        raise UsageError("--deadline must be greater than 0 and no more than 3600 seconds")
    if args.wait and ctx.output.json_mode:
        raise UsageError("--wait is interactive; use `auth login` followed by `auth poll` for JSON")
    payload = ctx.client.post_json("/login", {})
    if not isinstance(payload, dict):
        raise RemoteFailure("Brainstem login response must be a JSON object")
    _raise_provider_error(payload)
    code = payload.get("user_code")
    verification_uri = payload.get("verification_uri")
    if not isinstance(code, str) or not isinstance(verification_uri, str):
        raise RemoteFailure("Brainstem login response is missing code information")
    if not args.wait:
        return Result(
            payload,
            f"Open {verification_uri} and enter code {code}",
        )
    ctx.output.diagnostic(f"Open {verification_uri} and enter code {code}")

    interval_value = payload.get("interval", 5.0)
    if isinstance(interval_value, bool):
        raise RemoteFailure("Brainstem login response contains an invalid polling interval")
    try:
        interval = float(interval_value)
    except (TypeError, ValueError) as exc:
        raise RemoteFailure(
            "Brainstem login response contains an invalid polling interval"
        ) from exc
    if not math.isfinite(interval) or interval <= 0 or interval > 300:
        raise RemoteFailure("Brainstem login response contains an invalid polling interval")

    deadline = time.monotonic() + args.deadline
    while (remaining := deadline - time.monotonic()) > 0:
        time.sleep(min(interval, remaining))
        polled = ctx.client.post_json("/login/poll", {})
        status = _login_poll_status(polled)
        if status == "pending":
            continue
        if status == "ok":
            return Result(polled, "login complete")
    raise RemoteFailure(
        f"login did not complete within {args.deadline:g} seconds",
        details={"user_code": code},
    )


def auth_retry(ctx: Context, _args: Any) -> Result:
    payload = ctx.client.post_json("/login/retry", {})
    if not isinstance(payload, dict) or not isinstance(payload.get("status"), str):
        raise RemoteFailure("Brainstem login retry response is invalid")
    if payload["status"] in {"unauthenticated", "no_copilot_access"}:
        raise AuthenticationFailure(str(payload.get("error") or payload["status"]))
    if payload["status"] != "ok":
        raise RemoteFailure(str(payload.get("error") or f"login retry: {payload['status']}"))
    return Result(payload, "Copilot access ready")


def auth_switch(ctx: Context, args: Any) -> Result:
    if not args.yes:
        raise ConfirmationRequired("account switching clears cached credentials and requires --yes")
    payload = ctx.client.post_json("/login/switch", {})
    if not isinstance(payload, dict):
        raise RemoteFailure("Brainstem account switch response must be a JSON object")
    _raise_provider_error(payload)
    code = payload.get("user_code")
    verification_uri = payload.get("verification_uri")
    message = (
        f"Open {verification_uri} and enter code {code}"
        if isinstance(code, str) and isinstance(verification_uri, str)
        else "account switch started"
    )
    return Result(payload, message)


def agent_list(ctx: Context, _args: Any) -> Result:
    payload = ctx.client.get_json("/agents")
    _raise_provider_error(payload)
    if not isinstance(payload, dict) or not isinstance(payload.get("files"), list):
        raise RemoteFailure("Brainstem agents response is missing a files array")
    lines = []
    for item in payload["files"]:
        if not isinstance(item, dict):
            continue
        filename = item.get("filename")
        agents = item.get("agents")
        if not isinstance(filename, str):
            continue
        names = ", ".join(str(name) for name in agents) if isinstance(agents, list) else ""
        lines.append(f"{filename}: {names}" if names else filename)
    return Result(payload, "\n".join(lines))


def agent_import(ctx: Context, args: Any) -> Result:
    if not args.yes:
        raise ConfirmationRequired(
            "agent import executes user-supplied Python inside the Brainstem and requires --yes"
        )
    source = Path(args.file).expanduser()
    _agent_filename(source.name)
    payload_bytes = _read_agent_source(source)
    if args.sha256:
        if not re.fullmatch(r"[0-9a-fA-F]{64}", args.sha256):
            raise UsageError("--sha256 must contain exactly 64 hexadecimal characters")
        actual = hashlib.sha256(payload_bytes).hexdigest()
        if not hmac.compare_digest(actual, args.sha256.lower()):
            raise IntegrityFailure(
                "agent file does not match --sha256",
                details={"actual_sha256": actual},
            )
    payload = ctx.client.import_agent(
        source.name,
        payload_bytes,
        sha256=args.sha256,
        source_revision=None,
    )
    require_provider_success(payload, "agent import")
    return Result(payload, f"imported {source.name}")


def agent_export(ctx: Context, args: Any) -> Result:
    filename = _agent_filename(args.filename)
    destination = Path(args.output or filename).expanduser()
    if destination.exists() and not args.force:
        raise Conflict(f"refusing to overwrite existing file: {destination}")
    if destination.exists() and destination.is_dir():
        raise UsageError(f"output path is a directory: {destination}")
    payload = ctx.client.export_agent(filename)
    _atomic_write_file(destination, payload, replace=args.force)
    data = {"filename": filename, "path": str(destination), "bytes": len(payload)}
    return Result(data, f"exported {filename} to {destination}")


def _atomic_write_file(destination: Path, payload: bytes, *, replace: bool) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not replace:
        try:
            fd = os.open(
                destination,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
        except FileExistsError as exc:
            raise Conflict(f"refusing to overwrite existing file: {destination}") from exc
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
        except BaseException:
            with contextlib.suppress(OSError):
                destination.unlink()
            raise
        _fsync_directory(destination.parent)
        return

    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            if os.name == "posix":
                os.fchmod(handle.fileno(), 0o600)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        _fsync_directory(destination.parent)
    finally:
        with contextlib.suppress(FileNotFoundError):
            temporary.unlink()


def _fsync_directory(directory: Path) -> None:
    if os.name != "posix":
        return
    directory_fd = os.open(
        directory,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
    )
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def agent_remove(ctx: Context, args: Any) -> Result:
    filename = _agent_filename(args.filename)
    if not args.yes:
        raise ConfirmationRequired("agent removal requires --yes")
    payload = ctx.client.remove_agent(filename)
    require_provider_success(payload, "agent removal")
    return Result(payload, f"removed {filename}")


def agent_search(ctx: Context, args: Any) -> Result:
    agents = RarClient(timeout=ctx.config.timeout).search(args.query)
    compact = []
    for agent in agents:
        installable, blocker = installability(agent)
        compact.append(
            {
                "name": agent.get("name"),
                "display_name": agent.get("display_name"),
                "description": agent.get("description"),
                "version": agent.get("version"),
                "category": agent.get("category"),
                "quality_tier": agent.get("quality_tier"),
                "requires_env": agent.get("requires_env", []),
                "installable": installable,
                "install_blocker": blocker,
            }
        )
    lines = [
        f"{agent['name']}: {agent['description']}"
        for agent in compact
        if isinstance(agent["name"], str)
    ]
    return Result(
        {"revision": RAR_REVISION, "agents": compact},
        "\n".join(lines) if lines else "no matching RAR agents",
    )


def agent_info(ctx: Context, args: Any) -> Result:
    agent = RarClient(timeout=ctx.config.timeout).info(args.name)
    installable, blocker = installability(agent)
    lines = [
        f"name: {agent.get('name')}",
        f"display_name: {agent.get('display_name')}",
        f"version: {agent.get('version')}",
        f"category: {agent.get('category')}",
        f"quality_tier: {agent.get('quality_tier')}",
        f"description: {agent.get('description')}",
        f"installable: {str(installable).lower()}",
    ]
    if blocker:
        lines.append(f"install_blocker: {blocker}")
    return Result(
        {
            "revision": RAR_REVISION,
            "agent": agent,
            "installable": installable,
            "install_blocker": blocker,
        },
        "\n".join(lines),
    )


def agent_install(ctx: Context, args: Any) -> Result:
    if not args.yes:
        raise ConfirmationRequired(
            "RAR installation executes downloaded Python inside the Brainstem and requires --yes"
        )
    rar = RarClient(timeout=ctx.config.timeout)
    agent = rar.info(args.name)
    installable, blocker = installability(agent)
    if not installable:
        raise CapabilityUnavailable(f"{args.name} is not installable: {blocker}")
    filename, source, digest = rar.source(agent)
    _agent_filename(filename)
    payload = ctx.client.import_agent(
        filename,
        source,
        sha256=digest,
        source_revision=RAR_REVISION,
    )
    require_provider_success(payload, "agent import")
    data = {
        "name": args.name,
        "filename": filename,
        "sha256": digest,
        "source_revision": RAR_REVISION,
        "brainstem": payload,
    }
    return Result(data, f"installed {args.name} as {filename}")


def doctor(ctx: Context, args: Any) -> Result:
    checks: list[dict[str, Any]] = [
        {
            "name": "python",
            "ok": sys.version_info >= (3, 11),
            "detail": platform.python_version(),
        },
        {
            "name": "config",
            "ok": True,
            "detail": str(ctx.config.config_path),
        },
        {
            "name": "brainstem_url",
            "ok": True,
            "detail": ctx.config.brainstem_url,
        },
    ]
    if not args.offline:
        try:
            version = ctx.client.get_json("/version")
        except RappError as exc:
            checks.append({"name": "brainstem", "ok": False, "detail": str(exc)})
        else:
            checks.append(
                {
                    "name": "brainstem",
                    "ok": isinstance(version, dict) and isinstance(version.get("version"), str),
                    "detail": version,
                }
            )
        if args.deep:
            try:
                health = ctx.client.get_json("/health")
            except RappError as exc:
                checks.append({"name": "brainstem_deep", "ok": False, "detail": str(exc)})
            else:
                checks.append(
                    {
                        "name": "brainstem_deep",
                        "ok": isinstance(health, dict) and health.get("status") in {"ok", "ready"},
                        "detail": health,
                    }
                )
    ok = all(check["ok"] for check in checks)
    lines = [
        f"{'ok' if check['ok'] else 'fail'}  {check['name']}: {check['detail']}" for check in checks
    ]
    if not ok:
        raise DoctorFailure(checks, "\n".join([*lines, "doctor checks failed"]))
    return Result({"ok": ok, "checks": checks}, "\n".join(lines))


def config_path(ctx: Context, _args: Any) -> Result:
    value = str(ctx.config.config_path)
    return Result({"path": value}, value)


def config_show(ctx: Context, _args: Any) -> Result:
    payload = {
        "brainstem_url": ctx.config.brainstem_url,
        "timeout": ctx.config.timeout,
        "secret_configured": ctx.config.secret is not None,
        "config_path": str(ctx.config.config_path),
    }
    lines = [
        f"brainstem_url: {payload['brainstem_url']}",
        f"timeout: {payload['timeout']:g}",
        f"secret_configured: {str(payload['secret_configured']).lower()}",
        f"config_path: {payload['config_path']}",
    ]
    return Result(payload, "\n".join(lines))


def capabilities(ctx: Context, _args: Any) -> Result:
    try:
        installation = locate_brainstem()
    except RappError:
        installed = False
        installation_data = None
    else:
        installed = True
        installation_data = installation.to_dict()

    payload = {
        "brainstem": {
            "implementation": "provider_adapter",
            "provider": "kody-w/rapp-installer",
            "installed": installed,
            "installation": installation_data,
            "commands": ["health", "version", "run", "chat", "agent", "model"],
        },
        "ring": {
            "implementation": "read_only_observation",
            "provider": "kody-w/rapp-release-train",
            "installed": False,
            "commands": ["list", "status"],
        },
        "twin": {
            "implementation": "local_folder_hatch",
            "provider": "rapp-cli",
            "installed": True,
            "commands": ["hatch", "list", "show"],
            "unavailable_commands": ["drive"],
            "legacy_commands": ["legacy-list", "legacy-show"],
        },
        "rar": {
            "implementation": "integrity_pinned_snapshot",
            "provider": "kody-w/RAR",
            "installed": False,
            "commands": ["agent search", "agent info", "agent install"],
        },
        "rapp_1": {
            "implementation": "pre_acceptance_unavailable",
            "provider": "kody-w/rapp-1",
            "installed": False,
            "commands": [],
        },
    }
    lines = [
        (f"{name}: {value['implementation']}" + (" (installed)" if value["installed"] else ""))
        for name, value in payload.items()
    ]
    return Result(payload, "\n".join(lines))


def unavailable_capability(_ctx: Context, args: Any) -> Result:
    capability = getattr(args, "capability", args.command)
    raise CapabilityUnavailable(
        f"{capability} is not published as an executable RAPP capability yet",
        details={"capability": capability},
    )


def ring_list(ctx: Context, args: Any) -> Result:
    payload = ReleaseTrainClient(
        timeout=ctx.config.timeout,
        source=args.source,
        allow_insecure_http=args.allow_insecure_http,
    ).manifest()
    version_entry = next(
        (
            entry
            for entry in payload["entries"]
            if isinstance(entry, dict) and entry.get("name") == "rapp_brainstem/VERSION"
        ),
        None,
    )
    if not isinstance(version_entry, dict) or not isinstance(version_entry.get("sources"), list):
        raise RemoteFailure("release train manifest is missing ring sources")
    rings = [
        {
            "name": source.get("label"),
            "url": source.get("url"),
            "human_merge_required": source.get("label") == "grail",
        }
        for source in version_entry["sources"]
        if isinstance(source, dict) and isinstance(source.get("label"), str)
    ]
    lines = []
    for ring in rings:
        name = ring.get("name")
        repository = ring.get("url")
        if isinstance(name, str):
            suffix = " (human merge)" if ring.get("human_merge_required") else ""
            lines.append(f"{name}: {repository}{suffix}")
    return Result({"schema": payload["schema"], "rings": rings}, "\n".join(lines))


def ring_status(ctx: Context, args: Any) -> Result:
    payload = ReleaseTrainClient(
        timeout=ctx.config.timeout,
        source=args.source,
        allow_insecure_http=args.allow_insecure_http,
    ).status()
    ring_name = args.ring
    if ring_name:
        if ring_name not in RINGS:
            raise UsageError(f"unknown ring: {ring_name}")
        if ring_name == "grail":
            matching = [
                entry
                for entry in payload["entries"]
                if isinstance(entry, dict) and entry.get("name") == "rapp_brainstem/VERSION"
            ]
        else:
            matching = [
                entry
                for entry in payload["entries"]
                if isinstance(entry, dict) and entry.get("name") == f"rings/{ring_name}.json"
            ]
        if not matching:
            raise RemoteFailure(f"release train status does not contain ring {ring_name}")
        data = {"ring": ring_name, "entry": matching[0], "generated": payload.get("generated")}
        entry = matching[0]
        return Result(
            data,
            f"{ring_name}: {entry.get('primary_sha8')} | "
            f"{'drift' if entry.get('drift') else 'recorded'}",
        )

    summary = payload["summary"]
    return Result(
        payload,
        f"release train: {summary.get('entries')} entries | "
        f"{summary.get('drift')} drift | {summary.get('versions')} versions",
    )


def twin_hatch(ctx: Context, args: Any) -> Result:
    outcome = hatch_local_twin(
        ctx.client,
        args.folder,
        home=args.home or default_twins_home(),
        endpoint=ctx.config.brainstem_url,
        confirmed=args.yes,
    )
    return Result(outcome.to_dict(), outcome.message())


def twin_list(_ctx: Context, args: Any) -> Result:
    twins = list_twins(args.home, include_archived=args.all)
    data = [twin.to_dict() for twin in twins]
    lines = [f"{twin.id}: {twin.name or twin.rappid or 'unnamed'} [{twin.state}]" for twin in twins]
    legacy = args.twin_command.startswith("legacy-")
    return Result(
        {"legacy": legacy, "twins": data},
        "\n".join(lines)
        if lines
        else ("no legacy local twins found" if legacy else "no local twins found"),
    )


def twin_show(_ctx: Context, args: Any) -> Result:
    twin = show_twin(args.twin, args.home, include_archived=args.all)
    payload = twin.to_dict()
    lines = [
        f"id: {payload['id']}",
        f"name: {payload['name'] or ''}",
        f"rappid: {payload['rappid'] or ''}",
        f"state: {payload['state']}",
        f"path: {payload['path']}",
    ]
    return Result(payload, "\n".join(lines))


def invoke(handler: Any, ctx: Context, args: Any) -> int:
    result = handler(ctx, args)
    if result is not None:
        ctx.output.success(result.data, message=result.message)
    return 0


def normalize_message(parts: Sequence[str]) -> list[str]:
    return [part for part in parts if part]
