from __future__ import annotations

import os
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .errors import NotFound, RemoteFailure


@dataclass(frozen=True, slots=True)
class BrainstemInstallation:
    home: Path
    source: Path
    python: Path

    def to_dict(self) -> dict[str, Any]:
        return {key: str(value) for key, value in asdict(self).items()}


def default_brainstem_home() -> Path:
    configured = os.environ.get("RAPP_BRAINSTEM_HOME") or os.environ.get("BRAINSTEM_HOME")
    return Path(configured).expanduser() if configured else Path.home() / ".brainstem"


def locate_brainstem(home: str | Path | None = None) -> BrainstemInstallation:
    root = (Path(home).expanduser() if home else default_brainstem_home()).resolve()
    source_candidates = [
        root / "src" / "rapp_brainstem" / "brainstem.py",
        root / "rapp_brainstem" / "brainstem.py",
        root / "brainstem.py",
    ]
    source = next((candidate for candidate in source_candidates if candidate.is_file()), None)
    if source is None:
        raise NotFound(
            f"Brainstem installation not found under {root}",
            details={"home": str(root)},
        )

    python_candidates = (
        [root / "venv" / "Scripts" / "python.exe", root / "venv" / "Scripts" / "python"]
        if os.name == "nt"
        else [root / "venv" / "bin" / "python3", root / "venv" / "bin" / "python"]
    )
    python = next((candidate for candidate in python_candidates if candidate.is_file()), None)
    if python is None:
        raise NotFound(
            f"Brainstem Python environment not found under {root / 'venv'}",
            details={"home": str(root)},
        )
    return BrainstemInstallation(home=root, source=source, python=python)


def run_brainstem(installation: BrainstemInstallation) -> int:
    try:
        completed = subprocess.run(
            [str(installation.python), str(installation.source)],
            cwd=installation.source.parent,
            check=False,
        )
    except OSError as exc:
        raise RemoteFailure(f"could not launch Brainstem: {exc}") from exc
    return completed.returncode
