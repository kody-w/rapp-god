from __future__ import annotations

import hashlib
import hmac
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote

from .client import BrainstemClient
from .config import Config, normalize_base_url
from .errors import IntegrityFailure, NotFound, RemoteFailure, UsageError

RAR_REVISION = "241c6191736a856b6837ef2398447a25710b8d72"
RAR_BASE = f"https://raw.githubusercontent.com/kody-w/RAR/{RAR_REVISION}"


class RarClient:
    def __init__(self, *, timeout: float) -> None:
        config = Config(
            brainstem_url=normalize_base_url(RAR_BASE),
            timeout=timeout,
            secret=None,
            config_path=Path("<rar>"),
        )
        self._client = BrainstemClient(config, service_name="RAR")

    def registry(self) -> dict[str, Any]:
        payload = self._client.get_json("/registry.json")
        if not isinstance(payload, dict) or payload.get("schema") != "rapp-registry/1.1":
            raise RemoteFailure("RAR returned an unsupported registry schema")
        if not isinstance(payload.get("agents"), list):
            raise RemoteFailure("RAR registry is missing its agents array")
        return payload

    def search(self, query: str) -> list[dict[str, Any]]:
        terms = query.casefold().split()
        if not terms:
            raise UsageError("agent search requires a non-empty query")
        matches = []
        for agent in self.registry()["agents"]:
            if not isinstance(agent, dict):
                continue
            tags = agent.get("tags")
            searchable = " ".join(
                [
                    str(agent.get("name") or ""),
                    str(agent.get("display_name") or ""),
                    str(agent.get("description") or ""),
                    str(agent.get("category") or ""),
                    " ".join(str(tag) for tag in tags) if isinstance(tags, list) else "",
                ]
            ).casefold()
            if all(term in searchable for term in terms):
                matches.append(agent)
        return matches

    def info(self, name: str) -> dict[str, Any]:
        for agent in self.registry()["agents"]:
            if isinstance(agent, dict) and agent.get("name") == name:
                return agent
        raise NotFound(f"RAR agent not found: {name}")

    def source(self, agent: dict[str, Any]) -> tuple[str, bytes, str]:
        installable, reason = installability(agent)
        if not installable:
            raise IntegrityFailure(f"RAR entry is not an installable agent: {reason}")
        path_value = agent.get("_file")
        filename = agent.get("_install_filename")
        expected = agent.get("_sha256")
        if not all(isinstance(value, str) and value for value in (path_value, filename, expected)):
            raise RemoteFailure("RAR agent metadata is missing source integrity fields")
        if not _safe_registry_path(path_value):
            raise IntegrityFailure("RAR registry contains an unsafe source path")
        if len(expected) != 64 or any(char not in "0123456789abcdef" for char in expected.lower()):
            raise IntegrityFailure("RAR registry contains an invalid source digest")
        payload = self._client.get_bytes(f"/{quote(path_value, safe='/@._-')}")
        actual = hashlib.sha256(payload).hexdigest()
        if not hmac.compare_digest(actual, expected.lower()):
            raise IntegrityFailure(
                "RAR source does not match its registry digest",
                details={"expected_sha256": expected.lower(), "actual_sha256": actual},
            )
        return filename, payload, actual


def installability(agent: dict[str, Any]) -> tuple[bool, str | None]:
    if agent.get("name") == "@rapp/basic_agent":
        return False, "basic_agent is a dependency, not a callable cartridge"
    path_value = agent.get("_file")
    filename = agent.get("_install_filename")
    digest = agent.get("_sha256")
    if not isinstance(path_value, str) or not path_value.endswith(".py"):
        return False, "registry source is not a Python agent file"
    if not isinstance(filename, str) or not filename.endswith("_agent.py"):
        return False, "registry install filename is invalid"
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or any(char not in "0123456789abcdef" for char in digest.lower())
    ):
        return False, "registry source has no valid SHA-256"
    return True, None


def _safe_registry_path(value: str) -> bool:
    if "\\" in value or "\x00" in value or ":" in value:
        return False
    path = PurePosixPath(value)
    return (
        not path.is_absolute()
        and ".." not in path.parts
        and path.suffix == ".py"
        and all(part not in {"", "."} for part in path.parts)
    )
