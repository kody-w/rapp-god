from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .client import BrainstemClient
from .config import Config, normalize_base_url
from .errors import RemoteFailure

DEFAULT_RELEASE_TRAIN_URL = "https://raw.githubusercontent.com/kody-w/rapp-release-train/main"
RINGS = ("canary", "nightly", "alpha", "beta", "grail")


class ReleaseTrainClient:
    def __init__(
        self,
        *,
        timeout: float,
        source: str | None = None,
        allow_insecure_http: bool = False,
    ) -> None:
        url = source or os.environ.get("RAPP_RELEASE_TRAIN_URL") or DEFAULT_RELEASE_TRAIN_URL
        config = Config(
            brainstem_url=normalize_base_url(
                url,
                allow_insecure_http=allow_insecure_http,
            ),
            timeout=timeout,
            secret=None,
            config_path=Path("<release-train>"),
        )
        self._client = BrainstemClient(config, service_name="RAPP release train")

    def status(self) -> dict[str, Any]:
        payload = self._client.get_json("/api/v1/status.json")
        if not isinstance(payload, dict) or payload.get("schema") != "rapp-static-api-status/1.0":
            raise RemoteFailure("release train returned an unsupported status schema")
        if not isinstance(payload.get("entries"), list) or not isinstance(
            payload.get("summary"), dict
        ):
            raise RemoteFailure("release train status is missing entries or summary")
        summary = payload["summary"]
        if not all(
            isinstance(summary.get(key), int) and not isinstance(summary.get(key), bool)
            for key in ("entries", "drift", "versions")
        ):
            raise RemoteFailure("release train status summary has invalid counters")
        for entry in payload["entries"]:
            if not isinstance(entry, dict):
                raise RemoteFailure("release train status contains a non-object entry")
            if (
                not isinstance(entry.get("name"), str)
                or not isinstance(entry.get("drift"), bool)
                or not isinstance(entry.get("primary_sha8"), str)
                or not isinstance(entry.get("versions"), int)
                or isinstance(entry.get("versions"), bool)
            ):
                raise RemoteFailure("release train status contains an invalid entry")
        return payload

    def manifest(self) -> dict[str, Any]:
        payload = self._client.get_json("/manifest.json")
        if not isinstance(payload, dict) or payload.get("schema") != "rapp-static-api/1.0":
            raise RemoteFailure("release train returned an unsupported manifest schema")
        if not isinstance(payload.get("entries"), list):
            raise RemoteFailure("release train manifest is missing entries")
        for entry in payload["entries"]:
            if (
                not isinstance(entry, dict)
                or not isinstance(entry.get("name"), str)
                or not isinstance(entry.get("sources"), list)
            ):
                raise RemoteFailure("release train manifest contains an invalid entry")
            for source in entry["sources"]:
                if (
                    not isinstance(source, dict)
                    or not isinstance(source.get("label"), str)
                    or not isinstance(source.get("url"), str)
                ):
                    raise RemoteFailure("release train manifest contains an invalid source")
        return payload
