from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path

import pytest

import rapp_cli.twin_hatch as twin_hatch_module
from rapp_cli import cli, commands
from rapp_cli.config import Config
from rapp_cli.errors import (
    CapabilityUnavailable,
    Conflict,
    IntegrityFailure,
    NotFound,
    RemoteFailure,
    UsageError,
)
from rapp_cli.output import Output
from rapp_cli.twin_hatch import hatch_twin, prepare_twin

IDENTITY = "a" * 64
RAPPID = f"rappid:@owner/example:{IDENTITY}"


class FakeClient:
    def __init__(
        self,
        installed: dict[str, bytes] | None = None,
        *,
        list_response: object | None = None,
        import_responses: dict[str, object] | None = None,
        loaded_agents: dict[str, list[str]] | None = None,
    ) -> None:
        self.installed = dict(installed or {})
        self.list_response = list_response
        self.import_responses = dict(import_responses or {})
        self.loaded_agents = {
            filename: [filename.removesuffix("_agent.py")] for filename in self.installed
        }
        if loaded_agents is not None:
            self.loaded_agents.update(loaded_agents)
        self.calls: list[tuple[str, object]] = []

    def get_json(self, path: str):
        self.calls.append(("get", path))
        if self.list_response is not None:
            return self.list_response
        return {
            "files": [
                {
                    "filename": filename,
                    "agents": self.loaded_agents.get(filename, []),
                }
                for filename in sorted(self.installed)
            ]
        }

    def export_agent(self, filename: str) -> bytes:
        self.calls.append(("export", filename))
        try:
            return self.installed[filename]
        except KeyError as exc:
            raise NotFound(f"missing {filename}") from exc

    def import_agent(
        self,
        filename: str,
        payload: bytes,
        *,
        sha256: str | None = None,
        source_revision: str | None = None,
    ):
        self.calls.append(
            (
                "import",
                {
                    "filename": filename,
                    "payload": payload,
                    "sha256": sha256,
                    "source_revision": source_revision,
                },
            )
        )
        response = self.import_responses.get(filename, {"status": "ok"})
        if isinstance(response, Exception):
            raise response
        if not (isinstance(response, dict) and response.get("error")):
            self.installed[filename] = payload
            self.loaded_agents.setdefault(
                filename,
                [filename.removesuffix("_agent.py")],
            )
        return response

    def remove_agent(self, filename: str):
        self.calls.append(("remove", filename))
        self.installed.pop(filename, None)
        self.loaded_agents.pop(filename, None)
        return {"status": "ok"}


def write_twin(
    root: Path,
    *,
    rappid: str = RAPPID,
    metadata: dict[str, object] | None = None,
    soul: bytes = b"A prepared soul.\n",
    agents: dict[str, bytes] | None = None,
) -> Path:
    root.mkdir()
    document: dict[str, object] = {
        "schema": "rapp/1",
        "kind": "twin",
        "rappid": rappid,
        "name": "Example",
    }
    if metadata:
        document.update(metadata)
    (root / "rappid.json").write_text(json.dumps(document), encoding="utf-8")
    (root / "soul.md").write_bytes(soul)
    agent_root = root / "agents"
    agent_root.mkdir()
    agent_payloads = (
        {"example_agent.py": b"class ExampleAgent: pass\n"} if agents is None else agents
    )
    for filename, payload in agent_payloads.items():
        (agent_root / filename).write_bytes(payload)
    return root


