# rapp-dv — the RAPP Dataverse CLI

Hatch the **first RAPP brainstem** into a real, **out-of-the-box** Dataverse environment using an
**application user** (server-to-server auth), then chat with it in **Copilot Studio**. No custom
tables, no custom fields, no solution import. Zero Python dependencies (standard library only).

It writes the same OOTB records as the [static digital twin](https://github.com/kody-w/rapp-dataverse/tree/main/twin)
using the **same deterministic GUIDs**, so your real instance and the vTwin stay 1:1 (verify with
`python rapp_dv.py selftest`).

## Zero setup — you are never blocked

**No real Dataverse? No problem.** With no `RAPP_DV_*` configured, the CLI automatically reads from
the **global vTwin** — a public, server-less Dataverse served from GitHub raw — so every read
command works out of the box:

```bash
python rapp_dv.py whoami         # Mode: vTwin · global static Dataverse
python rapp_dv.py agents list    # EchoAgent, CalculatorAgent … (live from the vTwin)
python rapp_dv.py memory list
python rapp_dv.py chat "what is 6 * 7?"   # grounded brainstem context (shared vs user memory)
```

Writes (`hatch`, `seed`) preview in vTwin mode and apply for real once you connect. Force a mode
with `--vtwin` (read-only) or `--online`; point at a different twin with `--static <base-url>`.

## 1. Create the application user (the "required rights")

1. **Register an app** in Entra ID (Azure portal → App registrations → New). Note the
   **Application (client) ID** and your **Directory (tenant) ID**.
2. **Add a client secret** (Certificates & secrets → New client secret). Copy the value.
3. **Add it as an Application User** in the environment
   (Power Platform admin center → your environment → Settings → Users + permissions →
   **Application users** → New app user → pick the app registration).
4. **Assign a security role** with privileges on the OOTB tables RAPP uses. Grant Create / Read /
   Write / **Append** / **AppendTo** at **Organization** level on:
   - **Account** (the RAPP anchor)
   - **Contact** (users)
   - **Note (annotation)** (the RAPP store)

   A custom role with just those is least-privilege; in a dev environment you may assign
   **System Administrator** to the app user for speed. (Append/AppendTo are required because notes
   are attached to the account/contact via the regarding lookup.)

## 2. Configure

```bash
export RAPP_DV_URL=https://yourorg.crm.dynamics.com
export RAPP_DV_TENANT=<tenant-guid>
export RAPP_DV_CLIENT_ID=<app-client-id>
export RAPP_DV_CLIENT_SECRET=<app-client-secret>
```

(Or pass `--url --tenant --client-id --client-secret` on any command.)

## 3. Hatch the brainstem (twin sync)

`hatch` is a **twin sync**: it replicates the **entire global vTwin brainstem** into your connected
instance by upsert-by-id, using the same deterministic GUIDs — so your instance becomes **identical
to the globally-available brainstem**. Then you can `compare` outputs between the two at any time.

```bash
python rapp_dv.py whoami            # verify the application-user connection
python rapp_dv.py --dry-run hatch   # preview the sync (no changes)
python rapp_dv.py hatch             # replicate the global brainstem into this instance (idempotent)
python rapp_dv.py compare           # verify this instance is IN SYNC with the global vTwin
python rapp_dv.py agents list
python rapp_dv.py chat "what is 6 * 7?"
```

`hatch` upserts the whole brainstem onto OOTB tables only:

| What | OOTB record |
|------|-------------|
| Anchor + **soul** | `account` "RAPP System" (`description` = soul) |
| Users | `contact` |
| Config | `annotation` `subject=rapp.config` |
| **Agents** (agent.py in `notetext.sourcecode`) | `annotation` `subject=rapp.agent` |
| Memory (shared + user) | `annotation` `subject=rapp.memory` |
| Conversation + messages | `annotation` `subject=rapp.conversation` / `rapp.message` |

- **Source:** defaults to the global vTwin. Use `--from <raw/Pages base or folder>` to replicate a
  different brainstem, or `--defaults` for the bundled minimal one (`--soul-file` overrides its soul).
- **Idempotent:** upsert-by-id, safe to re-run. After hatching it auto-verifies with `compare`.
- **Compare outputs:** because the instance is identical to the global vTwin, run `chat`/agents
  against both and expect the same grounding; `compare` reports any drift (in-sync / drift / missing).

## 4. Chat in Copilot Studio

The CLI hatches the **data** (soul, agents, memory) onto OOTB Dataverse. The **brainstem loop** is
the AI Builder router prompt + a Power Automate flow; Copilot Studio is the chat surface.

1. **Router prompt** — create the AI Builder custom prompt from
   [`../brainstem/router_prompt.md`](../brainstem/router_prompt.md). Its grounding inputs are
   Dataverse `List rows` over the `annotation` table (`subject` = `rapp.agent` / `rapp.memory` / …).
2. **Orchestrator flow** — build the Power Automate cloud flow from
   [`../brainstem/orchestrator_flow.md`](../brainstem/orchestrator_flow.md). It loads the hatched records,
   calls the router prompt, dispatches agents, and returns the answer.
3. **Copilot Studio agent** — in [copilotstudio.microsoft.com](https://copilotstudio.microsoft.com):
   - Create an agent in the **same environment** you hatched into.
   - Add a **topic** (e.g. trigger "anything") whose action **calls the orchestrator flow**,
     passing the user's message (and the user id) and returning the flow's `final_answer`.
   - **Publish** → test in the Copilot Studio test pane, then channel it to **Teams / M365 Copilot**.

Because the agents, soul, and memory live in OOTB Dataverse, the bot is fully grounded the moment
it is published — and everything it learns (new `rapp.memory` / `rapp.message` notes) is queryable
in Dataverse and syncable back to the static twin.

## Commands

| Command | Purpose |
|---------|---------|
| `whoami` | WhoAmI — verify the app-user connection |
| `hatch [--soul-file F]` | Create the first brainstem (idempotent) |
| `agents list` | List `rapp.agent` notes |
| `memory list` | List `rapp.memory` notes (shared/user) |
| `seed <folder\|rawURL>` | Apply a brainstem export by upsert-by-id (twin sync) |
| `compare [--from SRC]` | Diff this instance vs the global vTwin (in-sync / drift / missing) |
| `chat "<msg>"` | Local grounded preview from live Dataverse |
| `selftest` | Offline: verify 1:1 identity with the static twin |
| `--dry-run` | Preview writes without making them |
| `--vtwin` / `--online` | Force the global vTwin (read-only) / a real connection |
| `--static <url>` | Use a different vTwin base URL |
