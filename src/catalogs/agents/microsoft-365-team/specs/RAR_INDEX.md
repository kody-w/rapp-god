# Spec: rar/index.json (the workflow manifest)

> Self-contained reference for the LLM. Tells you what `rar/index.json` looks like so you can read it, validate sha256s, and walk the user through fixes if a hash mismatches.

## Purpose

`rar/index.json` is the manifest of **what gets hot-loaded into a joining brainstem**. It lists every workflow agent, organ, sense, card, and rapplication that ships with this neighborhood, with sha256 hashes pinning each to its content.

When a brainstem joins, it walks this manifest; for each entry it fetches the file, computes sha256 over the bytes, and refuses to install if the hash doesn't match. This is the conformance mechanism that prevents silent agent drift across the Microsoft 365 Team team.

## Schema: `rapp-rar-index/1.0`

```json
{
  "schema": "rapp-rar-index/1.0",
  "name": "billwhalen-agent-team",
  "rar_for": "billwhalenmsft/agent-team-private",
  "purpose": "...",
  "version": "1.0",
  "created_at": "2026-05-10T20:55:00Z",
  "raw_url_prefix": "https://raw.githubusercontent.com/billwhalenmsft/agent-team-private/main",
  "required_for_participation": [ ... ],
  "kernel_base_included": [ ... ],
  "optional_for_participation": [ ... ],
  "organs": [],
  "senses": [],
  "cards": [],
  "rapplications": [ ... ]
}
```

## Per-item shape

Each entry under `required_for_participation` (or `optional_for_participation`, or `organs`, etc.) has this shape:

```json
{
  "kind": "agent",
  "name": "OutcomeFramer",
  "metadata_name": "OutcomeFramer",
  "file": "agents/microsoft-365-team_outcome_framer_agent.py",
  "raw_url": "https://raw.githubusercontent.com/<owner>/<repo>/main/agents/microsoft-365-team_outcome_framer_agent.py",
  "sha256": "ba01c0d56901c428...",
  "schema": "rapp-agent/1.0",
  "description": "Frames the outcome of any work item before build begins."
}
```

### Field meanings

- **`kind`** — `agent` | `organ` | `sense` | `card` | `rapplication`. The hot-loader uses this to route to the correct local directory.
- **`name`** / **`metadata_name`** — the class name the brainstem will register the agent as. Must match the `metadata.name` field inside the agent file.
- **`file`** — the path within the repo (relative to repo root).
- **`raw_url`** — the canonical fetch URL. For private repos this is informational; the joiner reads from disk after cloning.
- **`sha256`** — hex-encoded SHA-256 of the file's bytes. The conformance gate.
- **`schema`** — the agent's contract version. Currently `rapp-agent/1.0` for everything.
- **`description`** — human-readable summary of what the agent does.

## Validation procedure (for the LLM)

When you (the LLM) help install agents from this manifest:

1. Open `rar/index.json` and parse as JSON.
2. Confirm `schema` field is exactly `"rapp-rar-index/1.0"`. If not, refuse to proceed and report the mismatch.
3. For each entry in `required_for_participation`:
   a. Open the file at `<repo-root>/<file>`.
   b. Read all bytes.
   c. Compute sha256 (hex).
   d. Compare to `entry["sha256"]`. If different — STOP, report the entry name + expected + actual. Do not install.
   e. If match — copy the file to the local brainstem's agents/ directory.
4. After all entries succeed, the install is complete.

## What a sha256 mismatch means

If the sha256 doesn't match, ONE of these happened:

- **Bit rot** — the file was corrupted in transit (sneakernet to USB to USB) or by disk error. Have the user re-receive the repo from a clean source.
- **Tampering** — someone modified the agent file outside the planter flow. Refuse to install; report.
- **Manifest drift** — the neighborhood owner edited the agent file but forgot to re-run BillPlanter to refresh `rar/index.json`. Tell the user to ping the owner.

In all three cases the resolution is: do NOT install the unmatched agent. Report and let the human resolve.

## Updating the manifest (owner-side)

The neighborhood owner updates the manifest by re-running `BillPlanter`:

```python
BillPlanter(owner="<owner>", name="<name>", dry_run=False)  # idempotent for files; refreshes rar/index.json with current sha256s
```

This is the ONLY supported way to update the manifest. Hand-editing `rar/index.json` is an antipattern — sha256s will drift from the actual file bytes and joining brainstems will reject the agents.

## See also

- Agent contract: `AGENT_CONTRACT.md`
- Neighborhood protocol: `NEIGHBORHOOD_PROTOCOL.md`
- Constitution Article IV (sha256 pinning): `../CONSTITUTION.md`
