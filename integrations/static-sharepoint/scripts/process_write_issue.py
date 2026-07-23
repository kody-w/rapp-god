#!/usr/bin/env python3
"""Write API bridge — GitHub Issues in, deterministic SharePoint-style tenant out.

The read API is static JSON on GitHub Pages. Writes arrive as GitHub Issues
titled "[SP] ..." carrying a fenced ```json command. This processor validates
the command, mutates ``data/source.json`` (the authored truth), and the
workflow then reruns ``build.py`` (deterministic expansion), runs the test
suite, commits, and Pages redeploys — so a write becomes globally readable
in about a minute. No server.

Command shape (issue body, inside a ```json fence):

    {
      "schema": "sharepoint-write/1.0",
      "operation": "create",            // create | update
      "entity": "Contracts",            // Contracts | Meeting Notes
      "record": {
        "Title": "Maple Thread Textiles Loom Room SOW",
        "RelatedAccount": "Maple Thread Textiles",
        "ContractType": "SOW",          // MSA | SOW | Renewal | Services Agreement
        "ContractValue": 31200,
        "Status": "Draft",              // Draft | In Review | Active | Renewal Pending | Expired
        "ExpiryDays": 365,              // days after the fixed epoch
        "RelatedTicket": "CAS-260121",  // optional CAS-xxxxxx
        "Preview": "One-paragraph synthetic summary."
      }
    }

Simulator policy (v1):
  * create: Contracts, Meeting Notes
  * update: Contracts only — Status by Id
  * Policies are read-only; deletes are unsupported. Everything else is
    rejected with a clear error.

Usage:
  python3 scripts/process_write_issue.py --event-path "$GITHUB_EVENT_PATH"
  python3 scripts/process_write_issue.py --test '{"schema": ...}'
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_PATH = ROOT / "data" / "source.json"

WRITE_SCHEMA = "sharepoint-write/1.0"
TITLE_PREFIX = "[SP]"
REPO_SLUG = "static-sharepoint"

CONTRACT_TYPES = ("MSA", "SOW", "Renewal", "Services Agreement")
CONTRACT_STATUSES = ("Draft", "In Review", "Active", "Renewal Pending", "Expired")
TICKET_RE = re.compile(r"^CAS-\d{6}$")
TITLE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 .,'&()\-]{1,119}$")

ENTITY_ALIASES = {
    "contracts": "contracts",
    "meeting notes": "meetingnotes",
    "meetingnotes": "meetingnotes",
}
LIST_PATHS = {"contracts": "Contracts", "meetingnotes": "MeetingNotes"}


class WriteError(ValueError):
    pass


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def extract_command(body: str) -> dict:
    match = re.search(r"```json\s*\n(.*?)```", body or "", re.DOTALL)
    if not match:
        raise WriteError("No ```json fenced command found in the issue body")
    try:
        command = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise WriteError(f"Command is not valid JSON: {exc}") from exc
    if not isinstance(command, dict) or command.get("schema") != WRITE_SCHEMA:
        raise WriteError(f"Command schema must be '{WRITE_SCHEMA}'")
    return command


def require_title(value, label: str) -> str:
    if not isinstance(value, str) or not TITLE_RE.match(value.strip()):
        raise WriteError(
            f"{label} must be 2-120 chars of letters, digits, spaces, or . , ' & ( ) -"
        )
    return value.strip()


def require_account(source: dict, value) -> str:
    name = require_title(value, "RelatedAccount")
    for account in source["accounts"]:
        if account.casefold() == name.casefold():
            return account
    raise WriteError(
        f"Unknown account '{name}'. Use one of: "
        + ", ".join(source["accounts"][:8])
        + ", ..."
    )


def require_ticket(value) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not TICKET_RE.fullmatch(value.strip()):
        raise WriteError("RelatedTicket must match CAS-xxxxxx")
    return value.strip()


def require_preview(record: dict, title: str) -> str:
    preview = record.get("Preview")
    if preview is None:
        return (
            f"{title}. Synthetic one-paragraph summary created through the Write "
            "API; the full document body deliberately does not exist in this "
            "simulator."
        )
    if not isinstance(preview, str) or not 40 <= len(preview.strip()) <= 700:
        raise WriteError("Preview must be a 40-700 character paragraph")
    return preview.strip()


def slug_filename(source: dict, title: str, extension: str = "docx") -> str:
    stem = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60] or "document"
    taken = {
        row[1]
        for rows in (source["contracts"], source["policies"], source["meetingnotes"])
        for row in rows
    }
    filename = f"{stem}.{extension}"
    suffix = 2
    while filename in taken:
        filename = f"{stem}-{suffix}.{extension}"
        suffix += 1
    return filename


def record_guid(source: dict, list_key: str, index: int) -> str:
    namespace = uuid.UUID(source["namespace"])
    return str(uuid.uuid5(namespace, f"{REPO_SLUG}/{list_key}/{index}"))


def create_contract(source: dict, record: dict) -> dict:
    title = require_title(record.get("Title"), "Title")
    if any(row[0].casefold() == title.casefold() for row in source["contracts"]):
        raise WriteError(f"A contract titled '{title}' already exists")
    account = require_account(source, record.get("RelatedAccount"))
    kind = record.get("ContractType", "SOW")
    if kind not in CONTRACT_TYPES:
        raise WriteError(f"ContractType must be one of {list(CONTRACT_TYPES)}")
    value = record.get("ContractValue", 25000)
    if type(value) is not int or not 1000 <= value <= 10_000_000:
        raise WriteError("ContractValue must be an integer from 1000 through 10000000")
    status = record.get("Status", "Draft")
    if status not in CONTRACT_STATUSES:
        raise WriteError(f"Status must be one of {list(CONTRACT_STATUSES)}")
    expiry = record.get("ExpiryDays", 365)
    if type(expiry) is not int or not -400 <= expiry <= 2000:
        raise WriteError("ExpiryDays must be an integer from -400 through 2000")
    ticket = require_ticket(record.get("RelatedTicket"))
    preview = require_preview(record, title)
    index = len(source["contracts"])
    author = index % len(source["identities"])
    source["contracts"].append(
        [
            title,
            slug_filename(source, title),
            account,
            kind,
            value,
            status,
            expiry,
            author,
            ticket,
            preview,
        ]
    )
    return {
        "entity": "Contracts",
        "operation": "create",
        "Id": index + 1,
        "GUID": record_guid(source, "contracts", index),
        "Title": title,
        "RelatedAccount": account,
        "Status": status,
    }


def create_meetingnote(source: dict, record: dict) -> dict:
    title = require_title(record.get("Title"), "Title")
    if any(row[0].casefold() == title.casefold() for row in source["meetingnotes"]):
        raise WriteError(f"A meeting note titled '{title}' already exists")
    account = (
        require_account(source, record.get("RelatedAccount"))
        if record.get("RelatedAccount") is not None
        else None
    )
    ticket = require_ticket(record.get("RelatedTicket"))
    preview = require_preview(record, title)
    index = len(source["meetingnotes"])
    author = index % len(source["identities"])
    source["meetingnotes"].append(
        [title, slug_filename(source, title), account, ticket, author, preview]
    )
    return {
        "entity": "Meeting Notes",
        "operation": "create",
        "Id": index + 1,
        "GUID": record_guid(source, "meetingnotes", index),
        "Title": title,
        "RelatedAccount": account,
        "RelatedTicket": ticket,
    }


def update_contract(source: dict, record: dict) -> dict:
    item_id = record.get("Id")
    if type(item_id) is not int or not 1 <= item_id <= len(source["contracts"]):
        raise WriteError(
            f"Id must be an integer from 1 through {len(source['contracts'])}"
        )
    status = record.get("Status")
    if status not in CONTRACT_STATUSES:
        raise WriteError(
            f"update Contracts changes Status only; Status must be one of "
            f"{list(CONTRACT_STATUSES)}"
        )
    row = source["contracts"][item_id - 1]
    previous = row[5]
    if previous == status:
        raise WriteError(f"Contract {item_id} Status is already '{status}'")
    row[5] = status
    return {
        "entity": "Contracts",
        "operation": "update",
        "Id": item_id,
        "Title": row[0],
        "changed": ["Status"],
        "previous_status": previous,
        "Status": status,
    }


HANDLERS = {
    ("create", "contracts"): create_contract,
    ("create", "meetingnotes"): create_meetingnote,
    ("update", "contracts"): update_contract,
}


def process(command: dict) -> dict:
    operation = command.get("operation")
    entity_raw = command.get("entity")
    entity = ENTITY_ALIASES.get(str(entity_raw).strip().casefold())
    record = command.get("record")
    if not isinstance(record, dict):
        raise WriteError("'record' must be an object")
    handler = HANDLERS.get((operation, entity))
    if handler is None:
        raise WriteError(
            f"Unsupported operation '{operation} {entity_raw}'. Supported: "
            "create Contracts, create Meeting Notes, update Contracts "
            "(Status by Id). Policies are read-only; deletes are unsupported."
        )
    source = load_json(SOURCE_PATH)
    receipt = handler(source, record)
    save_json(SOURCE_PATH, source)
    path = LIST_PATHS["contracts" if receipt["entity"] == "Contracts" else "meetingnotes"]
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    if "/" in repository:
        owner, name = repository.split("/", 1)
        receipt["read_url"] = (
            f"https://{owner}.github.io/{name}/_api/web/lists/{path}/items.json"
        )
    else:
        receipt["read_url"] = f"_api/web/lists/{path}/items.json"
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--event-path")
    parser.add_argument("--test")
    args = parser.parse_args()

    try:
        if args.test:
            command = json.loads(args.test)
        else:
            event = load_json(Path(args.event_path or os.environ["GITHUB_EVENT_PATH"]))
            issue = event.get("issue", {})
            title = issue.get("title", "")
            if not title.startswith(TITLE_PREFIX):
                print(json.dumps({"skipped": f"title lacks {TITLE_PREFIX} prefix"}))
                return 0
            command = extract_command(issue.get("body", ""))
        receipt = process(command)
    except (WriteError, KeyError, json.JSONDecodeError) as exc:
        error = {"ok": False, "error": str(exc)}
        print(json.dumps(error, indent=2))
        output = os.environ.get("GITHUB_OUTPUT")
        if output:
            with open(output, "a", encoding="utf-8") as fh:
                fh.write("ok=false\n")
                fh.write(f"receipt={json.dumps(error)}\n")
        return 1

    receipt["ok"] = True
    print(json.dumps(receipt, indent=2))
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as fh:
            fh.write("ok=true\n")
            fh.write(f"receipt={json.dumps(receipt)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
