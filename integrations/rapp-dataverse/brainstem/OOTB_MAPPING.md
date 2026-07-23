# OOTB mapping — RAPP on out-of-the-box Dataverse

RAPP runs on three tables that exist in **every** Dataverse environment. No custom tables, no
custom fields, no solution import.

| RAPP concept | OOTB table | Encoding |
|--------------|-----------|----------|
| Anchor + **soul** | **account** "RAPP System" | `description` = the system prompt |
| Users | **contact** | standard person rows |
| Config | **annotation** | `subject = rapp.config`, `notetext` = `{maxrounds, voice_enabled, model}` |
| **Agent** (incl. agent.py) | **annotation** | `subject = rapp.agent`, `notetext` = `{name, description, manifest, parameters, sourcecode, kind, enabled}` |
| Shared memory | **annotation** regarding the account | `subject = rapp.memory` |
| User memory | **annotation** regarding the user's contact | `subject = rapp.memory` |
| Conversation | **annotation** | `subject = rapp.conversation`, `notetext` = `{session_id, title}` |
| Message (history + audit) | **annotation** | `subject = rapp.message`, `notetext` = `{session_id, sequence, role, content, agent_name}` |

**Two load-bearing ideas:**

1. **Memory scope = the note's regarding object.** A `rapp.memory` note regarding the **account**
   is shared; regarding a **contact** it is that user's memory. This mirrors
   `set_memory_context(user_guid)` in the Python RAPP.
2. **The agent.py is stored in `notetext.sourcecode`.** The single-file agent is never lost —
   Dataverse is the agent registry of record. `kind` is `python` (run the stored agent.py in a
   code tier) / `prompt` / `dataverse` / `flow` (how it executes in pure-native mode).

## Grounding queries (what the brainstem reads each turn)

```text
agents        GET annotations?$filter=subject eq 'rapp.agent'
shared mem    GET annotations?$filter=subject eq 'rapp.memory' and _objectid_value eq <RAPP-account-id>
user mem      GET annotations?$filter=subject eq 'rapp.memory' and _objectid_value eq <contact-id>
history       GET annotations?$filter=subject eq 'rapp.message' and contains(notetext,'<session_id>')&$orderby=createdon
soul          GET accounts(<RAPP-account-id>)?$select=description
```

## Writes

```text
ManageMemory   POST annotations { subject:'rapp.memory', notetext, objectid_account@odata.bind | objectid_contact@odata.bind }
append message POST annotations { subject:'rapp.message', notetext, objectid_contact@odata.bind }
```

Every write uses only OOTB fields, so a real `POST` accepts the exact same body the
[vTwin](../twin/) emits. See [`../twin/SYNC.md`](../twin/SYNC.md) for the 1:1 sync contract.
