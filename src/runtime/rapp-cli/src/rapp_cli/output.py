from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, TextIO

from . import __version__
from .errors import RappError


def _jsonable(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _jsonable(asdict(value))
    if hasattr(value, "to_dict"):
        return _jsonable(value.to_dict())
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    return str(value)


def _terminal_safe(value: str) -> str:
    pieces = []
    for character in value:
        codepoint = ord(character)
        if character in {"\n", "\t"} or (codepoint >= 32 and codepoint != 127):
            pieces.append(character)
        elif codepoint <= 0xFF:
            pieces.append(f"\\x{codepoint:02x}")
        else:
            pieces.append(f"\\u{codepoint:04x}")
    return "".join(pieces)


class Output:
    def __init__(
        self,
        *,
        json_mode: bool = False,
        jsonl_mode: bool = False,
        quiet: bool = False,
        command: str | None = None,
        stdout: TextIO | None = None,
        stderr: TextIO | None = None,
    ) -> None:
        self.json_mode = json_mode
        self.jsonl_mode = jsonl_mode
        self.quiet = quiet
        self.command = command
        self.stdout = stdout or sys.stdout
        self.stderr = stderr or sys.stderr

    def success(self, data: Any, *, message: str | None = None) -> None:
        if self.json_mode:
            self._dump(
                {
                    "schema": "rapp-cli-result/1.0",
                    "ok": True,
                    "command": self.command,
                    "data": _jsonable(data),
                    "warnings": [],
                    "meta": {"cli_version": __version__},
                }
            )
            return
        if not self.quiet:
            if message is not None:
                print(_terminal_safe(message), file=self.stdout)
            elif isinstance(data, str):
                print(_terminal_safe(data), file=self.stdout)
            else:
                self._dump(_jsonable(data))

    def error(self, error: RappError) -> None:
        payload = {
            "schema": "rapp-cli-error/1.0",
            "ok": False,
            "command": self.command,
            "error": {
                "code": error.code,
                "message": error.message,
                "details": _jsonable(error.details),
            },
        }
        if self.json_mode:
            if self.jsonl_mode:
                print(
                    json.dumps(
                        payload,
                        ensure_ascii=False,
                        allow_nan=False,
                        separators=(",", ":"),
                    ),
                    file=self.stdout,
                )
            else:
                self._dump(payload, stream=self.stdout)
        else:
            print(f"error: {_terminal_safe(error.message)}", file=self.stderr)

    def stream_event(self, event: Any) -> None:
        if self.json_mode:
            print(
                json.dumps(
                    {
                        "schema": "rapp-cli-event/1.0",
                        "command": self.command,
                        "event": _jsonable(event),
                    },
                    ensure_ascii=False,
                    allow_nan=False,
                ),
                file=self.stdout,
                flush=True,
            )
            return
        if self.quiet:
            return
        if isinstance(event, str):
            print(_terminal_safe(event), end="", flush=True, file=self.stdout)
        else:
            self._dump(_jsonable(event))

    def diagnostic(self, message: str) -> None:
        print(_terminal_safe(message), file=self.stderr)

    def _dump(self, value: Any, *, stream: TextIO | None = None) -> None:
        print(
            json.dumps(
                value,
                ensure_ascii=False,
                allow_nan=False,
                indent=2,
                sort_keys=True,
            ),
            file=stream or self.stdout,
        )
