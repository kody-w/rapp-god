# Static SharePoint

**Deterministic, zero-dependency, standalone document-collaboration tenant served as classic SharePoint-style REST shapes.**

Static SharePoint is an independently authored, static-JSON environment for demos, tests,
training, and integration prototyping. It serves the document libraries of the fictional
operator tenant **Aster Lane Office Systems** — Contracts, Policies, and Meeting Notes —
in classic SharePoint REST list shapes (`{"d": {"results": [...]}}`) from plain files on
GitHub Pages. It shares a fictional world with
[Static Dynamics 365](https://kody-w.github.io/static-dynamics-365/): the same customer
accounts, the same staff identities, and cross-references to the same CRM case ticket
numbers, so an agent can join documents to CRM records across both APIs.

> **Disclaimer.** This is an independently authored simulator serving SharePoint-style
> REST shapes. All records are synthetic; customer domains use `.example` and phone data
> uses reserved 555 numbers. It is not affiliated with, endorsed by, or claiming parity
> with Microsoft or any vendor.

**Live API:** https://kody-w.github.io/static-sharepoint/

## The enrichment seam: no binaries, by design

Every list item names a document (`FileLeafRef`, `ServerRelativeUrl`) — but the full
`.docx`/`.pdf` binaries **deliberately do not exist**. Each item instead carries a
one-paragraph synthetic summary in its `Preview` field. That gap is an intentional
enrichment seam: an agent that needs a full document can generate one from the Preview,
the per-list columns, and the joined CRM context, without this repo ever shipping fake
binary files.

## Quickstart

Requirements: Python 3.11+. There is nothing to install.

```sh
python3 build.py --check
python3 -m http.server --directory site 8000
```

Open <http://localhost:8000/>. To regenerate committed fixtures after editing
`data/source.json` (the compact authored truth):

```sh
python3 build.py
python3 -m unittest discover -s tests -p 'test_*.py'
```

The build uses only Python's standard library, a fixed UTC epoch, UUIDv5 identifiers,
canonical sorted JSON, and no wall clock or randomness — two builds are byte-identical,
and `python3 build.py --check` fails on any drift.

## Fixture example

```sh
curl 'https://kody-w.github.io/static-sharepoint/_api/web/lists/Contracts/items.json'
```

```js
const response = await fetch("./_api/web/lists/Contracts/items.json");
const contracts = await response.json();
console.log(contracts.d.results[0].Title, contracts.d.results[0].RelatedTicket);
```

Collections:

| URL | List |
|-----|------|
| `_api/web/lists.json` | Index of all lists with item counts |
| `_api/web/lists/Contracts/items.json` | Contracts (MSAs, SOWs, renewals) |
| `_api/web/lists/Policies/items.json` | Policies (HR, benefits, finance, security, compliance) |
| `_api/web/lists/MeetingNotes/items.json` | Meeting Notes (list title "Meeting Notes") |

Items carry `Id`, `Title`, `FileLeafRef`, `ServerRelativeUrl`, `Author`, `Created`,
`Modified`, `Preview`, plus per-list columns — `ContractType`, `ContractValue`,
`ExpiryDate`, `Status`, `RelatedAccount`, `RelatedTicket` on Contracts; `Category`,
`Status`, `EffectiveDate` on Policies; `MeetingDate`, `RelatedAccount`, `RelatedTicket`
on Meeting Notes. `RelatedTicket` values (e.g. `CAS-260134`, Summit Trail Software's
license renewal) resolve in the companion CRM's
[`incidents.json`](https://kody-w.github.io/static-dynamics-365/api/data/v9.2/incidents.json).

## Write API (Issues bridge)

Open a GitHub Issue titled `[SP] ...` whose body contains a fenced ```json command with
schema `sharepoint-write/1.0`. The workflow validates it, mutates `data/source.json`,
rebuilds deterministically, gates on the test suite, commits, redeploys Pages, and closes
the issue with a receipt. Supported in v1:

- `create` `Contracts` — requires `Title` and a `RelatedAccount` from the shared world
- `create` `Meeting Notes` — requires `Title`; `RelatedAccount`/`RelatedTicket` optional
- `update` `Contracts` — change `Status` by `Id`

Everything else (deletes, Policies writes, other fields) is rejected with a clear error.
See [API.md](API.md) for full command shapes.

## Architecture

| File | Role |
|------|------|
| `data/source.json` | Compact authored truth: epoch, namespace, tenant, identities, accounts, list rows |
| `build.py` | Stdlib-only deterministic expansion → `site/_api/...` + `site/index.html` |
| `tests/test_build.py` | stdlib unittest: determinism, derived counts, UUIDv5 ids, cross-references, write bridge |
| `scripts/process_write_issue.py` | Issues-as-CRUD bridge |
| `.github/workflows/ci.yml` | `build.py --check` + unittest on every push/PR |
| `.github/workflows/pages.yml` | Deploys exactly `site/` |
| `.github/workflows/write-api.yml` | Processes `[SP]` issues end to end |

Part of the [RAPP ecosystem](https://kody-w.github.io/RAR/).

## License

MIT — see [LICENSE](LICENSE).
