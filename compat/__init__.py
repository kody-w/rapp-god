"""Target-owned, fail-closed compatibility helpers."""

from .rapp1 import CompatibilityError, normalize_request, normalize_success
from .sdk_paths import PathResolutionError, RegistryPathResolver

__all__ = [
    "CompatibilityError",
    "PathResolutionError",
    "RegistryPathResolver",
    "normalize_request",
    "normalize_success",
]
