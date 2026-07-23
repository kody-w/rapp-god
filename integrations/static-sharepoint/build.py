#!/usr/bin/env python3
"""Build deterministic static SharePoint-style REST fixtures using only Python stdlib.

data/source.json is the compact authored truth. This script expands it into
classic SharePoint-REST-shaped JSON under site/ — every list served as
{"d": {"results": [...]}} — plus a lists index and a self-contained
site/index.html. UUIDv5 identifiers, a fixed UTC epoch, canonical sorted
JSON, and no wall clock or randomness make the output byte-reproducible.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
SOURCE_PATH = ROOT / "data" / "source.json"
SITE_ROOT = ROOT / "site"
API_ROOT = SITE_ROOT / "_api" / "web"
REPO_SLUG = "static-sharepoint"

LISTS: dict[str, dict[str, str]] = {
    "contracts": {
        "title": "Contracts",
        "path": "Contracts",
        "entity_type": "SP.Data.ContractsListItem",
        "list_entity": "ContractsList",
        "description": "Executed and in-flight customer agreements: MSAs, SOWs, and renewals.",
    },
    "policies": {
        "title": "Policies",
        "path": "Policies",
        "entity_type": "SP.Data.PoliciesListItem",
        "list_entity": "PoliciesList",
        "description": "Internal HR, benefits, finance, security, and compliance policies.",
    },
    "meetingnotes": {
        "title": "Meeting Notes",
        "path": "MeetingNotes",
        "entity_type": "SP.Data.Meeting_x0020_NotesListItem",
        "list_entity": "Meeting_x0020_NotesList",
        "description": "Customer and internal meeting notes referencing CRM cases and opportunities.",
    },
}

CONTRACT_TYPES = ("MSA", "SOW", "Renewal", "Services Agreement")
CONTRACT_STATUSES = ("Draft", "In Review", "Active", "Renewal Pending", "Expired")
POLICY_CATEGORIES = ("HR", "Benefits", "Finance", "Security", "Compliance")
POLICY_STATUSES = ("Active", "Under Review")

FILENAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*\.(docx|pdf)$")
TICKET_PATTERN = re.compile(r"^CAS-\d{6}$")
UTC_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?(?:Z|[+-]\d{2}:\d{2})$"
)


class BuildError(ValueError):
    """Raised when the authored source or generated data is invalid."""


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
        separators=(",", ": "),
    ) + "\n"


def parse_utc(value: str) -> datetime:
    if not isinstance(value, str) or not UTC_PATTERN.fullmatch(value):
        raise BuildError(f"datetime must include an explicit UTC offset: {value!r}")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise BuildError(f"datetime is not a real calendar value: {value!r}") from error
    return parsed.astimezone(timezone.utc)


def iso_millis(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )


def iso_seconds(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def record_guid(namespace: uuid.UUID, list_key: str, index: int | str) -> str:
    return str(uuid.uuid5(namespace, f"{REPO_SLUG}/{list_key}/{index}"))


def require_string(value: Any, path: str, *, maximum: int = 200) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise BuildError(f"{path} must be a non-empty trimmed string")
    if len(value) > maximum:
        raise BuildError(f"{path} is longer than {maximum} characters")
    return value


def require_int(value: Any, path: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise BuildError(f"{path} must be an integer from {minimum} through {maximum}")
    return value


def require_row(value: Any, path: str, length: int) -> list[Any]:
    if not isinstance(value, list) or len(value) != length:
        raise BuildError(f"{path} must be a list of exactly {length} fields")
    return value


def validate_source(source: dict[str, Any]) -> None:
    if not isinstance(source, dict) or set(source) != {
        "epoch",
        "namespace",
        "tenant",
        "identities",
        "accounts",
        "contracts",
        "policies",
        "meetingnotes",
    }:
        raise BuildError("source fields do not match the source contract")
    epoch_text = require_string(source["epoch"], "source.epoch", maximum=40)
    if iso_millis(parse_utc(epoch_text)) != epoch_text:
        raise BuildError("epoch must be canonical UTC with millisecond precision")
    namespace = require_string(source["namespace"], "source.namespace", maximum=36)
    try:
        parsed_namespace = uuid.UUID(namespace)
    except (ValueError, AttributeError) as error:
        raise BuildError("namespace must be a UUID") from error
    if str(parsed_namespace) != namespace:
        raise BuildError("namespace must be a canonical lowercase UUID")
    tenant = source["tenant"]
    if not isinstance(tenant, dict) or set(tenant) != {"name", "siteUrl"}:
        raise BuildError("source.tenant fields do not match the source contract")
    if tenant["name"] != "Aster Lane Office Systems":
        raise BuildError("tenant name does not match the public fixture contract")
    if tenant["siteUrl"] != "https://intranet.asterlane.example/sites/documents":
        raise BuildError("tenant siteUrl does not match the public fixture contract")

    identities = source["identities"]
    if not isinstance(identities, list) or not identities:
        raise BuildError("source.identities must be a non-empty list")
    identity_names: set[str] = set()
    for index, item in enumerate(identities):
        if not isinstance(item, dict) or set(item) != {"name", "role"}:
            raise BuildError(f"source.identities[{index}] fields are invalid")
        name = require_string(item["name"], f"source.identities[{index}].name")
        if not re.fullmatch(r"[^\s]+ [^\s]+", name):
            raise BuildError(
                f"source.identities[{index}].name must contain exactly two tokens"
            )
        require_string(item["role"], f"source.identities[{index}].role")
        if name in identity_names:
            raise BuildError(f"duplicate identity name: {name}")
        identity_names.add(name)

    accounts = source["accounts"]
    if not isinstance(accounts, list) or not accounts:
        raise BuildError("source.accounts must be a non-empty list")
    account_names: set[str] = set()
    for index, name in enumerate(accounts):
        require_string(name, f"source.accounts[{index}]")
        if name in account_names:
            raise BuildError(f"duplicate account name: {name}")
        account_names.add(name)

    def check_ticket(value: Any, path: str) -> None:
        if value is None:
            return
        ticket = require_string(value, path, maximum=10)
        if not TICKET_PATTERN.fullmatch(ticket):
            raise BuildError(f"{path} must match CAS-xxxxxx")

    def check_filename(value: Any, path: str, seen: set[str]) -> None:
        filename = require_string(value, path, maximum=120)
        if not FILENAME_PATTERN.fullmatch(filename):
            raise BuildError(f"{path} must be a lowercase docx or pdf filename")
        if filename in seen:
            raise BuildError(f"duplicate filename: {filename}")
        seen.add(filename)

    filenames: set[str] = set()
    contracts = source["contracts"]
    if not isinstance(contracts, list) or not contracts:
        raise BuildError("source.contracts must be a non-empty list")
    for index, value in enumerate(contracts):
        row = require_row(value, f"source.contracts[{index}]", 10)
        title, filename, account, kind, amount, status, expiry, author, ticket, preview = row
        require_string(title, f"source.contracts[{index}][0]")
        check_filename(filename, f"source.contracts[{index}][1]", filenames)
        if account not in account_names:
            raise BuildError(f"source.contracts[{index}] references unknown account {account!r}")
        if kind not in CONTRACT_TYPES:
            raise BuildError(f"source.contracts[{index}] contract type must be one of {CONTRACT_TYPES}")
        require_int(amount, f"source.contracts[{index}][4]", 1000, 10_000_000)
        if status not in CONTRACT_STATUSES:
            raise BuildError(f"source.contracts[{index}] status must be one of {CONTRACT_STATUSES}")
        require_int(expiry, f"source.contracts[{index}][6]", -400, 2000)
        require_int(author, f"source.contracts[{index}][7]", 0, len(identities) - 1)
        check_ticket(ticket, f"source.contracts[{index}][8]")
        require_string(preview, f"source.contracts[{index}][9]", maximum=700)

    policies = source["policies"]
    if not isinstance(policies, list) or not policies:
        raise BuildError("source.policies must be a non-empty list")
    for index, value in enumerate(policies):
        row = require_row(value, f"source.policies[{index}]", 7)
        title, filename, category, status, effective, author, preview = row
        require_string(title, f"source.policies[{index}][0]")
        check_filename(filename, f"source.policies[{index}][1]", filenames)
        if category not in POLICY_CATEGORIES:
            raise BuildError(f"source.policies[{index}] category must be one of {POLICY_CATEGORIES}")
        if status not in POLICY_STATUSES:
            raise BuildError(f"source.policies[{index}] status must be one of {POLICY_STATUSES}")
        require_int(effective, f"source.policies[{index}][4]", -2000, 0)
        require_int(author, f"source.policies[{index}][5]", 0, len(identities) - 1)
        require_string(preview, f"source.policies[{index}][6]", maximum=700)

    meetingnotes = source["meetingnotes"]
    if not isinstance(meetingnotes, list) or not meetingnotes:
        raise BuildError("source.meetingnotes must be a non-empty list")
    for index, value in enumerate(meetingnotes):
        row = require_row(value, f"source.meetingnotes[{index}]", 6)
        title, filename, account, ticket, author, preview = row
        require_string(title, f"source.meetingnotes[{index}][0]")
        check_filename(filename, f"source.meetingnotes[{index}][1]", filenames)
        if account is not None and account not in account_names:
            raise BuildError(
                f"source.meetingnotes[{index}] references unknown account {account!r}"
            )
        check_ticket(ticket, f"source.meetingnotes[{index}][3]")
        require_int(author, f"source.meetingnotes[{index}][4]", 0, len(identities) - 1)
        require_string(preview, f"source.meetingnotes[{index}][5]", maximum=700)


def item_base(
    source: dict[str, Any],
    list_key: str,
    index: int,
    *,
    title: str,
    filename: str,
    author_index: int,
    created: datetime,
    modified: datetime,
    preview: str,
) -> dict[str, Any]:
    namespace = uuid.UUID(source["namespace"])
    spec = LISTS[list_key]
    site_url = source["tenant"]["siteUrl"]
    site_path = site_url.split(".example", 1)[1]
    list_guid = record_guid(namespace, "lists", spec["path"])
    identity = source["identities"][author_index]
    item_id = index + 1
    return {
        "__metadata": {
            "id": f"Web/Lists(guid'{list_guid}')/Items({item_id})",
            "uri": f"{site_url}/_api/Web/Lists(guid'{list_guid}')/Items({item_id})",
            "etag": f'"{1 + index % 4}"',
            "type": spec["entity_type"],
        },
        "Id": item_id,
        "ID": item_id,
        "GUID": record_guid(namespace, list_key, index),
        "Title": title,
        "FileLeafRef": filename,
        "ServerRelativeUrl": f"{site_path}/Shared Documents/{spec['path']}/{filename}",
        "Author": identity["name"],
        "AuthorId": author_index + 1,
        "AuthorTitle": identity["role"],
        "Created": iso_seconds(created),
        "Modified": iso_seconds(modified),
        "Preview": preview,
    }


def build_items(source: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    epoch = parse_utc(source["epoch"])
    items: dict[str, list[dict[str, Any]]] = {key: [] for key in LISTS}

    for index, row in enumerate(source["contracts"]):
        title, filename, account, kind, amount, status, expiry, author, ticket, preview = row
        created = epoch - timedelta(days=420 - index * 23, hours=index % 7)
        modified = created + timedelta(days=15 + (index * 7) % 60, hours=index % 5)
        record = item_base(
            source,
            "contracts",
            index,
            title=title,
            filename=filename,
            author_index=author,
            created=created,
            modified=modified,
            preview=preview,
        )
        record.update(
            ContractType=kind,
            ContractValue=amount,
            Status=status,
            ExpiryDate=iso_seconds(epoch + timedelta(days=expiry)),
            RelatedAccount=account,
            RelatedTicket=ticket,
        )
        items["contracts"].append(record)

    for index, row in enumerate(source["policies"]):
        title, filename, category, status, effective, author, preview = row
        created = epoch - timedelta(days=620 - index * 40, hours=index % 6)
        modified = created + timedelta(days=45 + index * 9, hours=index % 3)
        record = item_base(
            source,
            "policies",
            index,
            title=title,
            filename=filename,
            author_index=author,
            created=created,
            modified=modified,
            preview=preview,
        )
        record.update(
            Category=category,
            Status=status,
            EffectiveDate=iso_seconds(epoch + timedelta(days=effective)),
        )
        items["policies"].append(record)

    for index, row in enumerate(source["meetingnotes"]):
        title, filename, account, ticket, author, preview = row
        created = epoch - timedelta(days=60 - index * 5, hours=index % 9)
        modified = created + timedelta(hours=2 + index)
        record = item_base(
            source,
            "meetingnotes",
            index,
            title=title,
            filename=filename,
            author_index=author,
            created=created,
            modified=modified,
            preview=preview,
        )
        record.update(
            MeetingDate=iso_seconds(created),
            RelatedAccount=account,
            RelatedTicket=ticket,
        )
        items["meetingnotes"].append(record)

    return items


def build_lists_index(
    source: dict[str, Any], items: dict[str, list[dict[str, Any]]]
) -> dict[str, Any]:
    namespace = uuid.UUID(source["namespace"])
    epoch = parse_utc(source["epoch"])
    site_url = source["tenant"]["siteUrl"]
    results = []
    for list_key, spec in LISTS.items():
        list_guid = record_guid(namespace, "lists", spec["path"])
        records = items[list_key]
        last_modified = max(record["Modified"] for record in records)
        results.append(
            {
                "__metadata": {
                    "id": f"Web/Lists(guid'{list_guid}')",
                    "uri": f"{site_url}/_api/Web/Lists(guid'{list_guid}')",
                    "type": "SP.List",
                },
                "Id": list_guid,
                "Title": spec["title"],
                "Description": spec["description"],
                "EntityTypeName": spec["list_entity"],
                "BaseTemplate": 101,
                "ItemCount": len(records),
                "Created": iso_seconds(epoch - timedelta(days=730)),
                "LastItemModifiedDate": last_modified,
                "ItemsUrl": f"_api/web/lists/{spec['path']}/items.json",
            }
        )
    return {"d": {"results": results}}


def build_index_html(items: dict[str, list[dict[str, Any]]]) -> str:
    rows = "\n".join(
        (
            '        <tr><td><a href="_api/web/lists/{path}/items.json">{title}</a></td>'
            "<td>{count}</td><td>{description}</td></tr>"
        ).format(
            path=spec["path"],
            title=spec["title"],
            count=len(items[key]),
            description=spec["description"],
        )
        for key, spec in LISTS.items()
    )
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Static SharePoint — Aster Lane Office Systems</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body { margin: 0; background: #0f1216; color: #d6dce3; font: 16px/1.6 -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
  main { max-width: 860px; margin: 0 auto; padding: 48px 24px 96px; }
  h1 { font-size: 28px; margin: 0 0 4px; color: #f2f5f8; display: flex; align-items: center; gap: 12px; }
  h1 svg { flex: none; }
  h2 { font-size: 19px; margin: 40px 0 12px; color: #eef1f5; }
  .sub { color: #8b96a3; margin: 0 0 28px; }
  .notice { background: #171c23; border: 1px solid #2a323d; border-radius: 8px; padding: 14px 18px; font-size: 14px; color: #a7b1bd; }
  table { width: 100%; border-collapse: collapse; margin: 8px 0 0; font-size: 15px; }
  th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid #232a33; }
  th { color: #8b96a3; font-weight: 600; font-size: 13px; text-transform: uppercase; letter-spacing: 0.05em; }
  a { color: #6cb2ff; text-decoration: none; }
  a:hover { text-decoration: underline; }
  pre { background: #171c23; border: 1px solid #2a323d; border-radius: 8px; padding: 16px; overflow-x: auto; font-size: 13.5px; color: #c9d3dd; }
  code { font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; }
  footer { margin-top: 48px; font-size: 14px; color: #8b96a3; }
</style>
</head>
<body>
<main>
  <h1>
    <svg width="30" height="30" viewBox="0 0 30 30" aria-hidden="true"><rect x="2" y="4" width="26" height="22" rx="3" fill="none" stroke="#6cb2ff" stroke-width="2"/><line x1="7" y1="11" x2="23" y2="11" stroke="#6cb2ff" stroke-width="2"/><line x1="7" y1="16" x2="23" y2="16" stroke="#3d6fa8" stroke-width="2"/><line x1="7" y1="21" x2="17" y2="21" stroke="#3d6fa8" stroke-width="2"/></svg>
    Static SharePoint
  </h1>
  <p class="sub">Deterministic document-collaboration fixtures for the fictional tenant
  <strong>Aster Lane Office Systems</strong>, served as classic SharePoint-style REST shapes
  (<code>{{"d": {{"results": [...]}}}}</code>) from plain static JSON.</p>

  <p class="notice">Independently authored simulator serving SharePoint-style REST shapes.
  Not affiliated with, endorsed by, or claiming parity with Microsoft. All content is
  synthetic: customer domains use <code>.example</code> and no real organizations, people,
  or documents are represented. Document binaries deliberately do not exist — each item
  carries a one-paragraph <code>Preview</code> instead (an enrichment seam).</p>

  <h2>Lists</h2>
  <table>
    <thead><tr><th>List</th><th>Items</th><th>Description</th></tr></thead>
    <tbody>
{rows}
    </tbody>
  </table>
  <p><a href="_api/web/lists.json">_api/web/lists.json</a> — index of all lists with item counts.</p>

  <h2>Read example</h2>
  <pre><code>const response = await fetch("./_api/web/lists/Contracts/items.json");
const contracts = await response.json();
console.log(contracts.d.results.length, contracts.d.results[0].Title);</code></pre>

  <h2>Cross-system joins</h2>
  <p>Contracts and meeting notes reference CRM case ticket numbers
  (<code>RelatedTicket</code>, e.g. <code>CAS-260134</code>) and shared customer accounts
  (<code>RelatedAccount</code>) from the companion
  <a href="https://kody-w.github.io/static-dynamics-365/">Static Dynamics 365</a> tenant,
  so an agent can join documents to live-shaped CRM records.</p>

  <h2>Write API</h2>
  <p>Open a GitHub Issue titled <code>[SP] ...</code> carrying a fenced
  <code>sharepoint-write/1.0</code> JSON command to create Contracts or Meeting Notes
  items, or update a contract Status by Id. See
  <a href="https://github.com/kody-w/static-sharepoint">the repository</a> for the command
  shapes.</p>

  <footer>
    <a href="https://github.com/kody-w/static-sharepoint">GitHub repository</a> ·
    <a href="https://kody-w.github.io/RAR/">RAR agent store</a> ·
    <a href="https://kody-w.github.io/static-dynamics-365/">Static Dynamics 365</a>
  </footer>
</main>
</body>
</html>
""".replace("{rows}", rows).replace('{{"d": {{"results": [...]}}}}', '{"d": {"results": [...]}}')


