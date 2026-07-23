# rapp-dataverse/1.0

**A spec for running RAPP entirely on out-of-the-box Dataverse — no custom tables, no custom
fields, no solution import — with a public static "vTwin" so nobody is ever blocked by lacking an
environment, and a CLI that hatches the brainstem into a real instance by twin sync.**

RAPP (the Rapid Agent Prototype Pattern) normally runs as a Python server (`brainstem.py`) or an
Azure Function (`function_app.py`). This spec defines how the **same** behaviour — a soul, agents,
memory, and a tool-calling loop — runs natively in Microsoft Power Platform on stock Dataverse.

---

## 1. Principles

- **OOTB only.** RAPP uses tables present in *every* Dataverse environment: `account`, `contact`,
  `annotation`. A conformant deployment requires **zero customization** and **zero solution import**.
- **The data houses the behaviour.** Agents (including their `agent.py`), memory, conversations,
  and config are rows, not files. The brainstem is grounded by reading those rows.
- **Never blocked.** A public, server-less **vTwin** of the brainstem is always available, so the
  pattern can be explored, tested, and compared with no real Dataverse.
- **One identity across twins.** Deterministic primary-key GUIDs are shared between the vTwin and
  any real instance, so they sync 1:1 by upsert-by-id.

---

## 2. The OOTB encoding (required)

| RAPP concept | OOTB table | Encoding |
|--------------|-----------|----------|
| Anchor + soul | `account` "RAPP System" | `description` = system prompt |
| Users | `contact` | person rows |
| Config | `annotation` | `subject = rapp.config`; `notetext` = JSON |
| Agent | `annotation` | `subject = rapp.agent`; `notetext` = `{name, description, manifest, parameters, sourcecode, kind, enabled}` |
| Shared memory | `annotation` regarding the account | `subject = rapp.memory` |
| User memory | `annotation` regarding the user's contact | `subject = rapp.memory` |
| Conversation | `annotation` | `subject = rapp.conversation` |
| Message (history + audit) | `annotation` | `subject = rapp.message`; `notetext` = `{session_id, sequence, role, content, agent_name}` |

Rules:

- The discriminator is the `annotation.subject`, namespaced `rapp.*`. The payload is JSON in
  `annotation.notetext`. Both are OOTB string columns.
- **Memory scope is the note's regarding object** (`objectid`): account = shared, contact = user.
- **The full `agent.py` is stored in `notetext.sourcecode`.** The single-file agent is the unit;
  Dataverse is its registry of record. `kind` ∈ `{python, prompt, dataverse, flow}` says how it
  executes in the current tier; the source is stored in all cases.
- A deployment MUST NOT require any column or table outside the three OOTB tables above.

See [`brainstem/OOTB_MAPPING.md`](brainstem/OOTB_MAPPING.md) for the grounding queries and write bindings.

---

## 3. The brainstem loop

Inference is an **AI Builder prompt** ([`brainstem/router_prompt.md`](brainstem/router_prompt.md))
grounded by the OOTB rows; orchestration is a **Power Automate** Do-Until loop
([`brainstem/orchestrator_flow.md`](brainstem/orchestrator_flow.md)) bounded by
`rapp.config.maxrounds`; the chat surface is **Copilot Studio**. The loop mirrors the Python RAPP:
load soul+memory+agents → call the router → dispatch an agent → append the observation → repeat →
respond. Every agent call is logged as a `rapp.message` annotation (Accountability).

---

## 4. The vTwin (digital twin)

A conformant pattern ships a **vTwin**: a read-only, server-less Dataverse Web API served from
static Git-host files, built on [`rapp-static-api/1.0`](https://github.com/kody-w/rapp-static-apis).

- Collections under `api/data/v9.2/{accounts,contacts,annotations}.json` are byte-shaped like a real
  `GET` (`@odata.context`, `value[]`, `@odata.etag`, `_objectid_value` + `lookuplogicalname` +
  `FormattedValue`, `versionnumber`, `statecode`…). A client can't tell the file from the live API.
- **Identity:** every primary-key GUID is deterministic, so it is the shared id across the vTwin and
  any real instance.
- **Sync:** bidirectional by upsert-by-id; deltas via `modifiedon`/`versionnumber`; scope limited to
  `rapp.*` notes + the RAPP anchor. See [`twin/SYNC.md`](twin/SYNC.md).
- One idempotent, stable-write build step regenerates the twin from hand-authored seeds.

Reference vTwin: [`twin/`](twin/). Live: `https://kody-w.github.io/rapp-dataverse/twin/`.

---

## 5. The hatcher (CLI)

A conformant pattern ships a **hatcher**: a CLI that authenticates as a Dataverse **application
user** (S2S client credentials) and replicates the global vTwin brainstem into a real instance by
upsert-by-id, so the instance becomes identical to the global brainstem.

- With no credentials configured, the CLI serves reads from the **global vTwin** — never blocked.
- `hatch` twin-syncs the full brainstem; `compare` diffs an instance against the vTwin
  (in-sync / drift / missing); `selftest` verifies the 1:1 identity scheme offline.

Reference hatcher: [`cli/rapp_dv.py`](cli/rapp_dv.py).

---

## 6. Conformance

An implementation is **rapp-dataverse/1.0 conformant** if:

- [ ] It uses only the OOTB `account`, `contact`, and `annotation` tables — no custom tables/fields,
      no solution import.
- [ ] RAPP entities are encoded as `rapp.*`-subject annotations with JSON `notetext`; memory scope
      is the regarding object; the agent.py is stored in `notetext.sourcecode`.
- [ ] The brainstem loop is an AI Builder router prompt + a bounded Power Automate loop.
- [ ] It ships a vTwin: a static, OData-shaped, deterministically-keyed digital twin that syncs 1:1
      with a real instance by upsert-by-id.
- [ ] It ships a hatcher that defaults to the vTwin when unconnected and replicates the brainstem
      into a real instance via an application user.

---

MIT © Kody Wildfeuer. Part of the RAPP ecosystem.
