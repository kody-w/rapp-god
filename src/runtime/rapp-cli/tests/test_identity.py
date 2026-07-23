from __future__ import annotations

import pytest

from rapp_cli.errors import UsageError
from rapp_cli.identity import is_canonical_rappid, parse_rappid

TAIL = "a" * 64


def test_parse_rappid_accepts_rapp1_length_limits():
    owner = "a" * 39
    slug = "b" * 100
    value = f"rappid:@{owner}/{slug}:{TAIL}"

    parsed = parse_rappid(value)

    assert parsed.owner == owner
    assert parsed.slug == slug
    assert parsed.tail == TAIL
    assert str(parsed) == value
    assert is_canonical_rappid(value) is True


@pytest.mark.parametrize(
    "value",
    [
        f"rappid:@Owner/slug:{TAIL}",
        f"rappid:@owner/Slug:{TAIL}",
        f"rappid:@owner.name/slug:{TAIL}",
        f"rappid:@owner/slug_name:{TAIL}",
        f"rappid:@owner--name/slug:{TAIL}",
        f"rappid:@owner/name--slug:{TAIL}",
        f"rappid:@owner-/slug:{TAIL}",
        f"rappid:@owner/slug-:{TAIL}",
        f"rappid:@{'a' * 40}/slug:{TAIL}",
        f"rappid:@owner/{'b' * 101}:{TAIL}",
        f"rappid:@owner/slug:{'A' * 64}",
    ],
)
def test_parse_rappid_rejects_noncanonical_rapp1_forms(value):
    with pytest.raises(UsageError):
        parse_rappid(value)

    assert is_canonical_rappid(value) is False
