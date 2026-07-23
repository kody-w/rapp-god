# Orchestrator flow — the tool-calling loop (Power Automate)

The cloud flow that runs the RAPP loop on OOTB Dataverse: load the soul/agents/memory from
`annotation` rows → call the [router prompt](router_prompt.md) → dispatch an agent → append the
observation → repeat up to `rapp.config.maxrounds` → return. **No Azure Function, OOTB tables only.**

## Trigger

From a **Copilot Studio** topic ("Run a flow"), a canvas app, or a Dataverse action. Inputs:
`user_input`, `session_id`, `user_id` (a contact id; optional → shared marker).

## Steps

1. **Resolve user** — find/create the `contact` for `user_id`.
2. **Write the user turn** — add an `annotation` `subject=rapp.message`, `notetext={session_id,
   sequence, role:'user', content:user_input}` regarding the contact.
3. **Load grounding (List rows on `annotation`):**
   - `Soul` ← `accounts(<RAPP>).description`.
   - `AgentCatalog` ← `subject eq 'rapp.agent'` → Select `{name, description, parameters}` from each `notetext`.
   - `SharedMemory` ← `subject eq 'rapp.memory' and _objectid_value eq <RAPP-account-id>`.
   - `UserMemory` ← `subject eq 'rapp.memory' and _objectid_value eq <contact-id>`.
   - `History` ← `subject eq 'rapp.message' and contains(notetext,'<session_id>')`, order by `createdon`, top 20.
4. **Do Until** `done or rounds >= maxrounds`:
   1. **AI Builder → Create text with prompt** (the router), passing the inputs + `UserInput`.
   2. **Parse JSON** the output.
   3. If `action = respond` → set `final_answer`, `done = true`.
   4. If `action = call_agent`:
      - Look up the `rapp.agent` annotation by `name`; if missing or `enabled = false`, observation =
        `"Blocked by policy: agent not available"`.
      - Dispatch by `notetext.kind`: `prompt` → its AI Builder prompt; `dataverse` → a table op
        (e.g. memory write/read); `flow` → a child flow. (`python` agents run in a code tier; in
        pure-native, bind them to a `prompt`/`flow`.)
      - **Add an `annotation`** `subject=rapp.message`, `role:'tool'`, `agent_name`, `content:observation`
        — *this row is the Accountability audit record.* Append it to `History`.
   5. Increment `rounds`.
5. **Apply `memory_writes`** — add a `rapp.memory` annotation per entry (regarding the account for
   shared, the contact for user). This is `ManageMemory` as data.
6. **Write the assistant turn** — add a `rapp.message` annotation (`role:'assistant'`, `final_answer`).
7. **Respond** — return `final_answer` (+ `voice_answer`).

## Notes

- The `Do Until` cap (`maxrounds`, default 3) is the analogue of the 3-round loop in the Python RAPP.
- Disabled agents are never dispatched — the OOTB form of the agent allow/deny policy.
- Every `tool` step is an `annotation` row, so the full reasoning/audit trail is queryable in
  Dataverse and syncable back to the [vTwin](../twin/SYNC.md).
