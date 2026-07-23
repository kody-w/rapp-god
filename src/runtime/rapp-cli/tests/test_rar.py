from __future__ import annotations

import hashlib

import pytest

from rapp_cli.errors import IntegrityFailure, NotFound
from rapp_cli.rar import RarClient, _safe_registry_path, installability


class FakeHttpClient:
    def __init__(self, registry, source=b"source"):
        self.registry = registry
        self.source = source

    def get_json(self, path):
        assert path == "/registry.json"
        return self.registry

    def get_bytes(self, path):
        return self.source


def make_client(registry, source=b"source"):
    client = RarClient(timeout=1)
    client._client = FakeHttpClient(registry, source)
    return client


def registry(agent):
    return {"schema": "rapp-registry/1.1", "agents": [agent]}


def agent(source=b"source"):
    return {
        "name": "@rapp/example",
        "display_name": "Example",
        "description": "Example agent",
        "tags": ["example"],
        "category": "core",
        "_file": "agents/@rapp/example_agent.py",
        "_install_filename": "rar_rapp_example_agent.py",
        "_sha256": hashlib.sha256(source).hexdigest(),
    }


def test_search_and_info():
    item = agent()
    client = make_client(registry(item))

    assert client.search("example core") == [item]
    assert client.info("@rapp/example") == item


def test_info_missing_is_typed():
    client = make_client(registry(agent()))

    with pytest.raises(NotFound):
        client.info("@rapp/missing")


def test_source_verifies_full_sha256():
    source = b"print('trusted')\n"
    item = agent(source)
    client = make_client(registry(item), source)

    assert client.source(item) == (
        "rar_rapp_example_agent.py",
        source,
        hashlib.sha256(source).hexdigest(),
    )


def test_source_rejects_tampering():
    item = agent(b"expected")
    client = make_client(registry(item), b"tampered")

    with pytest.raises(IntegrityFailure, match="does not match"):
        client.source(item)


@pytest.mark.parametrize("path", ["../evil.py", "..\\evil.py", "C:\\evil.py"])
def test_registry_path_rejects_traversal(path):
    assert _safe_registry_path(path) is False


@pytest.mark.parametrize(
    ("item", "reason"),
    [
        (
            {
                "name": "@rapp/basic_agent",
                "_file": "agents/@rapp/basic_agent.py",
                "_install_filename": "rar_rapp_basic_agent_agent.py",
                "_sha256": "a" * 64,
            },
            "dependency",
        ),
        (
            {
                "name": "@rapp/card",
                "_file": "agents/@rapp/card.py.card",
                "_install_filename": "rar_rapp_card_agent.py",
                "_sha256": "a" * 64,
            },
            "not a Python",
        ),
    ],
)
def test_non_installable_registry_entries_are_labeled(item, reason):
    assert installability(item)[0] is False
    assert reason in installability(item)[1]
