from __future__ import annotations

import pytest

from rapp_cli.jsonio import DuplicateKeyError, NonFiniteNumberError, loads


def test_duplicate_keys_are_rejected():
    with pytest.raises(DuplicateKeyError, match="duplicate"):
        loads('{"status":"ok","status":"error"}')


def test_non_finite_numbers_are_rejected():
    with pytest.raises(NonFiniteNumberError, match="non-finite"):
        loads('{"timeout":NaN}')
