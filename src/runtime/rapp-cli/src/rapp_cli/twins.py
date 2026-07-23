from __future__ import annotations

import os
import re
import stat as stat_module
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from .errors import NotFound, UsageError
from .filesystem import is_reparse_point
from .identity import is_canonical_rappid
from .jsonio import DuplicateKeyError, NonFiniteNumberError, loads

_TWIN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:@-]{0,255}$")
_MAX_METADATA_BYTES = 1024 * 1024


@dataclass(frozen=True, slots=True)
class Twin:
    id: str
    path: Path
    state: str
    rappid: str | None = None
    name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "path": str(self.path),
            "state": self.state,
            "rappid": self.rappid,
            "name": self.name,
        }


def default_twins_home() -> Path:
    configured = os.environ.get("RAPP_TWINS_HOME")
    return Path(configured).expanduser() if configured else Path.home() / ".rapp" / "twins"


def _metadata(path: Path) -> dict[str, Any]:
    for name in ("rappid.json", "manifest.json"):
        candidate = path / name
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        try:
            if is_reparse_point(candidate):
                continue
            fd = os.open(candidate, flags)
        except OSError:
            continue
        try:
            with os.fdopen(fd, "rb") as handle:
                info = os.fstat(handle.fileno())
                if not stat_module.S_ISREG(info.st_mode) or info.st_size > _MAX_METADATA_BYTES:
                    continue
                raw = handle.read(_MAX_METADATA_BYTES + 1)
            if len(raw) > _MAX_METADATA_BYTES:
                continue
            value = loads(raw.decode("utf-8"))
        except (
            OSError,
            UnicodeDecodeError,
            JSONDecodeError,
            DuplicateKeyError,
            NonFiniteNumberError,
        ):
            continue
        if isinstance(value, dict):
            return value
    return {}


def _twin(path: Path, state: str) -> Twin:
    metadata = _metadata(path)
    rappid = metadata.get("rappid") or metadata.get("id") or metadata.get("rappid_uuid")
    name = metadata.get("name") or metadata.get("display_name")
    return Twin(
        id=path.name,
        path=path,
        state=state,
        rappid=rappid if isinstance(rappid, str) else None,
        name=name if isinstance(name, str) else None,
    )


def list_twins(
    home: str | Path | None = None,
    *,
    include_archived: bool = False,
) -> list[Twin]:
    root = Path(home).expanduser() if home else default_twins_home()
    try:
        root_info = root.lstat()
    except FileNotFoundError:
        return []
    except OSError as exc:
        raise UsageError(f"cannot inspect twin home {root}: {exc}") from exc
    if (
        not stat_module.S_ISDIR(root_info.st_mode)
        or stat_module.S_ISLNK(root_info.st_mode)
        or is_reparse_point(root)
    ):
        raise UsageError(f"twin home must be a real directory: {root}")

    try:
        entries = sorted(root.iterdir(), key=lambda item: item.name)
    except OSError as exc:
        raise UsageError(f"cannot read twin home {root}: {exc}") from exc
    twins = [
        _twin(path, "active")
        for path in entries
        if path.is_dir() and not path.is_symlink() and not path.name.startswith(".")
    ]
    if include_archived:
        for directory, state in ((".archive", "archived"), (".purged", "purged")):
            state_root = root / directory
            if not state_root.is_dir() or state_root.is_symlink():
                continue
            try:
                state_entries = sorted(state_root.iterdir(), key=lambda item: item.name)
            except OSError:
                continue
            twins.extend(
                _twin(path, state)
                for path in state_entries
                if path.is_dir() and not path.is_symlink()
            )
    return twins


def show_twin(
    twin_id: str,
    home: str | Path | None = None,
    *,
    include_archived: bool = False,
) -> Twin:
    if not (_TWIN_ID_RE.fullmatch(twin_id) or is_canonical_rappid(twin_id)):
        raise UsageError("twin id contains unsupported characters")
    for twin in list_twins(home, include_archived=include_archived):
        if twin.id == twin_id or twin.rappid == twin_id:
            return twin
    raise NotFound(f"twin not found: {twin_id}")
