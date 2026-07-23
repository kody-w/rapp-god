from __future__ import annotations

import io
import json
import os

import pytest

from rapp_cli import cli, commands
from rapp_cli.errors import ConnectionFailure


class FakeClient:
    responses = {}
    posts = []
    stream_responses = None

    def __init__(self, config):
        self.config = config

    def get_json(self, path):
        value = self.responses[path]
        if isinstance(value, Exception):
            raise value
        return value

    def post_json(self, path, payload):
        self.posts.append((path, payload))
        return self.responses[path]

    def stream_events(self, path, payload):
        self.posts.append((path, payload))
        if self.stream_responses is not None:
            yield from self.stream_responses
            return
        yield {"event": "message", "id": None, "data": {"type": "delta", "text": "hello"}}
        yield {"event": "message", "id": None, "data": {"type": "delta", "text": " world"}}
        yield {
            "event": "message",
            "id": None,
            "data": {"type": "done", "response": "hello world", "agent_logs": ""},
        }

    def import_agent(self, filename, payload, *, sha256=None, source_revision=None):
        self.posts.append(
            (
                "/agents/import",
                {
                    "filename": filename,
                    "payload": payload,
                    "sha256": sha256,
                    "source_revision": source_revision,
                },
            )
        )
        return self.responses["/agents/import"]

    def export_agent(self, filename):
        self.posts.append(("/agents/export", filename))
        return self.responses["/agents/export"]

    def remove_agent(self, filename):
        self.posts.append(("/agents/remove", filename))
        return self.responses["/agents/remove"]


def run(monkeypatch, tmp_path, *args):
    FakeClient.responses = {}
    FakeClient.posts = []
    FakeClient.stream_responses = None
    monkeypatch.setattr(cli, "BrainstemClient", FakeClient)
    return [
        "--config",
        str(tmp_path / "missing.json"),
        *args,
    ]


def test_status_json(monkeypatch, tmp_path, capsys):
    argv = run(monkeypatch, tmp_path, "--json", "status")
    FakeClient.responses["/version"] = {"version": "1.2.3"}

    assert cli.main(argv) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["data"]["version"] == "1.2.3"
    assert payload["data"]["probe"] == "/version"


def test_no_arguments_prints_help(capsys):
    assert cli.main([]) == 0
    assert "Headless command-line" in capsys.readouterr().out


