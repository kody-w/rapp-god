# Static SharePoint — API Reference

Base URL: `https://kody-w.github.io/static-sharepoint/`

All read endpoints are static JSON files served by GitHub Pages. Shapes follow the
classic SharePoint REST (verbose OData) convention: collections are wrapped as
`{"d": {"results": [...]}}` and every item carries a `__metadata` object.

## Read endpoints

| Endpoint | Returns |
|----------|---------|
| `_api/web/lists.json` | All lists: `Id` (UUIDv5), `Title`, `Description`, `EntityTypeName`, `BaseTemplate`, `ItemCount`, `Created`, `LastItemModifiedDate`, `ItemsUrl` |
| `_api/web/lists/Contracts/items.json` | Contract documents |
| `_api/web/lists/Policies/items.json` | Policy documents |
| `_api/web/lists/MeetingNotes/items.json` | Meeting note documents (list title "Meeting Notes") |

## Item shape

Common fields on every item:

| Field | Type | Notes |
|-------|------|-------|
| `__metadata` | object | `id`, `uri`, `etag`, `type` (e.g. `SP.Data.ContractsListItem`, `SP.Data.Meeting_x0020_NotesListItem`) |
| `Id` / `ID` | int | Positional, 1-based |
| `GUID` | string | `uuid5(namespace, "static-sharepoint/<list>/<index>")` |
| `Title` | string | Document title |
| `FileLeafRef` | string | `.docx` / `.pdf` filename |
| `ServerRelativeUrl` | string | `/sites/documents/Shared Documents/<List>/<file>` — the binary deliberately does not exist (enrichment seam) |
| `Author`, `AuthorId`, `AuthorTitle` | string, int, string | Tenant staff identity |
| `Created`, `Modified` | string | Fixed-epoch-derived UTC (`...Z`), no wall clock |
| `Preview` | string | One-paragraph synthetic summary of the document body |

Per-list columns:

| List | Columns |
|------|---------|
| Contracts | `ContractType` (MSA, SOW, Renewal, Services Agreement), `ContractValue` (int USD), `Status` (Draft, In Review, Active, Renewal Pending, Expired), `ExpiryDate`, `RelatedAccount`, `RelatedTicket` |
| Policies | `Category` (HR, Benefits, Finance, Security, Compliance), `Status` (Active, Under Review), `EffectiveDate` |
| Meeting Notes | `MeetingDate`, `RelatedAccount`, `RelatedTicket` |

`RelatedAccount` values are customer organizations shared with
[Static Dynamics 365](https://kody-w.github.io/static-dynamics-365/api/data/v9.2/accounts.json);
`RelatedTicket` values (`CAS-xxxxxx`) resolve in that tenant's
[`incidents.json`](https://kody-w.github.io/static-dynamics-365/api/data/v9.2/incidents.json).

## Write API (`sharepoint-write/1.0`)

Open a GitHub Issue titled `[SP] ...` with a fenced ```json command. The workflow
validates, rebuilds, tests, commits, redeploys, and answers with a receipt comment.

### Create a contract

```json
{
  "schema": "sharepoint-write/1.0",
  "operation": "create",
  "entity": "Contracts",
  "record": {
    "Title": "Maple Thread Textiles Loom Room SOW",
    "RelatedAccount": "Maple Thread Textiles",
    "ContractType": "SOW",
    "ContractValue": 31200,
    "Status": "Draft",
    "ExpiryDays": 365,
    "RelatedTicket": "CAS-260121",
    "Preview": "One-paragraph synthetic summary of the document body."
  }
}
```

`Title` and `RelatedAccount` are required; `RelatedAccount` must be an existing
shared-world account. Defaults: `ContractType` SOW, `ContractValue` 25000, `Status`
Draft, `ExpiryDays` 365 (days after the fixed epoch), synthesized `Preview`.

### Create a meeting note

```json
{
  "schema": "sharepoint-write/1.0",
  "operation": "create",
  "entity": "Meeting Notes",
  "record": {
    "Title": "Juniper Ridge Desk Program Kickoff",
    "RelatedAccount": "Juniper Ridge Furnishings",
    "RelatedTicket": "CAS-260113",
    "Preview": "One-paragraph synthetic summary of the discussion."
  }
}
```

Only `Title` is required.

### Update a contract's status

```json
{
  "schema": "sharepoint-write/1.0",
  "operation": "update",
  "entity": "Contracts",
  "record": {
    "Id": 1,
    "Status": "Active"
  }
}
```

### Rejected (v1 policy)

Deletes, writes to Policies, updates to any field other than contract `Status`, and
unknown accounts/tickets are rejected with an explanatory receipt comment. Filenames for
created items are slugified from the title; item `Id`s are positional and permanent.
