from __future__ import annotations

import pytest

from rapp_cli.errors import RemoteFailure
from rapp_cli.provider import require_provider_success


@pytest.mark.parametrize("status", ["error", "pending", "", None, False, 1])
def test_provider_success_rejects_present_non_ok_status(status):
    with pytest.raises(RemoteFailure, match="non-ok status"):
        require_provider_success({"status": status}, "agent import")


def test_provider_success_accepts_ok_or_omitted_status():
    assert require_provider_success({"status": "ok"}, "agent import") == {"status": "ok"}
    assert require_provider_success({"message": "complete"}, "agent removal") == {
        "message": "complete"
    }
