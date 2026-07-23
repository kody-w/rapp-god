from __future__ import annotations

import os
from pathlib import Path

import pytest

from rapp_cli.errors import NotFound
from rapp_cli.runtime import locate_brainstem


def make_installation(tmp_path: Path) -> tuple[Path, Path, Path]:
    source = tmp_path / "src" / "rapp_brainstem" / "brainstem.py"
    source.parent.mkdir(parents=True)
    source.write_text("print('brainstem')\n", encoding="utf-8")
    python = (
        tmp_path / "venv" / "Scripts" / "python.exe"
        if os.name == "nt"
        else tmp_path / "venv" / "bin" / "python3"
    )
    python.parent.mkdir(parents=True)
    python.write_text("", encoding="utf-8")
    return tmp_path, source, python


def test_locate_installer_layout(tmp_path):
    home, source, python = make_installation(tmp_path)

    installation = locate_brainstem(home)

    assert installation.home == home
    assert installation.source == source
    assert installation.python == python


def test_locate_missing_installation_is_typed(tmp_path):
    with pytest.raises(NotFound, match="not found"):
        locate_brainstem(tmp_path)


def test_locate_normalizes_relative_home(tmp_path, monkeypatch):
    home, source, python = make_installation(tmp_path / "brainstem")
    monkeypatch.chdir(tmp_path)

    installation = locate_brainstem("brainstem")

    assert installation.home == home
    assert installation.source == source
    assert installation.python == python
