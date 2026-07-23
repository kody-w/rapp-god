from __future__ import annotations

import os
import re
import stat as stat_module
from pathlib import Path

from .errors import UsageError
from .filesystem import is_reparse_point

MAX_AGENT_BYTES = 16 * 1024 * 1024
MAX_AGENT_FILENAME_BYTES = 255
_AGENT_FILENAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*_agent\.py$")


def validate_agent_filename(value: str) -> str:
    if (
        type(value) is not str
        or not _AGENT_FILENAME_RE.fullmatch(value)
        or len(value.encode("ascii")) > MAX_AGENT_FILENAME_BYTES
    ):
        raise UsageError(
            "agent filename must be a basename ending in _agent.py "
            "of at most 255 ASCII bytes containing only letters, numbers, "
            "dot, underscore, or hyphen"
        )
    return value


def read_regular_file(
    source: Path,
    *,
    max_bytes: int,
    description: str,
    limit_description: str,
) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        source_info = os.lstat(source)
        if stat_module.S_ISLNK(source_info.st_mode) or is_reparse_point(source):
            raise UsageError(
                f"cannot open {description} {source}: symlinks and reparse points are not allowed"
            )
        if not stat_module.S_ISREG(source_info.st_mode):
            raise UsageError(f"{description} must be a regular file: {source}")
        fd = os.open(source, flags)
    except UsageError:
        raise
    except OSError as exc:
        raise UsageError(f"cannot open {description} {source}: {exc}") from exc
    with os.fdopen(fd, "rb") as handle:
        info = os.fstat(handle.fileno())
        if (
            not stat_module.S_ISREG(info.st_mode)
            or info.st_dev != source_info.st_dev
            or info.st_ino != source_info.st_ino
        ):
            raise UsageError(f"{description} must be a regular file: {source}")
        if info.st_size > max_bytes:
            raise UsageError(f"{description} exceeds {limit_description}: {source}")
        payload = handle.read(max_bytes + 1)
    if len(payload) > max_bytes:
        raise UsageError(f"{description} exceeds {limit_description}: {source}")
    return payload


def read_agent_source(source: Path) -> bytes:
    return read_regular_file(
        source,
        max_bytes=MAX_AGENT_BYTES,
        description="agent file",
        limit_description="the Brainstem 16 MiB upload limit",
    )
