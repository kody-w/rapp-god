# Spec: RAPP neighborhood protocol

> Self-contained reference for the LLM. Tells you how a neighborhood works so you can read this directory's structure correctly and walk the user through joining it.

## What a neighborhood is

A **neighborhood** is a public OR private GitHub repo containing:

- An identity (`rappid.json`) — its permanent address
- Metadata (`neighborhood.json`) — what kind of gate, who joins how
- A member roster (`members.json`) — who's in
- Workflow agents (`agents/`) — single-file Python agents per the agent contract
- A manifest (`rar/index.json`) — sha256-pinned list of what gets hot-loaded by joining brainstems
- A constitution (`CONSTITUTION.md`) — the rules every member honors
- Optional: rapplications (`rapplications/<name>/`), per-member front doors (`ses/<handle>/`), specs (`specs/`)

## The two roles

- **Owner** — minted the gate, has push access, can amend the constitution.
- **Member** — has been added as a collaborator (private gates) OR is listed in `members.json` (public gates). Can read everything; can submit changes via PR.

## Join lifecycle (private gate, this neighborhood)

```
1. Owner adds the operator as a GitHub collaborator on the private repo.
2. SE clones the repo locally (gh repo clone <owner>/<repo>).
3. SE drops the joiner agent into their brainstem agents/ directory.
4. SE chats: "join <owner>/<repo>".
   → Joiner reads rar/index.json from the local clone.
   → For each agent listed: sha256-verify against manifest, copy to local agents/.
   → Records the subscription at ~/.brainstem/neighborhoods.json.
5. SE chats: "SesWorkspaceInit setup".
   → Mints ses/<handle>/ in the cloned repo (sanitized metadata).
   → Creates ~/.microsoft-365-team-data/<handle>/customers/ LOCALLY for customer data.
6. SE commits + pushes the new ses/<handle>/ dir back to the repo.
```

After step 6, the operator is fully joined: workflow agents loaded locally, front door visible to teammates, local customer-data dir set up.

## Join lifecycle (public gate)

Same as above but step 1 is implicit (membership is open) and the operator is added to `members.json` via PR rather than via collaborator invite.

## What lives where (the three-tier boundary)

Per kernel spec `pages/docs/PUBLIC_PRIVATE_BOUNDARY.md` v1.1, this neighborhood obeys the three-tier estate model: **PII NEVER lives in the repo by default, even the private one.** The repo holds the *bones* of the digital organism; the operator's local device holds the *substance*.

| Lives in PUBLIC ESTATE (zero PII) | Lives in THE REPO ("bones" — visible to collaborators) | Lives ONLY ON DEVICE ("substance" — never in any repo by default) |
|---|---|---|
| Operator rappid | `agents/*` — sha256-pinned workflow | Real customer / client / patient names |
| Door catalog (rappid → URLs only) | `rapplications/<name>/` | Email addresses, phone numbers, contracts |
| Beacon (`.well-known/rapp-network.json`) | `ses/<handle>/projects.json` — slugs + status enums + dates ONLY | Customer-specific outcomes, KPI values |
| Activity feed (public-shaped) | `ses/<handle>/front_door.md` — sanitized | Mailbox content, transcripts, working notes |
| `private_estate_pointer` + commitment hash | `members.json` — handles + roles | Personal memory / journal / drafts |
| ZERO PII | `CONSTITUTION.md` + `rar/index.json` + `neighborhood.json` + `soul.md` | Voice recordings, screenshots, attachments |
| ZERO PII | **ZERO PII by default** (kernel §1.5) | `~/.brainstem/neighborhoods/microsoft-365-team/<handle>/customers/<slug>/` |

The repo's `.gitignore` excludes `.brainstem/` and `.microsoft-365-team-data/` so customer data physically cannot be `git add`ed without an intentional operator action.

**Three threat models closed at once:**

- *Public web sees PII* → blocked by the private repo's GitHub-collaborator gate
- *GitHub-the-vendor sees PII* → blocked by PII never being in the repo at all (the kernel's §1.5 tightening)
- *Collaborator-of-collaborator correlation* → blocked by `projects.json` revealing only opaque slugs + status enums

**Override:** the operator MAY put PII in the repo by an explicit action — see kernel spec `PUBLIC_PRIVATE_BOUNDARY.md` §1.6 for the four override paths. None of them are automatic. Article VIII (operator-mediated) governs throughout.

## Identity

Every neighborhood has its own `rappid.json` with a v2 rappid like:

```
rappid:v2:neighborhood:@<owner>/<repo>:<32-hex>@github.com/<owner>/<repo>
```

The rappid is the global address. All canonical URLs derive from it by string parsing — see kernel Article XLVI.

A planted rapplication inside the neighborhood gets its own variant rappid:

```
rappid:v2:rapplication:@<owner>/<repo>#<rapp-name>:<32-hex>@github.com/<owner>/<repo>
```

…with `parent_rappid` pointing at the neighborhood's rappid.

## Workflow conformance

The neighborhood's rules are enforced through THREE mechanisms:

1. **sha256 in `rar/index.json`** — the joiner refuses agents whose bytes don't match the manifest. No silent agent drift.
2. **`.gitignore` excluding `.microsoft-365-team-data/`** — physical block on customer data entering the repo.
3. **The agents themselves** — they gate behavior on each other (e.g. OutcomeValidator refuses to archive without explicit owner sign-off).

Constitutional rules in `CONSTITUTION.md` are also enforced socially: if a teammate violates them, you raise it as an issue + amend the agent or the constitution.

## Federating with other neighborhoods (out of scope for first install)

A neighborhood can have outbound references to other gates via `members.json` cross-listing or via a separate `federation.json`. This isn't required for this neighborhood and isn't covered here.

## See also

- this neighborhood constitution (this neighborhood's specific rules): `../CONSTITUTION.md`
- Agent contract: `AGENT_CONTRACT.md`
- Manifest format: `RAR_INDEX.md`
- Offline / sneakernet setup: `../OFFLINE_SETUP.md`


## Sneakernet portability invariant (kernel rule)

Per the kernel rapplication-sdk.md spec, an artifact shared between operators consists of EXACTLY two files: one `agent.py` (the bootstrap — `egg_hatcher_agent.py`) and one `.egg`. The receiver:

1. Drags the `.py` into their brainstem's `agents/` directory (file browser, no terminal).
2. Sends one chat: `EggHatcher from_egg=/path/to/file.egg`.

That is the entire setup. NO shell commands. NO config edits. NO restarts. NO follow-up chats. The bootstrap does workspace mint, rappid mint, sha256 verification, agent install, and subscription recording in the single chat.

If a flow asks the receiver to do anything beyond drag + chat, the artifact is not sneakernet-portable. The bootstrap agent is necessarily multi-mode (`from_egg` / `from_repo` / `pack_egg` / `status`) precisely so the receiver never needs more than one agent for any scenario.

### The docstring IS the readme

The sneakernet payload is exactly two files: `egg_hatcher_agent.py` + `.egg`. NO separate README.md / README.txt / INSTRUCTIONS file. The bootstrap agent's top-level docstring is the readme — both human-readable (drag + chat) and LLM-driveable (a section explicitly addressed to whichever LLM is shown the file). Adding a third file expands the payload past two and breaks the invariant.

This is sacred per kernel `pages/docs/rapplication-sdk.md` — Sneakernet portability invariant § "The docstring IS the readme."

