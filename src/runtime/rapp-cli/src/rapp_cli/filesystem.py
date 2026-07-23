from __future__ import annotations

import os
import stat
from pathlib import Path


def is_reparse_point(path: Path) -> bool:
    info = os.lstat(path)
    attribute = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(attribute and getattr(info, "st_file_attributes", 0) & attribute)