def test_hatch_success_preserves_safe_tree_and_writes_private_receipt(tmp_path):
    source = write_twin(
        tmp_path / "source",
        metadata={
            "display_name": "Example Twin",
            "parent_rappid": "rappid:@owner/parent:" + "b" * 64,
            "contact": "do-not-copy-to-result@example.test",
        },
    )
    (source / "frames").mkdir()
    (source / "frames" / "frame.bin").write_bytes(b"\x00\xffframe")
    (source / "memory.md").write_bytes(b"memory bytes\n")
    (source / "PROVENANCE.md").write_bytes(b"provenance bytes\n")
    original = {
        path.relative_to(source).as_posix(): path.read_bytes()
        for path in source.rglob("*")
        if path.is_file()
    }
    home = tmp_path / "twins"
    client = FakeClient()

    outcome = hatch_twin(
        client,
        source,
        home=home,
        endpoint="http://127.0.0.1:7071",
        confirmed=True,
    )

    target = home / IDENTITY
    assert outcome.materialization == "created"
    assert outcome.path == target
    assert outcome.agents[0].status == "imported"
    assert {
        path.relative_to(target).as_posix(): path.read_bytes()
        for path in target.rglob("*")
        if path.is_file()
    } == original
    uploaded = next(value for operation, value in client.calls if operation == "import")
    assert uploaded["sha256"] == hashlib.sha256(original["agents/example_agent.py"]).hexdigest()
    result_text = json.dumps(outcome.to_dict())
    assert "A prepared soul" not in result_text
    assert "class ExampleAgent" not in result_text
    assert "do-not-copy-to-result" not in result_text
    receipts = list((home / ".receipts").glob("*.json"))
    assert len(receipts) == 1
    receipt_text = receipts[0].read_text(encoding="utf-8")
    assert "A prepared soul" not in receipt_text
    assert "class ExampleAgent" not in receipt_text
    assert "do-not-copy-to-result" not in receipt_text
    if os.name == "posix":
        assert receipts[0].stat().st_mode & 0o077 == 0


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"schema": "rapp/2"}, "schema"),
        ({"kind": "egg"}, "kind"),
        ({"rappid": "rappid:legacy:" + "a" * 64}, "canonical"),
        ({"rappid": "rappid:@owner/slug:" + "A" * 64}, "canonical"),
        ({"rappid": "rappid:@owner/../slug:" + "a" * 64}, "canonical"),
        ({"name": 7}, "name"),
        ({"display_name": False}, "display_name"),
    ],
)
def test_hatch_rejects_noncanonical_identity_metadata(tmp_path, change, message):
    source = write_twin(tmp_path / "source", metadata=change)

    with pytest.raises(UsageError, match=message):
        prepare_twin(source)


@pytest.mark.parametrize(
    "raw",
    [
        b"[]",
        b'{"schema":"rapp/1","schema":"rapp/1"}',
        b'{"schema":"rapp/1","kind":"twin"}',
    ],
)
def test_hatch_requires_strict_identity_object(tmp_path, raw):
    source = write_twin(tmp_path / "source")
    (source / "rappid.json").write_bytes(raw)

    with pytest.raises(UsageError):
        prepare_twin(source)


def test_hatch_accepts_organism_kind_without_rewriting_metadata(tmp_path):
    source = write_twin(tmp_path / "source", metadata={"kind": "organism"})
    original = (source / "rappid.json").read_bytes()

    prepared = prepare_twin(source)

    assert prepared.kind == "organism"
    assert (source / "rappid.json").read_bytes() == original


@pytest.mark.parametrize("soul", [None, b"", b" \n\t", b"\xef\xbb\xbf \n"])
def test_hatch_requires_nonempty_utf8_soul(tmp_path, soul):
    source = write_twin(tmp_path / "source")
    if soul is None:
        (source / "soul.md").unlink()
    else:
        (source / "soul.md").write_bytes(soul)

    with pytest.raises(UsageError, match="soul.md"):
        prepare_twin(source)


def test_hatch_requires_immediate_agent(tmp_path):
    source = write_twin(tmp_path / "source", agents={})
    nested = source / "agents" / "nested"
    nested.mkdir()
    (nested / "nested_agent.py").write_text("pass\n", encoding="utf-8")

    with pytest.raises(UsageError, match="immediate"):
        prepare_twin(source)


def test_hatch_rejects_invalid_agent_filename(tmp_path):
    source = write_twin(
        tmp_path / "source",
        agents={"bad name_agent.py": b"pass\n"},
    )

    with pytest.raises(UsageError, match="agent filename"):
        prepare_twin(source)


def test_hatch_rejects_case_insensitive_duplicate_source_agents():
    files = {
        "agents/Example_agent.py": b"class First: pass\n",
        "agents/example_agent.py": b"class Second: pass\n",
    }

    with pytest.raises(UsageError, match="case-insensitive duplicate"):
        twin_hatch_module._agents(files)


@pytest.mark.skipif(os.name == "nt", reason="symlink creation is not reliably available")
@pytest.mark.parametrize("link_kind", ["root", "file", "directory"])
def test_hatch_rejects_symlinks(tmp_path, link_kind):
    source = write_twin(tmp_path / "source")
    candidate = source
    if link_kind == "root":
        candidate = tmp_path / "linked"
        candidate.symlink_to(source, target_is_directory=True)
    elif link_kind == "file":
        target = source / "notes-target.md"
        target.write_text("notes\n", encoding="utf-8")
        (source / "notes.md").symlink_to(target)
    else:
        target = tmp_path / "external"
        target.mkdir()
        (source / "linked-directory").symlink_to(target, target_is_directory=True)

    with pytest.raises(IntegrityFailure, match="symlink"):
        prepare_twin(candidate)


