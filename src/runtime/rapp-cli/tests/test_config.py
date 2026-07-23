from __future__ import annotations

import json

import pytest

from rapp_cli.config import Config, default_config_path, normalize_base_url
from rapp_cli.errors import UsageError


def test_config_precedence(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps({"brainstem_url": "http://file.example:7071", "timeout": 12}),
        encoding="utf-8",
    )

    config = Config.load(
        config_path=path,
        brainstem_url="https://cli.example/",
        timeout=5,
        env={
            "RAPP_BRAINSTEM_URL": "http://env.example:7071",
            "RAPP_TIMEOUT": "9",
        },
    )

    assert config.brainstem_url == "https://cli.example"
    assert config.timeout == 5


def test_config_reads_secret_file(tmp_path):
    secret_path = tmp_path / "secret"
    secret_path.write_text("shh\n", encoding="utf-8")
    secret_path.chmod(0o600)

    config = Config.load(
        config_path=tmp_path / "missing.json",
        secret_file=secret_path,
        env={},
    )

    assert config.secret == "shh"


@pytest.mark.parametrize(
    "value",
    [
        "localhost:7071",
        "file:///tmp/socket",
        "https://user:password@example.com",
        "https://example.com/?token=secret",
        "https://example.com:99999",
        "https://example.com:0",
    ],
)
def test_normalize_base_url_rejects_unsafe_urls(value):
    with pytest.raises(UsageError):
        normalize_base_url(value)


def test_remote_plaintext_requires_explicit_opt_in():
    with pytest.raises(UsageError, match="plaintext HTTP"):
        normalize_base_url("http://192.168.1.20:7071")

    assert (
        normalize_base_url(
            "http://192.168.1.20:7071",
            allow_insecure_http=True,
        )
        == "http://192.168.1.20:7071"
    )


def test_default_config_honors_xdg(tmp_path):
    assert default_config_path({"XDG_CONFIG_HOME": str(tmp_path)}) == (
        tmp_path / "rapp" / "config.json"
    )


def test_endpoint_environment_alias(tmp_path):
    config = Config.load(
        config_path=tmp_path / "missing.json",
        env={"RAPP_ENDPOINT": "https://brainstem.example"},
    )

    assert config.brainstem_url == "https://brainstem.example"


def test_malformed_config_is_explicit(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("{", encoding="utf-8")

    with pytest.raises(UsageError, match="not valid JSON"):
        Config.load(config_path=path, env={})


def test_unknown_config_fields_are_rejected(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"brainstem_url": "http://localhost:7071", "typo": 1}))

    with pytest.raises(UsageError, match="unknown fields"):
        Config.load(config_path=path, env={})


def test_duplicate_config_fields_are_rejected(tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"timeout":1,"timeout":2}', encoding="utf-8")

    with pytest.raises(UsageError, match="duplicate"):
        Config.load(config_path=path, env={})


@pytest.mark.parametrize("timeout", ["nan", "inf", "-inf"])
def test_non_finite_timeout_is_rejected(tmp_path, timeout):
    with pytest.raises(UsageError, match="greater than 0"):
        Config.load(
            config_path=tmp_path / "missing.json",
            timeout=timeout,
            env={},
        )


def test_secret_file_config_must_be_a_string(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"brainstem_secret_file": ["not", "a", "path"]}))

    with pytest.raises(UsageError, match="string path"):
        Config.load(config_path=path, env={})


def test_oversized_config_is_rejected(tmp_path):
    path = tmp_path / "config.json"
    path.write_bytes(b" " * (1024 * 1024 + 1))

    with pytest.raises(UsageError, match="exceeds 1 MiB"):
        Config.load(config_path=path, env={})