def build_outputs(source: dict[str, Any]) -> dict[Path, bytes]:
    validate_source(source)
    items = build_items(source)
    outputs: dict[Path, bytes] = {}
    for list_key, spec in LISTS.items():
        envelope = {"d": {"results": items[list_key]}}
        outputs[API_ROOT / "lists" / spec["path"] / "items.json"] = canonical_json(
            envelope
        ).encode("utf-8")
    outputs[API_ROOT / "lists.json"] = canonical_json(
        build_lists_index(source, items)
    ).encode("utf-8")
    outputs[SITE_ROOT / "index.html"] = build_index_html(items).encode("utf-8")
    return outputs


def load_source() -> dict[str, Any]:
    try:
        with SOURCE_PATH.open("r", encoding="utf-8") as handle:
            source = json.load(
                handle,
                parse_constant=lambda value: (_ for _ in ()).throw(
                    BuildError(f"source contains non-finite JSON number {value}")
                ),
            )
    except BuildError:
        raise
    except (OSError, json.JSONDecodeError) as error:
        raise BuildError(f"cannot load {SOURCE_PATH.name}: {error}") from error
    if not isinstance(source, dict):
        raise BuildError("source root must be an object")
    return source


def check_outputs(outputs: dict[Path, bytes]) -> list[str]:
    drift: list[str] = []
    for path, expected in sorted(outputs.items(), key=lambda item: item[0].as_posix()):
        try:
            actual = path.read_bytes()
        except FileNotFoundError:
            drift.append(f"missing: {path.relative_to(ROOT)}")
            continue
        if actual != expected:
            drift.append(f"drift: {path.relative_to(ROOT)}")
    expected_items = {
        path.resolve() for path in outputs if path.name == "items.json"
    }
    for path in sorted((API_ROOT / "lists").glob("*/items.json")):
        if path.resolve() not in expected_items:
            drift.append(f"stale: {path.relative_to(ROOT)}")
    return drift


def write_outputs(outputs: dict[Path, bytes]) -> None:
    for path, payload in sorted(outputs.items(), key=lambda item: item[0].as_posix()):
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_bytes(payload)
        os.replace(temporary, path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare generated bytes with committed outputs without writing",
    )
    args = parser.parse_args(argv)
    try:
        outputs = build_outputs(load_source())
    except BuildError as error:
        print(f"build error: {error}", file=sys.stderr)
        return 2
    if args.check:
        drift = check_outputs(outputs)
        if drift:
            print("\n".join(drift), file=sys.stderr)
            return 1
        print(f"verified {len(outputs)} deterministic generated files")
        return 0
    write_outputs(outputs)
    print(f"wrote {len(outputs)} deterministic generated files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