def test_hatch_rejects_reparse_points(tmp_path, monkeypatch):
    source = write_twin(tmp_path / "source")
    original = twin_hatch_module.is_reparse_point
    monkeypatch.setattr(
        twin_hatch_module,
        "is_reparse_point",
        lambda path: path == source or original(path),
    )

    with pytest.raises(IntegrityFailure, match="reparse"):
        prepare_twin(source)


@pytest.mark.skipif(os.name == "nt", reason="symlink creation is not reliably available")
def test_hatch_rejects_directory_swapped_to_symlink_after_enumeration(
    tmp_path,
    monkeypatch,
):
    source = write_twin(tmp_path / "source")
    nested = source / "nested"
    nested.mkdir()
    (nested / "safe.txt").write_text("safe\n", encoding="utf-8")
    external = tmp_path / "external"
    external.mkdir()
    (external / "outside.txt").write_text("must not be read\n", encoding="utf-8")
    held = source / "nested-held"
    swapped = False

    def swap_after_root(relative_path):
        nonlocal swapped
        if relative_path == "" and not swapped:
            nested.rename(held)
            nested.symlink_to(external, target_is_directory=True)
            swapped = True

    monkeypatch.setattr(
        twin_hatch_module,
        "_after_directory_enumeration",
        swap_after_root,
    )

    with pytest.raises(IntegrityFailure, match="changed|symlink"):
        prepare_twin(source)


def test_hatch_fails_closed_without_secure_directory_handles(tmp_path, monkeypatch):
    source = write_twin(tmp_path / "source")
    monkeypatch.setattr(twin_hatch_module, "_secure_walk_supported", lambda: False)

    with pytest.raises(CapabilityUnavailable, match="fails closed"):
        prepare_twin(source)


@pytest.mark.skipif(os.name == "nt", reason="backslash is not a valid Windows filename")
def test_hatch_rejects_traversal_like_relative_names(tmp_path):
    source = write_twin(tmp_path / "source")
    (source / "..\\escape").write_text("data\n", encoding="utf-8")

    with pytest.raises(IntegrityFailure, match="traversal-like"):
        prepare_twin(source)


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFO creation is unavailable")
def test_hatch_rejects_special_files_without_reading_them(tmp_path):
    source = write_twin(tmp_path / "source")
    os.mkfifo(source / "pipe")

    with pytest.raises(IntegrityFailure, match="regular file"):
        prepare_twin(source)


@pytest.mark.parametrize(
    "relative_path",
    [".lineage_key", ".copilot_token", ".env", "nested/private/notes.md"],
)
def test_hatch_rejects_forbidden_secret_paths(tmp_path, relative_path):
    source = write_twin(tmp_path / "source")
    forbidden = source / Path(relative_path)
    forbidden.parent.mkdir(parents=True, exist_ok=True)
    forbidden.write_text("secret", encoding="utf-8")

    with pytest.raises(IntegrityFailure, match="forbidden secret"):
        prepare_twin(source)


@pytest.mark.parametrize("semantic_file", ["soul.md", "rappid.json"])
def test_hatch_rejects_invalid_utf8_semantic_text(tmp_path, semantic_file):
    source = write_twin(tmp_path / "source")
    (source / semantic_file).write_bytes(b"\xff")

    with pytest.raises(UsageError, match="UTF-8"):
        prepare_twin(source)


def test_hatch_enforces_per_file_size_bound(tmp_path, monkeypatch):
    source = write_twin(
        tmp_path / "source",
        agents={"example_agent.py": b"x" * 257},
    )
    monkeypatch.setattr(twin_hatch_module, "MAX_TWIN_FILE_BYTES", 256)

    with pytest.raises(UsageError, match="per-file"):
        prepare_twin(source)


def test_hatch_enforces_file_count_and_total_bounds(tmp_path, monkeypatch):
    source = write_twin(tmp_path / "source")
    monkeypatch.setattr(twin_hatch_module, "MAX_TWIN_FILES", 2)
    with pytest.raises(UsageError, match="file limit"):
        prepare_twin(source)

    monkeypatch.setattr(twin_hatch_module, "MAX_TWIN_FILES", 4096)
    payload_total = sum(path.stat().st_size for path in source.rglob("*") if path.is_file())
    monkeypatch.setattr(twin_hatch_module, "MAX_TWIN_TOTAL_BYTES", payload_total - 1)
    with pytest.raises(UsageError, match="total payload"):
        prepare_twin(source)


