from __future__ import annotations

import io
import json
from pathlib import Path

from rapp_cli.errors import RemoteFailure
from rapp_cli.output import Output


def test_human_output_escapes_terminal_controls():
    stdout = io.StringIO()
    output = Output(stdout=stdout)

    output.success("ignored", message="safe\x1b[2Jtext\r")

    assert stdout.getvalue() == "safe\\x1b[2Jtext\\x0d\n"


def test_json_error_is_one_stdout_document():
    stdout = io.StringIO()
    stderr = io.StringIO()
    output = Output(
        json_mode=True,
        command="status",
        stdout=stdout,
        stderr=stderr,
    )

    output.error(RemoteFailure("failed", details={"path": Path("/tmp/example")}))

    payload = json.loads(stdout.getvalue())
    assert payload["error"]["code"] == "REMOTE_FAILED"
    assert payload["error"]["details"]["path"] == str(Path("/tmp/example"))
    assert stderr.getvalue() == ""


def test_jsonl_error_is_one_compact_line():
    stdout = io.StringIO()
    output = Output(
        json_mode=True,
        jsonl_mode=True,
        command="chat",
        stdout=stdout,
    )

    output.error(RemoteFailure("failed"))

    assert len(stdout.getvalue().splitlines()) == 1
    assert json.loads(stdout.getvalue())["error"]["code"] == "REMOTE_FAILED"
