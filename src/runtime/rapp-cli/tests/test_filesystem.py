from __future__ import annotations

from types import SimpleNamespace

import rapp_cli.filesystem as filesystem


def test_reparse_point_detection(monkeypatch, tmp_path):
    monkeypatch.setattr(filesystem.stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400, raising=False)
    monkeypatch.setattr(
        filesystem.os,
        "lstat",
        lambda _path: SimpleNamespace(st_file_attributes=0x400),
    )

    assert filesystem.is_reparse_point(tmp_path) is True