def test_maximal_agent_receipt_is_within_retry_read_bound(tmp_path):
    suffix = "_agent.py"
    agents = []
    for index in range(twin_hatch_module.MAX_TWIN_FILES):
        prefix = f"a{index:04x}"
        filename = prefix + "x" * (255 - len(prefix) - len(suffix)) + suffix
        twin_hatch_module.validate_agent_filename(filename)
        agents.append(
            twin_hatch_module.TwinAgent(
                filename=filename,
                payload=b"",
                sha256="c" * 64,
            )
        )
    prepared = twin_hatch_module.PreparedTwin(
        source=tmp_path / "source",
        rappid=f"rappid:@{'o' * 39}/{'s' * 100}:{IDENTITY}",
        kind="organism",
        identity_hash=IDENTITY,
        tree_sha256="b" * 64,
        entries=(),
        agents=tuple(agents),
        file_count=twin_hatch_module.MAX_TWIN_FILES,
        total_bytes=0,
    )

    payload = twin_hatch_module._receipt_payload(prepared)

    assert len(payload) <= twin_hatch_module.MAX_TWIN_RECEIPT_BYTES
    home = tmp_path / "twins"
    home.mkdir()
    twin_hatch_module._write_receipt(home, prepared, payload)
    twin_hatch_module._write_receipt(home, prepared, payload)
    receipt = home / ".receipts" / f"{prepared.tree_sha256}.json"
    assert receipt.read_bytes() == payload


def test_agent_filename_bound_supports_receipt_proof():
    suffix = "_agent.py"
    largest = "a" * (255 - len(suffix)) + suffix
    too_large = "a" * (256 - len(suffix)) + suffix

    assert twin_hatch_module.validate_agent_filename(largest) == largest
    with pytest.raises(UsageError, match="at most 255"):
        twin_hatch_module.validate_agent_filename(too_large)


def test_oversized_receipt_is_rejected_before_materialization(tmp_path, monkeypatch):
    source = write_twin(tmp_path / "source")
    home = tmp_path / "twins"
    client = FakeClient()
    monkeypatch.setattr(twin_hatch_module, "MAX_TWIN_RECEIPT_BYTES", 1)

    with pytest.raises(UsageError, match="generated Twin receipt"):
        hatch_twin(
            client,
            source,
            home=home,
            endpoint="http://127.0.0.1:7071",
            confirmed=True,
        )

    assert not home.exists()
    assert client.calls == []


def test_tree_digest_is_deterministic_and_covers_paths_and_bytes(tmp_path):
    first = write_twin(tmp_path / "first")
    second = write_twin(tmp_path / "second")
    (first / "z").mkdir()
    (first / "z" / "value.bin").write_bytes(b"value")
    (first / "empty").mkdir()
    (second / "empty").mkdir()
    (second / "z").mkdir()
    (second / "z" / "value.bin").write_bytes(b"value")

    first_digest = prepare_twin(first).tree_sha256
    second_digest = prepare_twin(second).tree_sha256
    assert first_digest == second_digest

    (second / "z" / "value.bin").write_bytes(b"changed")
    assert prepare_twin(second).tree_sha256 != first_digest


def test_agent_content_is_treated_as_inert_data(tmp_path):
    source = write_twin(
        tmp_path / "source",
        agents={
            "malicious_agent.py": (
                b"from pathlib import Path\n"
                b"Path(__file__).with_name('executed').write_text('bad')\n"
            )
        },
    )
    client = FakeClient()

    hatch_twin(
        client,
        source,
        home=tmp_path / "twins",
        endpoint="http://127.0.0.1:7071",
        confirmed=True,
    )

    assert not (source / "agents" / "executed").exists()
    assert not list(source.rglob("__pycache__"))


@pytest.mark.parametrize("relationship", ["same", "home-inside-source", "source-inside-home"])
def test_hatch_rejects_source_home_overlap_before_mutation_or_network(
    tmp_path,
    relationship,
):
    if relationship == "source-inside-home":
        home = tmp_path / "twins"
        home.mkdir()
        source = write_twin(home / "prepared")
    else:
        source = write_twin(tmp_path / "source")
        home = source if relationship == "same" else source / "twins"
    client = FakeClient()

    with pytest.raises(UsageError, match="must not contain one another"):
        hatch_twin(
            client,
            source,
            home=home,
            endpoint="http://127.0.0.1:7071",
            confirmed=True,
        )

    assert client.calls == []
    assert not (home / ".locks").exists()
    if relationship == "home-inside-source":
        assert not home.exists()


