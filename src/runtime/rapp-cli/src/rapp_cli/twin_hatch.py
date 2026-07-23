from __future__ import annotations

import contextlib
import ctypes
import errno
import hashlib
import hmac
import json
import os
import shutil
import stat as stat_module
import sys
import tempfile
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path, PureWindowsPath
from typing import Any, Protocol

from .agent_files import read_regular_file, validate_agent_filename
from .errors import (
    CapabilityUnavailable,
    ConfirmationRequired,
    Conflict,
    IntegrityFailure,
    RemoteFailure,
    UsageError,
)
from .filesystem import is_reparse_point
from .identity import parse_rappid
from .jsonio import DuplicateKeyError, NonFiniteNumberError, loads
from .provider import require_provider_object, require_provider_success

MAX_TWIN_FILES = 4096
MAX_TWIN_DIRECTORIES = 4096
MAX_TWIN_FILE_BYTES = 16 * 1024 * 1024
MAX_TWIN_TOTAL_BYTES = 256 * 1024 * 1024
MAX_TWIN_RECEIPT_BYTES = 2 * 1024 * 1024
HATCH_CONFIRMATION_MESSAGE = (
    "twin hatch copies and registers executable agent Python and requires --yes"
)
_FORBIDDEN_NAMES = frozenset({".lineage_key", ".copilot_token", ".env"})
_UNSUPPORTED_FSYNC_ERRORS = frozenset(
    value
    for value in (
        getattr(errno, "EINVAL", None),
        getattr(errno, "ENOTSUP", None),
        getattr(errno, "EOPNOTSUPP", None),
        getattr(errno, "EROFS", None),
    )
    if value is not None
)


class HatchClient(Protocol):
    def get_json(self, path: str) -> Any: ...

    def export_agent(self, filename: str) -> bytes: ...

    def import_agent(
        self,
        filename: str,
        payload: bytes,
        *,
        sha256: str | None = None,
        source_revision: str | None = None,
    ) -> Any: ...


@dataclass(frozen=True, slots=True)
class TreeEntry:
    relative_path: str
    data: bytes | None

    @property
    def is_directory(self) -> bool:
        return self.data is None


@dataclass(frozen=True, slots=True)
class TwinAgent:
    filename: str
    payload: bytes
    sha256: str


@dataclass(frozen=True, slots=True)
class ProviderAgentFile:
    filename: str
    loaded_agents: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PreparedTwin:
    source: Path
    rappid: str
    kind: str
    identity_hash: str
    tree_sha256: str
    entries: tuple[TreeEntry, ...]
    agents: tuple[TwinAgent, ...]
    file_count: int
    total_bytes: int


