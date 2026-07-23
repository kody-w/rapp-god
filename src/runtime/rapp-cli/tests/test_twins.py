from __future__ import annotations

import json
import os

import pytest

from rapp_cli.errors import NotFound, UsageError
from rapp_cli.twins import list_twins, show_twin


def write_twin(root, name, *, state=None, rappid=None):
    parent = root / state if state else root
    path = parent / name
    path.mkdir(parents=True)
    (path / "rappid.json").write_text(
        json.dumps({"rappid": rappid or f"rappid:{name}", "name": name.title()}),
        encoding="utf-8",
    )
    return path


def test_list_twins_separates_active_and_archived(tmp_path):
    write_twin(tmp_path, "active")
    write_twin(tmp_path, "old", state=".archive")

    assert [twin.id for twin in list_twins(tmp_path)] == ["active"]
    assert [(twin.id, twin.state) for twin in list_twins(tmp_path, include_archived=True)] == [
        ("active", "active"),
        ("old", "archived"),
    ]


def test_show_twin_accepts_rappid(tmp_path):
    write_twin(tmp_path, "echo", rappid="rappid:echo")

    assert show_twin("rappid:echo", tmp_path).id == "echo"


def test_show_twin_rejects_traversal(tmp_path):
    with pytest.raises(UsageError):
        show_twin("../outside", tmp_path)


@pytest.mark.parametrize(
    "rappid",
    [
        "rappid:@Owner/slug:" + "a" * 64,
        "rappid:@owner/slug_name:" + "a" * 64,
        "rappid:@owner--name/slug:" + "a" * 64,
        "rappid:@" + "a" * 40 + "/slug:" + "a" * 64,
    ],
)
def test_show_twin_uses_strict_rapp1_parser(rappid, tmp_path):
    with pytest.raises(UsageError):
        show_twin(rappid, tmp_path)


def test_show_twin_missing_is_typed(tmp_path):
    with pytest.raises(NotFound):
        show_twin("missing", tmp_path)


@pytest.mark.skipif(os.name == "nt", reason="symlink creation is not reliably available")
def test_list_twins_skips_symlinked_workspace(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    (tmp_path / "linked").symlink_to(target, target_is_directory=True)

    assert list_twins(tmp_path) == [show_twin("target", tmp_path)]


def test_malformed_metadata_does_not_break_listing(tmp_path):
    twin = tmp_path / "echo"
    twin.mkdir()
    (twin / "rappid.json").write_text('{"rappid":', encoding="utf-8")

    listed = list_twins(tmp_path)

    assert len(listed) == 1
    assert listed[0].rappid is None