def test_hatch_rejects_case_variant_filesystem_alias_overlap(tmp_path):
    probe = tmp_path / "CaseSensitivityProbe"
    probe.mkdir()
    case_insensitive = (tmp_path / "casesensitivityprobe").exists()
    probe.rmdir()
    if not case_insensitive:
        pytest.skip("test volume is case-sensitive")

    container = tmp_path / "CaseAliasRoot"
    container.mkdir()
    source = write_twin(container / "SourceTwin")
    container_alias = container.with_name(container.name.swapcase())
    source_alias = container_alias / source.name.swapcase()
    nonexistent_descendant = source_alias / "TwinHome"

    for home in (container_alias, nonexistent_descendant):
        client = FakeClient()
        with pytest.raises(UsageError, match="must not contain one another"):
            hatch_twin(
                client,
                source,
                home=home,
                endpoint="http://127.0.0.1:7071",
                confirmed=True,
            )
        assert client.calls == []

    assert not nonexistent_descendant.exists()
    assert not (container / ".locks").exists()


def test_identity_advisory_lock_rejects_concurrent_cli_hatch(tmp_path):
    source = write_twin(tmp_path / "source")
    home = tmp_path / "twins"
    home.mkdir()
    client = FakeClient()

    with (
        twin_hatch_module._identity_lock(home, IDENTITY),
        pytest.raises(Conflict, match="already running"),
    ):
        hatch_twin(
            client,
            source,
            home=home,
            endpoint="http://127.0.0.1:7071",
            confirmed=True,
        )

    assert client.calls == []
    assert (home / ".locks" / f"{IDENTITY}.lock").is_file()


def test_materialization_failure_cleans_stage_before_provider_contact(tmp_path, monkeypatch):
    source = write_twin(tmp_path / "source")
    home = tmp_path / "twins"
    client = FakeClient()

    def fail_install(_source, _target):
        raise OSError("simulated install failure")

    monkeypatch.setattr(twin_hatch_module, "_rename_no_replace", fail_install)

    with pytest.raises(UsageError, match="atomically install"):
        hatch_twin(
            client,
            source,
            home=home,
            endpoint="http://127.0.0.1:7071",
            confirmed=True,
        )

    assert not (home / IDENTITY).exists()
    assert not list(home.glob(".hatch-*"))
    assert not list((home / ".receipts").glob("*.json"))
    assert client.installed == {}
    assert client.calls == []


def test_existing_identical_target_and_agent_are_idempotent(tmp_path):
    source = write_twin(tmp_path / "source")
    home = tmp_path / "twins"
    agent = (source / "agents" / "example_agent.py").read_bytes()
    first_client = FakeClient()
    hatch_twin(
        first_client,
        source,
        home=home,
        endpoint="http://127.0.0.1:7071",
        confirmed=True,
    )
    second_client = FakeClient({"example_agent.py": agent})

    outcome = hatch_twin(
        second_client,
        source,
        home=home,
        endpoint="http://127.0.0.1:7071",
        confirmed=True,
    )

    assert outcome.materialization == "existing"
    assert outcome.agents[0].status == "existing"
    assert all(operation != "import" for operation, _value in second_client.calls)


def test_existing_different_target_conflicts_before_network(tmp_path):
    source = write_twin(tmp_path / "source")
    home = tmp_path / "twins"
    target = home / IDENTITY
    target.parent.mkdir()
    shutil.copytree(source, target)
    (target / "soul.md").write_text("different\n", encoding="utf-8")
    client = FakeClient()

    with pytest.raises(Conflict, match="differs"):
        hatch_twin(
            client,
            source,
            home=home,
            endpoint="http://127.0.0.1:7071",
            confirmed=True,
        )

    assert client.calls == []


def test_identical_target_winning_install_race_is_idempotent(tmp_path, monkeypatch):
    source = write_twin(tmp_path / "source")
    home = tmp_path / "twins"

    def win_race(stage, target):
        shutil.copytree(stage, target)
        raise FileExistsError("simulated identical winner")

    monkeypatch.setattr(twin_hatch_module, "_rename_no_replace", win_race)

    outcome = hatch_twin(
        FakeClient(),
        source,
        home=home,
        endpoint="http://127.0.0.1:7071",
        confirmed=True,
    )

    assert outcome.materialization == "existing"
    assert not list(home.glob(".hatch-*"))