@dataclass(frozen=True, slots=True)
class AgentStatus:
    filename: str
    sha256: str
    status: str

    def to_dict(self) -> dict[str, str]:
        return {
            "filename": self.filename,
            "sha256": self.sha256,
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class HatchOutcome:
    rappid: str
    kind: str
    twin_id: str
    path: Path
    source_sha256: str
    materialization: str
    endpoint: str
    agents: tuple[AgentStatus, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "rapp-twin-hatch/1.0",
            "rappid": self.rappid,
            "kind": self.kind,
            "id": self.twin_id,
            "path": str(self.path),
            "source_sha256": self.source_sha256,
            "materialization": self.materialization,
            "endpoint": self.endpoint,
            "agents": [agent.to_dict() for agent in self.agents],
            "runtime_activation": "next_request",
        }

    def message(self) -> str:
        agent_lines = [f"{agent.filename}: {agent.status}" for agent in self.agents]
        return "\n".join(
            [
                f"hatched {self.rappid} at {self.path}",
                f"Brainstem: {self.endpoint}",
                *agent_lines,
                "agents hot-load on the next request; no restart required",
            ]
        )


def prepare_twin(folder: str | Path) -> PreparedTwin:
    source = Path(folder).expanduser()
    source_fd, resolved_source, source_info = _open_source_root(source)
    entries: list[TreeEntry] = []
    file_count = 0
    directory_count = 0
    total_bytes = 0

    def walk(
        directory_fd: int,
        parents: tuple[str, ...],
        opened_directory_info: os.stat_result,
    ) -> None:
        nonlocal directory_count, file_count, total_bytes
        relative_directory = "/".join(parents)
        try:
            before = os.fstat(directory_fd)
            with os.scandir(directory_fd) as iterator:
                children = [
                    (
                        _relative_component(child.name),
                        child.stat(follow_symlinks=False),
                    )
                    for child in iterator
                ]
        except OSError as exc:
            label = relative_directory or "."
            raise UsageError(f"cannot read twin directory {label}: {exc}") from exc
        _require_same_inode(before, opened_directory_info, relative_directory or ".")
        children.sort(key=lambda item: item[0])
        _after_directory_enumeration(relative_directory)
        for name, enumerated_info in children:
            relative_parts = (*parents, name)
            relative_path = "/".join(relative_parts)
            _reject_forbidden_path(relative_parts, relative_path)
            if stat_module.S_ISLNK(enumerated_info.st_mode):
                raise IntegrityFailure(
                    f"twin path must not be a symlink or reparse point: {relative_path}"
                )
            child_fd, opened_info = _open_child_no_follow(
                directory_fd,
                name,
                enumerated_info,
                relative_path,
            )
            if stat_module.S_ISDIR(opened_info.st_mode):
                directory_count += 1
                if directory_count > MAX_TWIN_DIRECTORIES:
                    os.close(child_fd)
                    raise UsageError(f"twin exceeds the {MAX_TWIN_DIRECTORIES} directory limit")
                entries.append(TreeEntry(relative_path, None))
                try:
                    walk(child_fd, relative_parts, opened_info)
                finally:
                    os.close(child_fd)
                continue
            if not stat_module.S_ISREG(opened_info.st_mode):
                os.close(child_fd)
                raise IntegrityFailure(
                    f"twin path must be a regular file or directory: {relative_path}"
                )
            file_count += 1
            if file_count > MAX_TWIN_FILES:
                os.close(child_fd)
                raise UsageError(f"twin exceeds the {MAX_TWIN_FILES} file limit")
            payload = _read_open_file(child_fd, opened_info, relative_path)
            total_bytes += len(payload)
            if total_bytes > MAX_TWIN_TOTAL_BYTES:
                raise UsageError(
                    f"twin exceeds the {MAX_TWIN_TOTAL_BYTES} byte total payload limit"
                )
            entries.append(TreeEntry(relative_path, payload))
        after = os.fstat(directory_fd)
        _require_unchanged_directory(before, after, relative_directory or ".")

    try:
        walk(source_fd, (), source_info)
    finally:
        os.close(source_fd)
    entries.sort(key=lambda entry: entry.relative_path)
    files = {
        entry.relative_path: entry.data
        for entry in entries
        if not entry.is_directory and entry.data is not None
    }
    directories = {entry.relative_path for entry in entries if entry.is_directory}
    metadata = _metadata(files.get("rappid.json"))
    _validate_soul(files.get("soul.md"))
    if "agents" not in directories:
        raise UsageError("twin folder requires a root agents/ directory")
    agents = _agents(files)
    if not agents:
        raise UsageError(
            "twin folder requires at least one immediate regular agents/*_agent.py file"
        )
    tree_sha256 = _tree_digest(entries)
    return PreparedTwin(
        source=resolved_source,
        rappid=metadata["rappid"],
        kind=metadata["kind"],
        identity_hash=metadata["identity_hash"],
        tree_sha256=tree_sha256,
        entries=tuple(entries),
        agents=tuple(agents),
        file_count=file_count,
        total_bytes=total_bytes,
    )


def hatch_twin(
    client: HatchClient,
    folder: str | Path,
    *,
    home: str | Path,
    endpoint: str,
    confirmed: bool,
) -> HatchOutcome:
    if not confirmed:
        raise ConfirmationRequired(HATCH_CONFIRMATION_MESSAGE)
    prepared = prepare_twin(folder)
    receipt_payload = _receipt_payload(prepared)
    twins_home = Path(home).expanduser()
    _validate_source_home_separation(
        prepared.source,
        twins_home,
        prepared.identity_hash,
    )
    _ensure_twins_home(twins_home)
    target = twins_home / prepared.identity_hash
    with _identity_lock(twins_home, prepared.identity_hash):
        initial_materialization = _target_materialization(target, prepared.tree_sha256)
        stage: Path | None = None
        try:
            if initial_materialization == "absent":
                stage = _stage_tree(twins_home, prepared)
                materialization = _install_or_verify(
                    stage,
                    target,
                    prepared.tree_sha256,
                    twins_home,
                )
            else:
                _verify_target(target, prepared.tree_sha256)
                materialization = "existing"
            _write_receipt(twins_home, prepared, receipt_payload)
            statuses = _register_agents(client, prepared.agents)
            return HatchOutcome(
                rappid=prepared.rappid,
                kind=prepared.kind,
                twin_id=prepared.identity_hash,
                path=target,
                source_sha256=prepared.tree_sha256,
                materialization=materialization,
                endpoint=endpoint,
                agents=statuses,
            )
        finally:
            if stage is not None:
                with contextlib.suppress(OSError):
                    _remove_path(stage)


def _secure_walk_supported() -> bool:
    return (
        os.name == "posix"
        and bool(getattr(os, "O_NOFOLLOW", 0))
        and bool(getattr(os, "O_DIRECTORY", 0))
        and os.open in os.supports_dir_fd
        and os.scandir in os.supports_fd
    )


def _open_source_root(source: Path) -> tuple[int, Path, os.stat_result]:
    if not _secure_walk_supported():
        raise CapabilityUnavailable(
            "secure no-follow Twin traversal is unavailable on this platform; hatch fails closed"
        )
    try:
        resolved = source.resolve(strict=True)
        path_info = source.lstat()
        reparse = is_reparse_point(source)
    except FileNotFoundError as exc:
        raise UsageError(f"twin source does not exist: {source}") from exc
    except OSError as exc:
        raise UsageError(f"cannot inspect twin source {source}: {exc}") from exc
    if (
        not stat_module.S_ISDIR(path_info.st_mode)
        or stat_module.S_ISLNK(path_info.st_mode)
        or reparse
    ):
        raise IntegrityFailure(f"twin source must be a real non-symlink directory: {source}")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(source, flags)
    except OSError as exc:
        raise IntegrityFailure(
            f"twin source changed or became unsafe while opening: {source}"
        ) from exc
    try:
        opened_info = os.fstat(descriptor)
        _require_same_inode(path_info, opened_info, ".")
        if not stat_module.S_ISDIR(opened_info.st_mode):
            raise IntegrityFailure(f"twin source must be a directory: {source}")
    except IntegrityFailure:
        os.close(descriptor)
        raise
    except OSError as exc:
        os.close(descriptor)
        raise UsageError(f"cannot verify opened twin source {source}: {exc}") from exc
    return descriptor, resolved, opened_info


def _open_child_no_follow(
    parent_fd: int,
    name: str,
    enumerated_info: os.stat_result,
    relative_path: str,
) -> tuple[int, os.stat_result]:
    expected_directory = stat_module.S_ISDIR(enumerated_info.st_mode)
    expected_file = stat_module.S_ISREG(enumerated_info.st_mode)
    if not expected_directory and not expected_file:
        raise IntegrityFailure(f"twin path must be a regular file or directory: {relative_path}")
    flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NONBLOCK", 0)
    if expected_directory:
        flags |= os.O_DIRECTORY
    try:
        descriptor = os.open(name, flags, dir_fd=parent_fd)
    except OSError as exc:
        if exc.errno in {
            errno.ELOOP,
            errno.ENOTDIR,
            getattr(errno, "EMLINK", errno.ELOOP),
        }:
            raise IntegrityFailure(
                f"twin path changed or became a symlink/reparse point: {relative_path}"
            ) from exc
        raise UsageError(f"cannot safely open twin path {relative_path}: {exc}") from exc
    try:
        opened_info = os.fstat(descriptor)
        _require_same_inode(enumerated_info, opened_info, relative_path)
        if expected_directory != stat_module.S_ISDIR(opened_info.st_mode):
            raise IntegrityFailure(f"twin path changed while opening: {relative_path}")
        if expected_file != stat_module.S_ISREG(opened_info.st_mode):
            raise IntegrityFailure(f"twin path changed while opening: {relative_path}")
    except IntegrityFailure:
        os.close(descriptor)
        raise
    except OSError as exc:
        os.close(descriptor)
        raise UsageError(f"cannot verify twin path {relative_path}: {exc}") from exc
    return descriptor, opened_info


def _read_open_file(
    descriptor: int,
    opened_info: os.stat_result,
    relative_path: str,
) -> bytes:
    if opened_info.st_size > MAX_TWIN_FILE_BYTES:
        os.close(descriptor)
        raise UsageError(
            f"twin file {relative_path} exceeds the {MAX_TWIN_FILE_BYTES} byte per-file limit"
        )
    try:
        with os.fdopen(descriptor, "rb") as handle:
            payload = handle.read(MAX_TWIN_FILE_BYTES + 1)
            after = os.fstat(handle.fileno())
    except OSError as exc:
        raise UsageError(f"cannot read twin file {relative_path}: {exc}") from exc
    if len(payload) > MAX_TWIN_FILE_BYTES:
        raise UsageError(
            f"twin file {relative_path} exceeds the {MAX_TWIN_FILE_BYTES} byte per-file limit"
        )
    _require_same_inode(opened_info, after, relative_path)
    if (
        opened_info.st_size != after.st_size
        or opened_info.st_mtime_ns != after.st_mtime_ns
        or opened_info.st_ctime_ns != after.st_ctime_ns
        or len(payload) != after.st_size
    ):
        raise IntegrityFailure(f"twin file changed while reading: {relative_path}")
    return payload


def _require_same_inode(
    expected: os.stat_result,
    actual: os.stat_result,
    relative_path: str,
) -> None:
    if expected.st_dev != actual.st_dev or expected.st_ino != actual.st_ino:
        raise IntegrityFailure(f"twin path changed while scanning: {relative_path}")


def _require_unchanged_directory(
    before: os.stat_result,
    after: os.stat_result,
    relative_path: str,
) -> None:
    _require_same_inode(before, after, relative_path)
    if before.st_mtime_ns != after.st_mtime_ns or before.st_ctime_ns != after.st_ctime_ns:
        raise IntegrityFailure(f"twin directory changed while scanning: {relative_path}")


def _after_directory_enumeration(_relative_path: str) -> None:
    return None


def _resolve_for_overlap(path: Path, description: str) -> Path:
    try:
        return path.resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        raise UsageError(f"cannot resolve {description} {path}: {exc}") from exc


def _paths_overlap(first: Path, second: Path) -> bool:
    return first == second or first.is_relative_to(second) or second.is_relative_to(first)


def _nearest_existing_path(
    path: Path,
    description: str,
) -> tuple[Path, bool]:
    candidate = path
    has_missing_descendants = False
    while True:
        try:
            candidate.stat()
        except (FileNotFoundError, NotADirectoryError):
            parent = candidate.parent
            if parent == candidate:
                raise UsageError(
                    f"cannot find an existing ancestor for {description} {path}"
                ) from None
            candidate = parent
            has_missing_descendants = True
            continue
        except OSError as exc:
            raise UsageError(f"cannot inspect {description} {candidate}: {exc}") from exc
        return candidate, has_missing_descendants


def _path_identity(path: Path, description: str) -> tuple[int, int]:
    try:
        info = path.stat()
    except OSError as exc:
        raise UsageError(f"cannot inspect {description} {path}: {exc}") from exc
    return info.st_dev, info.st_ino


def _ancestor_identities(path: Path, description: str) -> set[tuple[int, int]]:
    identities: set[tuple[int, int]] = set()
    current = path
    while True:
        identities.add(_path_identity(current, description))
        parent = current.parent
        if parent == current:
            return identities
        current = parent


def _identity_paths_overlap(
    source: Path,
    candidate: Path,
    description: str,
) -> bool:
    source_identity = _path_identity(source, "twin source")
    source_ancestors = _ancestor_identities(source, "twin source")
    existing_candidate, has_missing_descendants = _nearest_existing_path(
        candidate,
        description,
    )
    candidate_ancestors = _ancestor_identities(existing_candidate, description)
    if source_identity in candidate_ancestors:
        return True
    if not has_missing_descendants:
        candidate_identity = _path_identity(existing_candidate, description)
        if candidate_identity in source_ancestors:
            return True
    return False


def _validate_source_home_separation(
    source: Path,
    home: Path,
    identity_hash: str,
) -> None:
    resolved_source = _resolve_for_overlap(source, "twin source")
    resolved_home = _resolve_for_overlap(home, "twin home")
    resolved_target = _resolve_for_overlap(home / identity_hash, "twin target")
    for description, candidate in (
        ("twin home", resolved_home),
        ("twin target", resolved_target),
    ):
        if _paths_overlap(resolved_source, candidate) or _identity_paths_overlap(
            resolved_source,
            candidate,
            description,
        ):
            raise UsageError(f"twin source and {description} must not contain one another")


def _ensure_control_directory(home: Path, name: str) -> Path:
    directory = home / name
    try:
        directory.mkdir(mode=0o700)
    except FileExistsError:
        pass
    except OSError as exc:
        raise UsageError(f"cannot create Twin control directory {directory}: {exc}") from exc
    try:
        info = directory.lstat()
        reparse = is_reparse_point(directory)
    except OSError as exc:
        raise UsageError(f"cannot inspect Twin control directory {directory}: {exc}") from exc
    if not stat_module.S_ISDIR(info.st_mode) or stat_module.S_ISLNK(info.st_mode) or reparse:
        raise IntegrityFailure(
            f"Twin control path must be a real non-symlink directory: {directory}"
        )
    return directory


@contextlib.contextmanager
def _identity_lock(home: Path, identity_hash: str) -> Iterator[None]:
    if os.name != "posix":
        raise CapabilityUnavailable(
            "secure advisory Twin hatch locking is unavailable on this platform"
        )
    import fcntl

    locks = _ensure_control_directory(home, ".locks")
    lock_path = locks / f"{identity_hash}.lock"
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(lock_path, flags, 0o600)
    except OSError as exc:
        raise UsageError(f"cannot open Twin hatch lock {lock_path}: {exc}") from exc
    try:
        info = os.fstat(descriptor)
    except OSError as exc:
        os.close(descriptor)
        raise UsageError(f"cannot verify Twin hatch lock {lock_path}: {exc}") from exc
    if not stat_module.S_ISREG(info.st_mode):
        os.close(descriptor)
        raise IntegrityFailure(f"Twin hatch lock must be a regular file: {lock_path}")
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise Conflict(
                f"another rapp-cli hatch is already running for {identity_hash}"
            ) from exc
        _fsync_directory(locks)
        try:
            yield
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
    finally:
        os.close(descriptor)


def _relative_component(name: str) -> str:
    try:
        name.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise IntegrityFailure("twin path names must be valid UTF-8") from exc
    windows_name = PureWindowsPath(name)
    if (
        not name
        or name in {".", ".."}
        or "/" in name
        or "\\" in name
        or "\x00" in name
        or windows_name.is_absolute()
        or bool(windows_name.drive)
    ):
        raise IntegrityFailure(f"twin contains a traversal-like path component: {name!r}")
    return name


def _reject_forbidden_path(parts: tuple[str, ...], relative_path: str) -> None:
    folded = tuple(part.casefold() for part in parts)
    if any(part in _FORBIDDEN_NAMES for part in folded) or "private" in folded:
        raise IntegrityFailure(f"twin contains forbidden secret path: {relative_path}")


def _metadata(raw: bytes | None) -> dict[str, str]:
    if raw is None:
        raise UsageError("twin folder requires root rappid.json")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UsageError("rappid.json must be UTF-8 text") from exc
    try:
        payload = loads(text)
    except DuplicateKeyError as exc:
        raise UsageError(f"rappid.json has duplicate fields: {exc}") from exc
    except NonFiniteNumberError as exc:
        raise UsageError(f"rappid.json contains {exc}") from exc
    except JSONDecodeError as exc:
        raise UsageError(
            "rappid.json is not valid JSON",
            details={"line": exc.lineno, "column": exc.colno},
        ) from exc
    if not isinstance(payload, dict):
        raise UsageError("rappid.json must contain a JSON object")
    if payload.get("schema") != "rapp/1":
        raise UsageError('rappid.json schema must be exactly "rapp/1"')
    kind = payload.get("kind")
    if kind not in {"twin", "organism"}:
        raise UsageError('rappid.json kind must be "twin" or "organism"')
    rappid = payload.get("rappid")
    if not isinstance(rappid, str):
        raise UsageError("rappid.json rappid must be a string")
    try:
        identity = parse_rappid(rappid)
    except UsageError as exc:
        raise UsageError(
            "rappid.json rappid must be canonical "
            "rappid:@owner/slug:<64 lowercase hexadecimal characters>: "
            f"{exc}"
        ) from exc
    for field in ("name", "display_name"):
        if field in payload and not isinstance(payload[field], str):
            raise UsageError(f"rappid.json {field} must be a string when present")
    return {
        "rappid": rappid,
        "kind": kind,
        "identity_hash": identity.tail,
    }


def _validate_soul(raw: bytes | None) -> None:
    if raw is None:
        raise UsageError("twin folder requires root soul.md")
    try:
        soul = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UsageError("soul.md must be UTF-8 text") from exc
    if not soul.lstrip("\ufeff").strip():
        raise UsageError("soul.md must contain non-whitespace UTF-8 text")


def _agents(files: Mapping[str, bytes]) -> list[TwinAgent]:
    agents: list[TwinAgent] = []
    casefolded: dict[str, str] = {}
    for relative_path, payload in sorted(files.items()):
        parts = relative_path.split("/")
        if len(parts) != 2 or parts[0] != "agents" or not parts[1].endswith("_agent.py"):
            continue
        filename = validate_agent_filename(parts[1])
        folded = filename.casefold()
        previous = casefolded.get(folded)
        if previous is not None:
            raise UsageError(
                f"twin contains case-insensitive duplicate agent filenames: {previous}, {filename}"
            )
        casefolded[folded] = filename
        agents.append(
            TwinAgent(
                filename=filename,
                payload=payload,
                sha256=hashlib.sha256(payload).hexdigest(),
            )
        )
    return agents


def _tree_digest(entries: list[TreeEntry] | tuple[TreeEntry, ...]) -> str:
    digest = hashlib.sha256()
    for entry in sorted(entries, key=lambda item: item.relative_path):
        path = entry.relative_path.encode("utf-8")
        digest.update(b"D" if entry.is_directory else b"F")
        digest.update(len(path).to_bytes(8, "big"))
        digest.update(path)
        if entry.data is not None:
            digest.update(len(entry.data).to_bytes(8, "big"))
            digest.update(entry.data)
    return digest.hexdigest()


def _ensure_twins_home(home: Path) -> None:
    try:
        home.lstat()
    except FileNotFoundError:
        try:
            home.mkdir(mode=0o700, parents=True)
        except FileExistsError:
            pass
        except OSError as exc:
            raise UsageError(f"cannot create twin home {home}: {exc}") from exc
    except OSError as exc:
        raise UsageError(f"cannot inspect twin home {home}: {exc}") from exc
    try:
        info = home.lstat()
        reparse = is_reparse_point(home)
    except OSError as exc:
        raise UsageError(f"cannot inspect twin home {home}: {exc}") from exc
    if not stat_module.S_ISDIR(info.st_mode) or stat_module.S_ISLNK(info.st_mode) or reparse:
        raise IntegrityFailure(f"twin home must be a real non-symlink directory: {home}")


def _target_materialization(target: Path, expected_digest: str) -> str:
    try:
        target.lstat()
    except FileNotFoundError:
        return "absent"
    except OSError as exc:
        raise UsageError(f"cannot inspect twin target {target}: {exc}") from exc
    _verify_target(target, expected_digest)
    return "existing"


def _verify_target(target: Path, expected_digest: str) -> None:
    try:
        existing = prepare_twin(target)
    except (IntegrityFailure, UsageError) as exc:
        raise Conflict(f"existing twin target is not an identical safe tree: {target}") from exc
    if not hmac.compare_digest(existing.tree_sha256, expected_digest):
        raise Conflict(
            f"existing twin target differs from the source: {target}",
            details={
                "expected_sha256": expected_digest,
                "actual_sha256": existing.tree_sha256,
            },
        )


def _stage_tree(home: Path, prepared: PreparedTwin) -> Path:
    try:
        stage = Path(
            tempfile.mkdtemp(
                prefix=f".hatch-{prepared.identity_hash[:12]}-",
                dir=home,
            )
        )
    except OSError as exc:
        raise UsageError(f"cannot create twin staging directory in {home}: {exc}") from exc
    completed = False
    try:
        directories = [entry for entry in prepared.entries if entry.is_directory]
        for entry in sorted(
            directories,
            key=lambda item: (item.relative_path.count("/"), item.relative_path),
        ):
            (stage / Path(*entry.relative_path.split("/"))).mkdir(mode=0o700)
        for entry in prepared.entries:
            if entry.data is None:
                continue
            destination = stage / Path(*entry.relative_path.split("/"))
            flags = (
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | getattr(os, "O_BINARY", 0)
                | getattr(os, "O_NOFOLLOW", 0)
            )
            fd = os.open(destination, flags, 0o600)
            with os.fdopen(fd, "wb") as handle:
                handle.write(entry.data)
                handle.flush()
                os.fsync(handle.fileno())
        for entry in sorted(
            directories,
            key=lambda item: (item.relative_path.count("/"), item.relative_path),
            reverse=True,
        ):
            _fsync_directory(stage / Path(*entry.relative_path.split("/")))
        _fsync_directory(stage)
        _fsync_directory(home)
        completed = True
        return stage
    except OSError as exc:
        raise UsageError(f"cannot stage twin in {home}: {exc}") from exc
    finally:
        if not completed:
            with contextlib.suppress(OSError):
                _remove_path(stage)


def _listed_agent_files(client: HatchClient) -> dict[str, ProviderAgentFile]:
    payload = require_provider_object(client.get_json("/agents"), "agents list")
    files = payload.get("files")
    if not isinstance(files, list):
        raise RemoteFailure("Brainstem agents response is missing a files array")
    entries: dict[str, ProviderAgentFile] = {}
    for item in files:
        if not isinstance(item, dict):
            raise RemoteFailure("Brainstem agents response contains a non-object file entry")
        filename = item.get("filename")
        if (
            not isinstance(filename, str)
            or not filename
            or Path(filename).name != filename
            or "/" in filename
            or "\\" in filename
        ):
            raise RemoteFailure("Brainstem agents response contains an invalid filename")
        loaded = item.get("agents")
        if not isinstance(loaded, list):
            raise RemoteFailure(
                f"Brainstem agents response for {filename} is missing an agents array"
            )
        loaded_agents: list[str] = []
        for loaded_name in loaded:
            if not isinstance(loaded_name, str) or not loaded_name.strip():
                raise RemoteFailure(
                    f"Brainstem agents response for {filename} contains "
                    "an invalid loaded-agent name"
                )
            loaded_agents.append(loaded_name)
        folded = filename.casefold()
        if folded in entries:
            raise RemoteFailure(
                "Brainstem agents response contains case-insensitive duplicate filenames"
            )
        entries[folded] = ProviderAgentFile(
            filename=filename,
            loaded_agents=tuple(loaded_agents),
        )
    return entries


def _require_loaded_agent(entry: ProviderAgentFile) -> None:
    if not entry.loaded_agents:
        raise RemoteFailure(
            f"Brainstem agent file exists but reports no loaded agents: {entry.filename}",
            details={"filename": entry.filename},
        )


def _matching_provider_entry(
    entries: Mapping[str, ProviderAgentFile],
    filename: str,
) -> ProviderAgentFile | None:
    entry = entries.get(filename.casefold())
    if entry is not None and entry.filename != filename:
        raise Conflict(
            "Brainstem contains a case-only agent filename collision: "
            f"{entry.filename} conflicts with {filename}",
            details={
                "existing_filename": entry.filename,
                "incoming_filename": filename,
            },
        )
    return entry


def _register_agents(
    client: HatchClient,
    agents: tuple[TwinAgent, ...],
) -> tuple[AgentStatus, ...]:
    existing_files = _listed_agent_files(client)
    statuses: dict[str, AgentStatus] = {}
    missing: list[TwinAgent] = []
    for agent in agents:
        existing = _matching_provider_entry(existing_files, agent.filename)
        if existing is None:
            missing.append(agent)
            continue
        exported = client.export_agent(existing.filename)
        if not isinstance(exported, bytes):
            raise RemoteFailure("Brainstem agent export response must be bytes")
        actual = hashlib.sha256(exported).hexdigest()
        if not hmac.compare_digest(actual, agent.sha256):
            raise Conflict(
                f"Brainstem agent filename already contains different source: {agent.filename}",
                details={
                    "filename": agent.filename,
                    "expected_sha256": agent.sha256,
                    "actual_sha256": actual,
                },
            )
        _require_loaded_agent(existing)
        statuses[agent.filename] = AgentStatus(
            filename=agent.filename,
            sha256=agent.sha256,
            status="existing",
        )
    for agent in missing:
        response = client.import_agent(
            agent.filename,
            agent.payload,
            sha256=agent.sha256,
            source_revision=None,
        )
        require_provider_success(response, "agent import")
        exported = client.export_agent(agent.filename)
        if not isinstance(exported, bytes):
            raise RemoteFailure("Brainstem post-import agent export response must be bytes")
        actual = hashlib.sha256(exported).hexdigest()
        if not hmac.compare_digest(actual, agent.sha256):
            raise Conflict(
                f"Brainstem agent changed during import verification: {agent.filename}",
                details={
                    "filename": agent.filename,
                    "expected_sha256": agent.sha256,
                    "actual_sha256": actual,
                },
            )
        refreshed = _listed_agent_files(client)
        imported_entry = _matching_provider_entry(refreshed, agent.filename)
        if imported_entry is None:
            raise RemoteFailure(
                f"Brainstem agents response is missing imported file: {agent.filename}"
            )
        _require_loaded_agent(imported_entry)
        statuses[agent.filename] = AgentStatus(
            filename=agent.filename,
            sha256=agent.sha256,
            status="imported",
        )
    return tuple(statuses[agent.filename] for agent in agents)


def _receipt_payload(prepared: PreparedTwin) -> bytes:
    payload = {
        "schema": "rapp-cli-twin-hatch-receipt/1.0",
        "scope": "local_materialization",
        "provider_registration": "not_recorded",
        "rappid": prepared.rappid,
        "kind": prepared.kind,
        "twin_id": prepared.identity_hash,
        "source_sha256": prepared.tree_sha256,
        "agents": [
            {"filename": agent.filename, "sha256": agent.sha256} for agent in prepared.agents
        ],
    }
    encoded = (
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )
    if len(encoded) > MAX_TWIN_RECEIPT_BYTES:
        raise UsageError(f"generated Twin receipt exceeds the {MAX_TWIN_RECEIPT_BYTES} byte limit")
    return encoded


def _write_receipt(home: Path, prepared: PreparedTwin, payload: bytes) -> None:
    receipts = _ensure_control_directory(home, ".receipts")
    receipt = receipts / f"{prepared.tree_sha256}.json"
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_BINARY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        fd = os.open(receipt, flags, 0o600)
    except FileExistsError:
        existing = read_regular_file(
            receipt,
            max_bytes=MAX_TWIN_RECEIPT_BYTES,
            description="twin receipt",
            limit_description=f"the {MAX_TWIN_RECEIPT_BYTES} byte receipt limit",
        )
        if not hmac.compare_digest(existing, payload):
            raise Conflict(f"existing twin receipt differs: {receipt}") from None
        return
    except OSError as exc:
        raise UsageError(f"cannot create twin receipt {receipt}: {exc}") from exc
    completed = False
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        _fsync_directory(receipts)
        _fsync_directory(home)
        completed = True
        return
    except OSError as exc:
        raise UsageError(f"cannot write twin receipt {receipt}: {exc}") from exc
    finally:
        if not completed:
            with contextlib.suppress(OSError):
                receipt.unlink()


def _install_or_verify(
    stage: Path,
    target: Path,
    expected_digest: str,
    home: Path,
) -> str:
    renamed = False
    completed = False
    try:
        try:
            _rename_no_replace(stage, target)
            renamed = True
        except FileExistsError:
            _verify_target(target, expected_digest)
            completed = True
            return "existing"
        _fsync_directory(home)
        completed = True
        return "created"
    except OSError as exc:
        raise UsageError(f"cannot atomically install twin at {target}: {exc}") from exc
    finally:
        if renamed and not completed:
            with contextlib.suppress(OSError):
                _remove_path(target)


def _rename_no_replace(source: Path, target: Path) -> None:
    if os.name == "nt":
        os.rename(source, target)
        return
    libc = ctypes.CDLL(None, use_errno=True)
    source_bytes = os.fsencode(source)
    target_bytes = os.fsencode(target)
    if sys.platform == "darwin":
        rename = getattr(libc, "renamex_np", None)
        if rename is None:
            raise OSError(errno.ENOTSUP, "atomic no-replace rename is unavailable")
        rename.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        result = rename(source_bytes, target_bytes, 0x00000004)
    elif sys.platform.startswith("linux"):
        rename = getattr(libc, "renameat2", None)
        if rename is None:
            raise OSError(errno.ENOTSUP, "atomic no-replace rename is unavailable")
        rename.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        ]
        rename.restype = ctypes.c_int
        result = rename(-100, source_bytes, -100, target_bytes, 0x00000001)
    else:
        raise OSError(errno.ENOTSUP, "atomic no-replace rename is unavailable")
    if result == 0:
        return
    error_number = ctypes.get_errno()
    if error_number in {errno.EEXIST, errno.ENOTEMPTY}:
        raise FileExistsError(error_number, os.strerror(error_number), str(target))
    raise OSError(
        error_number,
        f"{os.strerror(error_number)} while renaming {source} to {target}",
    )


def _fsync_directory(directory: Path) -> None:
    if os.name != "posix":
        return
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(directory, flags)
    try:
        try:
            os.fsync(descriptor)
        except OSError as exc:
            if exc.errno not in _UNSUPPORTED_FSYNC_ERRORS:
                raise
    finally:
        os.close(descriptor)


def _remove_path(path: Path) -> None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return
    if stat_module.S_ISDIR(info.st_mode) and not stat_module.S_ISLNK(info.st_mode):
        shutil.rmtree(path)
    else:
        path.unlink()