def test_json_version_uses_machine_contract(capsys):
    assert cli.main(["--json", "--version"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == "version"
    assert payload["data"]["version"] == "0.1.0"


def test_parser_errors_use_json_contract(capsys):
    assert cli.main(["--json", "not-a-command"]) == 2

    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "rapp-cli-error/1.0"
    assert payload["error"]["code"] == "INVALID_USAGE"


def test_nested_parser_error_does_not_leak_internal_dest_name(capsys):
    assert cli.main(["--json", "agent"]) == 2

    payload = json.loads(capsys.readouterr().out)
    assert payload["error"]["message"] == "a subcommand is required"


def test_chat_posts_headless_contract(monkeypatch, tmp_path, capsys):
    argv = run(monkeypatch, tmp_path, "chat", "hello", "world", "--session-id", "abc")
    FakeClient.responses["/chat"] = {"response": "hi", "session_id": "abc"}

    assert cli.main(argv) == 0

    assert capsys.readouterr().out == "hi\n"
    assert FakeClient.posts == [
        (
            "/chat",
            {
                "user_input": "hello world",
                "conversation_history": [],
                "session_id": "abc",
            },
        )
    ]


def test_chat_json_omits_agent_logs_by_default(monkeypatch, tmp_path, capsys):
    argv = run(monkeypatch, tmp_path, "--json", "chat", "hello")
    FakeClient.responses["/chat"] = {
        "response": "hi",
        "session_id": "abc",
        "agent_logs": "local path and tool details",
    }

    assert cli.main(argv) == 0

    payload = json.loads(capsys.readouterr().out)
    assert "agent_logs" not in payload["data"]


def test_chat_reads_piped_stdin(monkeypatch, tmp_path, capsys):
    argv = run(monkeypatch, tmp_path, "chat")
    FakeClient.responses["/chat"] = {"response": "from stdin"}
    monkeypatch.setattr("sys.stdin", io.StringIO("piped prompt\n"))

    assert cli.main(argv) == 0

    assert capsys.readouterr().out == "from stdin\n"
    assert FakeClient.posts[0][1]["user_input"] == "piped prompt"


def test_chat_dash_reads_stdin(monkeypatch, tmp_path, capsys):
    argv = run(monkeypatch, tmp_path, "chat", "-")
    FakeClient.responses["/chat"] = {"response": "from dash"}
    monkeypatch.setattr("sys.stdin", io.StringIO("dash prompt\n"))

    assert cli.main(argv) == 0

    assert capsys.readouterr().out == "from dash\n"
    assert FakeClient.posts[0][1]["user_input"] == "dash prompt"


def test_chat_rejects_oversized_piped_input(monkeypatch, tmp_path, capsys):
    argv = run(monkeypatch, tmp_path, "chat", "-")
    monkeypatch.setattr("sys.stdin", io.StringIO("x" * (1024 * 1024 + 1)))

    assert cli.main(argv) == 2

    assert "exceeds the 1 MiB" in capsys.readouterr().err


def test_chat_history_accepts_tool_role(monkeypatch, tmp_path, capsys):
    history = tmp_path / "history.json"
    history.write_text(
        json.dumps([{"role": "tool", "content": "result"}]),
        encoding="utf-8",
    )
    argv = run(monkeypatch, tmp_path, "chat", "continue", "--history", str(history))
    FakeClient.responses["/chat"] = {"response": "done"}

    assert cli.main(argv) == 0

    assert FakeClient.posts[0][1]["conversation_history"] == [{"role": "tool", "content": "result"}]


def test_stream_json_is_json_lines(monkeypatch, tmp_path, capsys):
    argv = run(monkeypatch, tmp_path, "--jsonl", "chat", "hello", "--stream")

    assert cli.main(argv) == 0

    events = [json.loads(line)["event"] for line in capsys.readouterr().out.splitlines()]
    assert [event["text"] for event in events if event["type"] == "delta"] == [
        "hello",
        " world",
    ]
    assert events[-1] == {"type": "done", "response": "hello world"}


def test_stream_rejects_single_json_mode(monkeypatch, tmp_path, capsys):
    argv = run(monkeypatch, tmp_path, "--json", "chat", "hello", "--stream")

    assert cli.main(argv) == 2

    payload = json.loads(capsys.readouterr().out)
    assert payload["error"]["code"] == "INVALID_USAGE"


def test_stream_error_is_failure(monkeypatch, tmp_path, capsys):
    argv = run(monkeypatch, tmp_path, "--jsonl", "chat", "hello", "--stream")
    FakeClient.stream_responses = [
        {
            "event": "message",
            "id": None,
            "data": {"type": "error", "error": "model failed"},
        }
    ]

    assert cli.main(argv) == 7

    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["error"]["message"] == "model failed"


def test_stream_requires_done_event(monkeypatch, tmp_path, capsys):
    argv = run(monkeypatch, tmp_path, "chat", "hello", "--stream")
    FakeClient.stream_responses = [
        {
            "event": "message",
            "id": None,
            "data": {"type": "delta", "text": "partial"},
        }
    ]

    assert cli.main(argv) == 7

    captured = capsys.readouterr()
    assert captured.out == "partial"
    assert "without a done event" in captured.err


def test_quiet_suppresses_human_stream(monkeypatch, tmp_path, capsys):
    argv = run(monkeypatch, tmp_path, "--quiet", "chat", "hello", "--stream")

    assert cli.main(argv) == 0

    assert capsys.readouterr().out == ""


def test_typed_error_exit_and_json(monkeypatch, tmp_path, capsys):
    argv = run(monkeypatch, tmp_path, "--json", "status")
    FakeClient.responses["/version"] = ConnectionFailure("offline")

    assert cli.main(argv) == 4

    payload = json.loads(capsys.readouterr().out)
    assert payload["error"]["code"] == "CONNECTION_FAILED"


def test_unexpected_error_has_stable_machine_contract(monkeypatch, tmp_path, capsys):
    argv = run(monkeypatch, tmp_path, "--json", "status")
    FakeClient.responses["/version"] = ValueError("secret internal detail")

    assert cli.main(argv) == 70

    payload = json.loads(capsys.readouterr().out)
    assert payload["error"]["code"] == "INTERNAL_ERROR"
    assert "secret internal detail" not in payload["error"]["message"]


def test_launch_rejects_json_mode(monkeypatch, tmp_path, capsys):
    argv = run(monkeypatch, tmp_path, "--json", "launch")

    assert cli.main(argv) == 2

    payload = json.loads(capsys.readouterr().out)
    assert payload["error"]["code"] == "INVALID_USAGE"


def test_doctor_offline_never_calls_remote(monkeypatch, tmp_path, capsys):
    argv = run(monkeypatch, tmp_path, "doctor", "--offline")

    assert cli.main(argv) == 0

    assert "python" in capsys.readouterr().out


def test_doctor_failure_preserves_check_details(monkeypatch, tmp_path, capsys):
    argv = run(monkeypatch, tmp_path, "--json", "doctor")
    FakeClient.responses["/version"] = ConnectionFailure("offline")

    assert cli.main(argv) == 1

    payload = json.loads(capsys.readouterr().out)
    assert payload["error"]["code"] == "DOCTOR_FAILED"
    assert any(check["name"] == "brainstem" for check in payload["error"]["details"]["checks"])


def test_doctor_modes_are_mutually_exclusive(monkeypatch, tmp_path, capsys):
    argv = run(monkeypatch, tmp_path, "--json", "doctor", "--offline", "--deep")

    assert cli.main(argv) == 2

    assert json.loads(capsys.readouterr().out)["error"]["code"] == "INVALID_USAGE"


def test_agent_import(monkeypatch, tmp_path, capsys):
    source = tmp_path / "hello_agent.py"
    source.write_text("class HelloAgent: pass\n", encoding="utf-8")
    argv = run(monkeypatch, tmp_path, "agent", "import", str(source), "--yes")
    FakeClient.responses["/agents/import"] = {"status": "ok"}

    assert cli.main(argv) == 0

    assert "imported hello_agent.py" in capsys.readouterr().out


def test_agent_import_rejects_non_ok_status(monkeypatch, tmp_path, capsys):
    source = tmp_path / "hello_agent.py"
    source.write_text("class HelloAgent: pass\n", encoding="utf-8")
    argv = run(monkeypatch, tmp_path, "agent", "import", str(source), "--yes")
    FakeClient.responses["/agents/import"] = {"status": "pending"}

    assert cli.main(argv) == 7

    assert "non-ok status" in capsys.readouterr().err


def test_agent_import_requires_confirmation(monkeypatch, tmp_path, capsys):
    source = tmp_path / "hello_agent.py"
    source.write_text("class HelloAgent: pass\n", encoding="utf-8")
    argv = run(monkeypatch, tmp_path, "agent", "import", str(source))

    assert cli.main(argv) == 6

    assert "requires --yes" in capsys.readouterr().err


def test_auth_status_shows_resumable_code(monkeypatch, tmp_path, capsys):
    argv = run(monkeypatch, tmp_path, "auth", "status")
    FakeClient.responses["/login/status"] = {
        "pending": True,
        "user_code": "ABCD-EFGH",
        "verification_uri": "https://github.com/login/device",
        "expires_in": 300,
    }

    assert cli.main(argv) == 0

    output = capsys.readouterr().out
    assert "ABCD-EFGH" in output
    assert "github.com/login/device" in output


def test_agent_import_rejects_hash_mismatch(monkeypatch, tmp_path, capsys):
    source = tmp_path / "hello_agent.py"
    source.write_text("class HelloAgent: pass\n", encoding="utf-8")
    argv = run(
        monkeypatch,
        tmp_path,
        "agent",
        "import",
        str(source),
        "--sha256",
        "0" * 64,
        "--yes",
    )

    assert cli.main(argv) == 8

    assert "does not match" in capsys.readouterr().err


@pytest.mark.skipif(os.name == "nt", reason="symlink creation is not reliably available")
def test_agent_import_rejects_symlink(monkeypatch, tmp_path, capsys):
    target = tmp_path / "target_agent.py"
    target.write_text("class TargetAgent: pass\n", encoding="utf-8")
    source = tmp_path / "linked_agent.py"
    source.symlink_to(target)
    argv = run(monkeypatch, tmp_path, "agent", "import", str(source), "--yes")

    assert cli.main(argv) == 2

    assert "cannot open" in capsys.readouterr().err


def test_agent_export_refuses_overwrite(monkeypatch, tmp_path, capsys):
    destination = tmp_path / "copy.py"
    destination.write_text("existing", encoding="utf-8")
    argv = run(
        monkeypatch,
        tmp_path,
        "agent",
        "export",
        "hello_agent.py",
        "--output",
        str(destination),
    )

    assert cli.main(argv) == 6

    assert destination.read_text(encoding="utf-8") == "existing"
    assert "refusing to overwrite" in capsys.readouterr().err


def test_agent_export_writes_atomically(monkeypatch, tmp_path, capsys):
    destination = tmp_path / "copy_agent.py"
    argv = run(
        monkeypatch,
        tmp_path,
        "agent",
        "export",
        "hello_agent.py",
        "--output",
        str(destination),
    )
    FakeClient.responses["/agents/export"] = b"trusted source\n"

    assert cli.main(argv) == 0

    assert destination.read_bytes() == b"trusted source\n"
    assert "exported hello_agent.py" in capsys.readouterr().out


def test_atomic_export_failure_preserves_existing(monkeypatch, tmp_path):
    destination = tmp_path / "agent.py"
    destination.write_bytes(b"previous")

    def fail_replace(_source, _destination):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(commands.os, "replace", fail_replace)

    with pytest.raises(OSError, match="simulated"):
        commands._atomic_write_file(destination, b"new", replace=True)

    assert destination.read_bytes() == b"previous"
    assert list(tmp_path.glob(".*.tmp")) == []


def test_agent_remove_requires_confirmation(monkeypatch, tmp_path, capsys):
    argv = run(monkeypatch, tmp_path, "agent", "remove", "hello_agent.py")

    assert cli.main(argv) == 6

    assert "requires --yes" in capsys.readouterr().err


def test_agent_remove_rejects_non_ok_status(monkeypatch, tmp_path, capsys):
    argv = run(
        monkeypatch,
        tmp_path,
        "agent",
        "remove",
        "hello_agent.py",
        "--yes",
    )
    FakeClient.responses["/agents/remove"] = {"status": "pending"}

    assert cli.main(argv) == 7

    assert "non-ok status" in capsys.readouterr().err


def test_config_show_never_prints_secret(monkeypatch, tmp_path, capsys):
    secret = tmp_path / "secret"
    secret.write_text("do-not-print-me", encoding="utf-8")
    secret.chmod(0o600)
    argv = [
        "--config",
        str(tmp_path / "missing.json"),
        "--secret-file",
        str(secret),
        "config",
        "show",
    ]
    monkeypatch.setattr(cli, "BrainstemClient", FakeClient)

    assert cli.main(argv) == 0

    output = capsys.readouterr().out
    assert "secret_configured: true" in output
    assert "do-not-print-me" not in output


def test_unpublished_capability_fails_honestly(monkeypatch, tmp_path, capsys):
    argv = run(monkeypatch, tmp_path, "--json", "ring", "fly", "canary")

    assert cli.main(argv) == 3

    payload = json.loads(capsys.readouterr().out)
    assert payload["error"]["code"] == "CAPABILITY_UNAVAILABLE"


def test_chat_http_200_copilot_error_is_failure(monkeypatch, tmp_path, capsys):
    argv = run(monkeypatch, tmp_path, "chat", "hello")
    FakeClient.responses["/chat"] = {
        "response": "not available",
        "no_copilot_access": True,
    }

    assert cli.main(argv) == 5

    assert "does not have Copilot access" in capsys.readouterr().err


def test_auth_login_returns_device_code(monkeypatch, tmp_path, capsys):
    argv = run(monkeypatch, tmp_path, "auth", "login")
    FakeClient.responses["/login"] = {
        "user_code": "ABCD-EFGH",
        "verification_uri": "https://github.com/login/device",
        "interval": 5,
    }

    assert cli.main(argv) == 0

    output = capsys.readouterr().out
    assert "ABCD-EFGH" in output
    assert "github.com/login/device" in output


def test_auth_wait_rejects_json_mode(monkeypatch, tmp_path, capsys):
    argv = run(monkeypatch, tmp_path, "--json", "auth", "login", "--wait")
    FakeClient.responses["/login"] = {
        "user_code": "ABCD-EFGH",
        "verification_uri": "https://github.com/login/device",
        "interval": 5,
    }

    assert cli.main(argv) == 2

    payload = json.loads(capsys.readouterr().out)
    assert payload["error"]["code"] == "INVALID_USAGE"
    assert FakeClient.posts == []


def test_auth_wait_never_sleeps_past_deadline(monkeypatch, tmp_path, capsys):
    argv = run(monkeypatch, tmp_path, "auth", "login", "--wait", "--deadline", "2")
    FakeClient.responses["/login"] = {
        "user_code": "ABCD-EFGH",
        "verification_uri": "https://github.com/login/device",
        "interval": 10,
    }
    FakeClient.responses["/login/poll"] = {"status": "pending"}
    now = [0.0]
    sleeps = []

    monkeypatch.setattr(commands.time, "monotonic", lambda: now[0])

    def sleep(seconds):
        sleeps.append(seconds)
        now[0] += seconds

    monkeypatch.setattr(commands.time, "sleep", sleep)

    assert cli.main(argv) == 7

    assert sleeps == [2.0]
    assert "within 2 seconds" in capsys.readouterr().err


def test_auth_switch_requires_confirmation(monkeypatch, tmp_path, capsys):
    argv = run(monkeypatch, tmp_path, "auth", "switch")

    assert cli.main(argv) == 6

    assert "requires --yes" in capsys.readouterr().err


def test_auth_poll_error_is_failure(monkeypatch, tmp_path, capsys):
    argv = run(monkeypatch, tmp_path, "auth", "poll")
    FakeClient.responses["/login/poll"] = {
        "status": "error",
        "error": "exchange failed",
    }

    assert cli.main(argv) == 7

    assert "exchange failed" in capsys.readouterr().err


def test_health_no_copilot_is_auth_failure(monkeypatch, tmp_path, capsys):
    argv = run(monkeypatch, tmp_path, "brainstem", "health")
    FakeClient.responses["/health"] = {
        "status": "ok",
        "version": "0.6.16",
        "copilot": "no_access",
    }

    assert cli.main(argv) == 5

    assert "does not have Copilot access" in capsys.readouterr().err


def test_model_set_requires_confirmed_model(monkeypatch, tmp_path, capsys):
    argv = run(monkeypatch, tmp_path, "model", "set", "gpt-example")
    FakeClient.responses["/models/set"] = {}

    assert cli.main(argv) == 7

    assert "missing the selected model" in capsys.readouterr().err


def test_model_list_rejects_malformed_entries(monkeypatch, tmp_path, capsys):
    argv = run(monkeypatch, tmp_path, "model", "list")
    FakeClient.responses["/models"] = {
        "current": "good",
        "models": [{"id": "good"}, {"name": "missing id"}],
    }

    assert cli.main(argv) == 7

    assert "invalid model" in capsys.readouterr().err


def test_agent_import_http_200_error_is_failure(monkeypatch, tmp_path, capsys):
    source = tmp_path / "hello_agent.py"
    source.write_text("class HelloAgent: pass\n", encoding="utf-8")
    argv = run(monkeypatch, tmp_path, "agent", "import", str(source), "--yes")
    FakeClient.responses["/agents/import"] = {"error": "agent failed to load"}

    assert cli.main(argv) == 7

    assert "agent failed to load" in capsys.readouterr().err


def test_ring_status_uses_static_api(monkeypatch, tmp_path, capsys):
    class FakeReleaseTrain:
        def __init__(self, **_kwargs):
            pass

        def status(self):
            return {
                "schema": "rapp-static-api-status/1.0",
                "generated": "2026-01-01T00:00:00Z",
                "summary": {"entries": 1, "drift": 0, "versions": 1},
                "entries": [],
            }

    monkeypatch.setattr(commands, "ReleaseTrainClient", FakeReleaseTrain)
    argv = run(monkeypatch, tmp_path, "--json", "ring", "status")

    assert cli.main(argv) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["data"]["schema"] == "rapp-static-api-status/1.0"


def test_twin_list_reads_local_workspaces(monkeypatch, tmp_path, capsys):
    twin_home = tmp_path / "twins"
    twin = twin_home / "echo"
    twin.mkdir(parents=True)
    (twin / "rappid.json").write_text(
        json.dumps({"rappid": "rappid:echo", "name": "Echo"}),
        encoding="utf-8",
    )
    argv = run(
        monkeypatch,
        tmp_path,
        "--json",
        "twin",
        "legacy-list",
        "--home",
        str(twin_home),
    )

    assert cli.main(argv) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["data"]["twins"][0]["rappid"] == "rappid:echo"


def test_rar_install_passes_verified_source_to_brainstem(monkeypatch, tmp_path, capsys):
    class FakeRar:
        def __init__(self, **_kwargs):
            pass

        def info(self, name):
            return {
                "name": name,
                "_file": "agents/@rapp/example_agent.py",
                "_install_filename": "rar_rapp_example_agent.py",
                "_sha256": "a" * 64,
            }

        def source(self, _agent):
            return "rar_rapp_example_agent.py", b"trusted", "a" * 64

    monkeypatch.setattr(commands, "RarClient", FakeRar)
    argv = run(
        monkeypatch,
        tmp_path,
        "agent",
        "install",
        "@rapp/example",
        "--yes",
    )
    FakeClient.responses["/agents/import"] = {"status": "ok"}

    assert cli.main(argv) == 0

    assert "installed @rapp/example" in capsys.readouterr().out
    assert FakeClient.posts[-1][1]["filename"] == "rar_rapp_example_agent.py"
    assert FakeClient.posts[-1][1]["source_revision"]


def test_rar_install_requires_confirmation(monkeypatch, tmp_path, capsys):
    argv = run(monkeypatch, tmp_path, "agent", "install", "@rapp/example")

    assert cli.main(argv) == 6

    assert "requires --yes" in capsys.readouterr().err


def test_rar_install_rejects_dependency_only_entry(monkeypatch, tmp_path, capsys):
    class FakeRar:
        def __init__(self, **_kwargs):
            pass

        def info(self, _name):
            return {
                "name": "@rapp/basic_agent",
                "_file": "agents/@rapp/basic_agent.py",
                "_install_filename": "rar_rapp_basic_agent.py",
                "_sha256": "a" * 64,
            }

    monkeypatch.setattr(commands, "RarClient", FakeRar)
    argv = run(
        monkeypatch,
        tmp_path,
        "agent",
        "install",
        "@rapp/basic_agent",
        "--yes",
    )

    assert cli.main(argv) == 3

    assert "not installable" in capsys.readouterr().err