def test_different_target_winning_install_race_conflicts_without_removal(tmp_path, monkeypatch):
    source = write_twin(tmp_path / "source")
    home = tmp_path / "twins"
    client = FakeClient()

    def win_race(stage, target):
        shutil.copytree(stage, target)
        (target / "soul.md").write_text("race winner\n", encoding="utf-8")
        raise FileExistsError("simulated different winner")

    monkeypatch.setattr(twin_hatch_module, "_rename_no_replace", win_race)

    with pytest.raises(Conflict, match="differs"):
        hatch_twin(
            client,
            source,
            home=home,
            endpoint="http://127.0.0.1:7071",
            confirmed=True,
        )

    assert (home / IDENTITY / "soul.md").read_text(encoding="utf-8") == "race winner\n"
    assert client.installed == {}
    assert not list((home / ".receipts").glob("*.json"))


def test_existing_different_brainstem_agent_conflicts_without_upload(tmp_path):
    source = write_twin(tmp_path / "source")
    client = FakeClient({"example_agent.py": b"different"})
    home = tmp_path / "twins"

    with pytest.raises(Conflict, match="different source"):
        hatch_twin(
            client,
            source,
            home=home,
            endpoint="http://127.0.0.1:7071",
            confirmed=True,
        )

    assert all(operation != "import" for operation, _value in client.calls)
    assert (home / IDENTITY).is_dir()
    assert list((home / ".receipts").glob("*.json"))
    assert not list(home.glob(".hatch-*"))


def test_broken_existing_agent_is_not_idempotent_success(tmp_path):
    source = write_twin(tmp_path / "source")
    payload = (source / "agents" / "example_agent.py").read_bytes()
    client = FakeClient(
        {"example_agent.py": payload},
        loaded_agents={"example_agent.py": []},
    )

    with pytest.raises(RemoteFailure, match="reports no loaded agents"):
        hatch_twin(
            client,
            source,
            home=tmp_path / "twins",
            endpoint="http://127.0.0.1:7071",
            confirmed=True,
        )

    assert all(operation != "import" for operation, _value in client.calls)


def test_case_only_brainstem_agent_collision_conflicts(tmp_path):
    source = write_twin(tmp_path / "source")
    payload = (source / "agents" / "example_agent.py").read_bytes()
    client = FakeClient({"Example_agent.py": payload})

    with pytest.raises(Conflict, match="case-only"):
        hatch_twin(
            client,
            source,
            home=tmp_path / "twins",
            endpoint="http://127.0.0.1:7071",
            confirmed=True,
        )

    assert all(operation not in {"export", "import"} for operation, _value in client.calls)


def test_partial_import_failure_retains_retryable_local_and_provider_state(tmp_path):
    source = write_twin(
        tmp_path / "source",
        agents={
            "first_agent.py": b"class First: pass\n",
            "second_agent.py": b"class Second: pass\n",
        },
    )
    client = FakeClient(
        import_responses={"second_agent.py": {"error": "second failed"}},
    )

    with pytest.raises(RemoteFailure, match="second failed"):
        hatch_twin(
            client,
            source,
            home=tmp_path / "twins",
            endpoint="http://127.0.0.1:7071",
            confirmed=True,
        )

    home = tmp_path / "twins"
    assert set(client.installed) == {"first_agent.py"}
    assert all(operation != "remove" for operation, _value in client.calls)
    assert (home / IDENTITY).is_dir()
    assert list((home / ".receipts").glob("*.json"))

    retry = FakeClient(client.installed)
    outcome = hatch_twin(
        retry,
        source,
        home=home,
        endpoint="http://127.0.0.1:7071",
        confirmed=True,
    )

    assert [agent.status for agent in outcome.agents] == ["existing", "imported"]
    assert set(retry.installed) == {"first_agent.py", "second_agent.py"}


def test_failed_load_remains_failure_on_idempotent_retry(tmp_path):
    class BrokenLoadClient(FakeClient):
        def import_agent(
            self,
            filename,
            payload,
            *,
            sha256=None,
            source_revision=None,
        ):
            response = super().import_agent(
                filename,
                payload,
                sha256=sha256,
                source_revision=source_revision,
            )
            self.loaded_agents[filename] = []
            return response

    source = write_twin(tmp_path / "source")
    client = BrokenLoadClient()
    home = tmp_path / "twins"

    with pytest.raises(RemoteFailure, match="reports no loaded agents"):
        hatch_twin(
            client,
            source,
            home=home,
            endpoint="http://127.0.0.1:7071",
            confirmed=True,
        )

    assert (home / IDENTITY).is_dir()
    assert list((home / ".receipts").glob("*.json"))
    assert [operation for operation, _value in client.calls].count("import") == 1

    with pytest.raises(RemoteFailure, match="reports no loaded agents"):
        hatch_twin(
            client,
            source,
            home=home,
            endpoint="http://127.0.0.1:7071",
            confirmed=True,
        )

    assert [operation for operation, _value in client.calls].count("import") == 1
    assert all(operation != "remove" for operation, _value in client.calls)


