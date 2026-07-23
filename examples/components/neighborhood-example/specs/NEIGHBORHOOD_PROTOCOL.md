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
   → Creates ~/.neighborhood-example-data/<handle>/customers/ LOCALLY for customer data.
6. SE commits + pushes the new ses/<handle>/ dir back to the repo.
```

After step 6, the operator is fully joined: workflow agents loaded locally, front door visible to teammates, local customer-data dir set up.

## Join lifecycle (public gate)

Same as above but step 1 is implicit (membership is open) and the operator is added to `members.json` via PR rather than via collaborator invite.

## What lives where (the boundary)

| Lives in REPO (visible to all members) | Lives on DEVICE (only this SE sees it) |
|---|---|
| `agents/*` — sha256-pinned workflow | `~/.neighborhood-example-data/<handle>/customers/*` — customer data |
| `ses/<handle>/projects.json` — sanitized slugs + status | `~/.neighborhood-example-data/<handle>/customers/<slug>/status.json` — actual customer name + contacts |
| `ses/<handle>/front_door.md` — who you are at the Neighborhood Example team level | `~/.neighborhood-example-data/<handle>/customers/<slug>/notes.md` — working notes |
| `members.json` — who's in | `~/.brainstem/rappid.json` — your permanent identity |
| `CONSTITUTION.md` — the rules | `~/.brainstem/neighborhoods.json` — your subscription record |
| `rar/index.json` — workflow manifest | `~/.brainstem/.brainstem_data/*` — agent state |

The repo's `.gitignore` excludes `.neighborhood-example-data/` so customer data physically cannot be `git add`ed even by accident.

## Identity

Every neighborhood has its own `rappid.json` with a consolidated rappid like:

```
rappid:@<owner>/<slug>:<hex>
```

The rappid is the global address (CONSTITUTION Art. XXXIV.1: one string, no
`v2:`/`<kind>:` prefix, no `@github.com/...` suffix). `kind` lives in the
`rappid.json` record. All canonical URLs derive from it by string parsing — see
kernel Article XLVI.

A planted rapplication inside the neighborhood gets its own `rappid.json`
record (same `@<owner>/<slug>` location, its own hash, `kind: rapplication`):

```
rappid:@<owner>/<slug>:<hex>
```

…with `parent_rappid` pointing at the neighborhood's rappid.

## Workflow conformance

The neighborhood's rules are enforced through THREE mechanisms:

1. **sha256 in `rar/index.json`** — the joiner refuses agents whose bytes don't match the manifest. No silent agent drift.
2. **`.gitignore` excluding `.neighborhood-example-data/`** — physical block on customer data entering the repo.
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
