from __future__ import annotations

import pytest

from rapp_cli.errors import RemoteFailure
from rapp_cli.release_train import ReleaseTrainClient


class FakeHttpClient:
    def __init__(self, responses):
        self.responses = responses

    def get_json(self, path):
        return self.responses[path]


def client_with(responses):
    client = ReleaseTrainClient(timeout=1)
    client._client = FakeHttpClient(responses)
    return client


def test_status_requires_exact_schema():
    client = client_with({"/api/v1/status.json": {"schema": "other"}})

    with pytest.raises(RemoteFailure, match="unsupported"):
        client.status()


def test_status_rejects_nested_type_errors():
    client = client_with(
        {
            "/api/v1/status.json": {
                "schema": "rapp-static-api-status/1.0",
                "summary": {"entries": "one", "drift": 0, "versions": 1},
                "entries": [],
            }
        }
    )

    with pytest.raises(RemoteFailure, match="counters"):
        client.status()


def test_manifest_accepts_release_train_schema():
    payload = {
        "schema": "rapp-static-api/1.0",
        "entries": [
            {
                "name": "rapp_brainstem/VERSION",
                "sources": [{"label": "canary", "url": "https://example.test/version"}],
            }
        ],
    }
    client = client_with({"/manifest.json": payload})

    assert client.manifest() == payload