def test_provider_error_retained_upload_stays_failed_on_retry(tmp_path):
    class RetainingErrorClient(FakeClient):
        def import_agent(
            self,
            filename,
            payload,
            *,
            sha256=None,
            source_revision=None,
        ):
            super().import_agent(
                filename,
                payload,
                sha256=sha256,
                source_revision=source_revision,
            )
            self.loaded_agents[filename] = []
            return {"error": "saved but failed to load"}

    source = write_twin(tmp_path / "source")
    client = RetainingErrorClient()
    home = tmp_path / "twins"

    with pytest.raises(RemoteFailure, match="saved but failed to load"):
        hatch_twin(
            client,
            source,
            home=home,
            endpoint="http://127.0.0.1:7071",
            confirmed=True,
        )

    with pytest.raises(RemoteFailure, match="reports no loaded agents"):
        hatch_twin(
            client,
            source,
            home=home,
            endpoint="http://127.0.0.1:7071",
            confirmed=True,
        )

    assert [operation for operation, _value in client.calls].count("import") == 1
    assert all(operation != "remove" for operation, _value in client.calls)


def test_post_import_export_hash_must_match_before_success(tmp_path):
    class TamperingClient(FakeClient):
        def import_agent(
            self,
            filename,
            payload,
            *,
            sha256=None,
            source_revision=None,
        ):
            response = super().import_agent(
                filename,
                payload,
                sha256=sha256,
                source_revision=source_revision,
            )
            self.installed[filename] = b"replacement from another writer"
            return response

    source = write_twin(tmp_path / "source")
    client = TamperingClient()
    home = tmp_path / "twins"

    with pytest.raises(Conflict, match="changed during import verification"):
        hatch_twin(
            client,
            source,
            home=home,
            endpoint="http://127.0.0.1:7071",
            confirmed=True,
        )

    assert client.installed["example_agent.py"] == b"replacement from another writer"
    assert all(operation != "remove" for operation, _value in client.calls)
    assert (home / IDENTITY).is_dir()


def test_non_ok_import_status_is_failure_without_delete(tmp_path):
    source = write_twin(tmp_path / "source")
    client = FakeClient(import_responses={"example_agent.py": {"status": "pending"}})

    with pytest.raises(RemoteFailure, match="non-ok status"):
        hatch_twin(
            client,
            source,
            home=tmp_path / "twins",
            endpoint="http://127.0.0.1:7071",
            confirmed=True,
        )

    assert set(client.installed) == {"example_agent.py"}
    assert all(operation != "remove" for operation, _value in client.calls)


@pytest.mark.parametrize(
    "response",
    [
        [],
        {"files": [None]},
        {"files": [{"filename": "../bad_agent.py"}]},
        {"files": [{"filename": "example_agent.py"}]},
        {"files": [{"filename": "example_agent.py", "agents": "Example"}]},
        {"files": [{"filename": "example_agent.py", "agents": [""]}]},
        {"files": [{"filename": "example_agent.py", "agents": [7]}]},
        {
            "files": [
                {"filename": "Example_agent.py", "agents": ["Example"]},
                {"filename": "example_agent.py", "agents": ["example"]},
            ]
        },
        {"error": "provider failed"},
    ],
)
def test_hatch_rejects_malformed_or_failed_agents_response(tmp_path, response):
    source = write_twin(tmp_path / "source")

    with pytest.raises(RemoteFailure):
        hatch_twin(
            FakeClient(list_response=response),
            source,
            home=tmp_path / "twins",
            endpoint="http://127.0.0.1:7071",
            confirmed=True,
        )


def test_hatch_rejects_malformed_import_response_without_unsafe_delete(tmp_path):
    source = write_twin(tmp_path / "source")
    client = FakeClient(import_responses={"example_agent.py": []})

    with pytest.raises(RemoteFailure, match="JSON object"):
        hatch_twin(
            client,
            source,
            home=tmp_path / "twins",
            endpoint="http://127.0.0.1:7071",
            confirmed=True,
        )

    home = tmp_path / "twins"
    assert set(client.installed) == {"example_agent.py"}
    assert all(operation != "remove" for operation, _value in client.calls)
    assert (home / IDENTITY).is_dir()
    assert list((home / ".receipts").glob("*.json"))


