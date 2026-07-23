"""Registry-relative, offline-only SDK path resolution."""

import hashlib
from pathlib import Path, PurePosixPath
from typing import Dict, Mapping, Tuple


class PathResolutionError(ValueError):
    pass


class RegistryPathResolver:
    def __init__(self, repository_root: Path, sources: Mapping[str, str]):
        self.repository_root = repository_root.resolve()
        self.sources = dict(sources)
        self._cache: Dict[Tuple[str, str], Path] = {}

    @staticmethod
    def cache_key(source: str, relative_path: str) -> str:
        return hashlib.sha256(
            (source + "\0" + relative_path).encode("utf-8")
        ).hexdigest()

    def resolve(self, source: str, relative_path: str) -> Path:
        key = (source, relative_path)
        if key in self._cache:
            return self._cache[key]
        if source not in self.sources:
            raise PathResolutionError("unknown registry source: {}".format(source))
        logical = PurePosixPath(relative_path)
        if logical.is_absolute() or ".." in logical.parts or not logical.parts:
            raise PathResolutionError("unsafe registry-relative path")
        component = (self.repository_root / self.sources[source]).resolve()
        try:
            component.relative_to(self.repository_root)
        except ValueError:
            raise PathResolutionError("component root escapes repository")
        candidate = component.joinpath(*logical.parts).resolve()
        try:
            candidate.relative_to(component)
        except ValueError:
            raise PathResolutionError("resolved path escapes component")
        if not candidate.is_file():
            raise PathResolutionError(
                "registry-relative path is unavailable: {}:{}".format(
                    source, relative_path
                )
            )
        self._cache[key] = candidate
        return candidate
