#!/usr/bin/env python3
"""Dependency-free structural verification for rapp-messaging."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def load(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def main():
    registry = load(ROOT / "registry.json")
    assert registry["schema"] == "rapp-messaging-registry/1.0"

    ids = set()
    for relative in registry["schemas"]:
        path = ROOT / relative
        assert path.is_file(), f"missing schema: {relative}"
        schema = load(path)
        schema_id = schema["$id"]
        assert schema_id not in ids, f"duplicate schema id: {schema_id}"
        ids.add(schema_id)
        assert schema["$schema"].endswith("2020-12/schema")

    for spec in registry["specs"]:
        path = ROOT / spec["path"]
        assert path.is_file(), f"missing spec: {spec['path']}"
        assert spec["id"] in path.read_text(encoding="utf-8")

    vectors = load(ROOT / registry["vectors"])
    assert vectors["schema"] == "rapp-messaging-vectors/1.0"
    vector_ids = [item["id"] for item in vectors["vectors"]]
    assert len(vector_ids) == len(set(vector_ids))
    assert all(item["level"] in {"MUST", "SHOULD"} for item in vectors["vectors"])
    assert len(vector_ids) >= 10

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "not a new chat endpoint" in readme
    assert "OpenRappter" in readme
    print(
        f"PASS: {len(registry['specs'])} specs, "
        f"{len(ids)} schemas, {len(vector_ids)} vectors"
    )


if __name__ == "__main__":
    main()