def test_hatch_json_command_and_help(monkeypatch, tmp_path, capsys):
    source = write_twin(tmp_path / "source")
    home = tmp_path / "twins"
    client = FakeClient()
    monkeypatch.setattr(cli, "BrainstemClient", lambda _config: client)

    exit_code = cli.main(
        [
            "--config",
            str(tmp_path / "missing-config.json"),
            "--json",
            "twin",
            "hatch",
            str(source),
            "--yes",
            "--home",
            str(home),
        ]
    )

    assert exit_code == 0
    result = json.loads(capsys.readouterr().out)
    assert result["command"] == "twin.hatch"
    assert result["data"]["rappid"] == RAPPID
    assert result["data"]["endpoint"] == "http://127.0.0.1:7071"
    assert result["data"]["agents"][0]["status"] == "imported"

    with pytest.raises(SystemExit) as help_exit:
        cli.main(["twin", "hatch", "--help"])
    assert help_exit.value.code == 0
    help_output = capsys.readouterr().out
    assert "FOLDER" in help_output
    assert "--yes" in help_output
    assert "--home" in help_output


def test_hatch_requires_confirmation_before_config_source_or_network(monkeypatch, tmp_path, capsys):
    config_reads: list[bool] = []

    def fail_config_load(_cls, **_kwargs):
        config_reads.append(True)
        raise AssertionError("config must not be read")

    monkeypatch.setattr(cli.Config, "load", classmethod(fail_config_load))

    exit_code = cli.main(
        [
            "--json",
            "twin",
            "hatch",
            str(tmp_path / "missing-source"),
            "--home",
            str(tmp_path / "twins"),
        ]
    )

    assert exit_code == 6
    assert config_reads == []
    result = json.loads(capsys.readouterr().out)
    assert result["error"]["code"] == "CONFIRMATION_REQUIRED"


def test_canonical_list_show_aliases_and_receipts_are_hidden(monkeypatch, tmp_path, capsys):
    home = tmp_path / "twins"
    twin = home / IDENTITY
    twin.mkdir(parents=True)
    (twin / "rappid.json").write_text(
        json.dumps({"rappid": RAPPID, "name": "Example"}),
        encoding="utf-8",
    )
    (home / ".receipts").mkdir()
    (home / ".receipts" / "receipt.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(cli, "BrainstemClient", lambda _config: FakeClient())
    base = ["--config", str(tmp_path / "missing-config.json"), "--json", "twin"]

    assert cli.main([*base, "list", "--home", str(home)]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert listed["command"] == "twin.list"
    assert listed["data"]["legacy"] is False
    assert [item["id"] for item in listed["data"]["twins"]] == [IDENTITY]

    assert cli.main([*base, "show", RAPPID, "--home", str(home)]) == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["command"] == "twin.show"
    assert shown["data"]["id"] == IDENTITY

    assert cli.main([*base, "legacy-list", "--home", str(home)]) == 0
    legacy = json.loads(capsys.readouterr().out)
    assert legacy["data"]["legacy"] is True


def test_twin_capabilities_and_drive_identity(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(
        commands,
        "locate_brainstem",
        lambda: (_ for _ in ()).throw(UsageError("not installed")),
    )
    context = commands.Context(
        config=Config(
            brainstem_url="http://127.0.0.1:7071",
            timeout=1,
            secret=None,
            config_path=tmp_path / "config.json",
        ),
        client=FakeClient(),
        output=Output(),
    )

    capability = commands.capabilities(context, None).data["twin"]
    assert capability["implementation"] == "local_folder_hatch"
    assert capability["installed"] is True
    assert capability["commands"] == ["hatch", "list", "show"]
    assert capability["unavailable_commands"] == ["drive"]

    assert cli.main(["--json", "twin", "drive"]) == 3
    failure = json.loads(capsys.readouterr().out)
    assert failure["command"] == "twin.drive"
    assert failure["error"]["details"]["capability"] == "twin.drive"


def test_readme_and_security_document_hatch_contract():
    root = Path(__file__).resolve().parents[1]
    readme = (root / "README.md").read_text(encoding="utf-8")
    security = (root / "SECURITY.md").read_text(encoding="utf-8")

    for expected in (
        "rapp twin hatch FOLDER --yes",
        "rappid:@owner/slug:<64 lowercase hex>",
        "soul.md",
        "agents/",
        ".egg",
        "summon",
        "direct Twin driving",
    ):
        assert expected in readme
    for expected in (
        "symlink",
        ".lineage_key",
        ".copilot_token",
        ".env",
        "private",
        "16 MiB",
        "automatically deletes",
        "non-CLI",
    ):
        assert expected in security
