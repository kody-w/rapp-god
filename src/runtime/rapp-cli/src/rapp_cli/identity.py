from __future__ import annotations

import re
from dataclasses import dataclass

from .errors import UsageError

LABEL_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", re.ASCII)
RAPPID_RE = re.compile(
    r"^rappid:@(?P<owner>[a-z0-9]+(?:-[a-z0-9]+)*)/"
    r"(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*):(?P<tail>[0-9a-f]{64})$",
    re.ASCII,
)


@dataclass(frozen=True, slots=True)
class Rappid:
    owner: str
    slug: str
    tail: str

    def __str__(self) -> str:
        return f"rappid:@{self.owner}/{self.slug}:{self.tail}"


def _validate_label(value: str, *, name: str, maximum: int) -> str:
    if (
        type(value) is not str
        or not 1 <= len(value) <= maximum
        or LABEL_RE.fullmatch(value) is None
    ):
        raise UsageError(
            f"rappid {name} must be 1-{maximum} lowercase "
            "alphanumeric/hyphen characters without adjacent or edge hyphens"
        )
    return value


def parse_rappid(value: str) -> Rappid:
    if type(value) is not str:
        raise UsageError("rappid must be a string")
    match = RAPPID_RE.fullmatch(value)
    if match is None:
        raise UsageError("rappid does not match the RAPP/1 canonical form")
    owner = _validate_label(match.group("owner"), name="owner", maximum=39)
    slug = _validate_label(match.group("slug"), name="slug", maximum=100)
    return Rappid(owner=owner, slug=slug, tail=match.group("tail"))


def is_canonical_rappid(value: str) -> bool:
    try:
        parse_rappid(value)
    except UsageError:
        return False
    return True
