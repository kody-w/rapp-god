from __future__ import annotations

import json
from typing import Any


class DuplicateKeyError(ValueError):
    pass


class NonFiniteNumberError(ValueError):
    pass


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _constant(value: str) -> Any:
    raise NonFiniteNumberError(f"non-finite JSON number: {value}")


def loads(value: str | bytes) -> Any:
    return json.loads(
        value,
        object_pairs_hook=_object,
        parse_constant=_constant,
    )
