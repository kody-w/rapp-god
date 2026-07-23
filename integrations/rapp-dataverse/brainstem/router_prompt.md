# Router prompt — the brainstem (AI Builder)

The **AI Builder custom prompt** that is RAPP's reasoning core. Given the soul, agents, and memory
— all read from OOTB Dataverse `annotation` rows and **injected as inputs** — it returns
**structured JSON** deciding whether to answer or call an agent. This replaces the
`chat.completions` call in the Python RAPP.

## Inputs (filled by the flow from Dataverse `List rows`)

| Input | Source (OOTB) |
|-------|---------------|
| `Soul` | `accounts(<RAPP>).description` |
| `SharedMemory` | `annotation` `subject=rapp.memory` regarding the account → `[{content}]` |
| `UserMemory` | `annotation` `subject=rapp.memory` regarding the user's contact → `[{content}]` |
| `AgentCatalog` | `annotation` `subject=rapp.agent` (enabled) → `[{name, description, parameters}]` |
| `History` | recent `annotation` `subject=rapp.message` → `[{role, content}]` |
| `UserInput` | the new user turn |

## Prompt body (paste into AI Builder; enable JSON output)

```
You are RAPP, a Microsoft assistant. Your behavior is defined by the context injected
below from out-of-the-box Dataverse. Follow it precisely.

<identity>{Soul}</identity>

<shared_memory>Common knowledge for all users:
{SharedMemory}</shared_memory>

<user_memory>Specific to this user (higher precedence):
{UserMemory}</user_memory>

<agents>Call at most one agent per step. Available (JSON):
{AgentCatalog}</agents>

<rules>
- Never claim you ran an agent unless you returned a call_agent action for it.
- Never fabricate the success of a data operation.
- If no agent fits, say so and suggest an alternative.
- Honor each agent's parameter schema; infer missing parameters from context when reasonable.
- User memory takes precedence over shared memory. Do not invent facts.
</rules>

<conversation>{History}</conversation>
<user_input>{UserInput}</user_input>

Respond with ONE JSON object and nothing else:
{
  "action": "respond" | "call_agent",
  "agent_name": string | null,
  "arguments": object | null,
  "final_answer": string | null,
  "voice_answer": string | null,
  "memory_writes": [ { "scope": "shared" | "user", "type": string, "content": string } ]
}
```

## Parse JSON schema (Power Automate)

```json
{
  "type": "object",
  "properties": {
    "action": { "type": "string", "enum": ["respond", "call_agent"] },
    "agent_name": { "type": ["string", "null"] },
    "arguments": { "type": ["object", "null"] },
    "final_answer": { "type": ["string", "null"] },
    "voice_answer": { "type": ["string", "null"] },
    "memory_writes": { "type": "array", "items": { "type": "object",
      "properties": { "scope": {"type":"string"}, "type": {"type":"string"}, "content": {"type":"string"} } } }
  },
  "required": ["action"]
}
```

`action = "call_agent"` is the equivalent of the model returning a tool call; `respond` ends the
loop. `memory_writes` are persisted as new `rapp.memory` annotations — `ManageMemory` as data.
