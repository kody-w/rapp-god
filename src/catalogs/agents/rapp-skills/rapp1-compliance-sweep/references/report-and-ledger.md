# RAPP/1 Sweep Ledger and Report

## File ledger

Use one row per tracked path and recursive archive member:

```text
target_commit
path
path_b64
container_path
container_id
member_id
parent_member_id
physical_member_index
raw_member_name_b64
entry_type
mode
git_object
recursion_depth
bytes
sha256
role
owner
mutability
source_or_generator
provenance
applicable_sections
evidence
finding
disposition
status
```

`path_b64` and `raw_member_name_b64` preserve exact Git/archive name bytes.
`container_path` is empty for ordinary files. Archive member paths may use a
stable display notation, but `container_id`, `member_id`, parent relation, and
physical index remain separate so duplicate names are not collapsed.

Reconcile archive coverage as an ordered multiset of unique member identities,
not a set of display paths:

```text
(container_id, physical_member_index, raw_member_name_b64)
```

Allowed terminal statuses:

- `REVIEWED-CONFORMANT`
- `REVIEWED-NON-RAPP`
- `JUSTIFIED-CONTEXT`
- `IMMUTABLE-OBSERVED`
- `OWNER-BLOCKED`
- `EXTERNAL-BLOCKED`
- `DRIFT`
- `NOT-REVIEWED:<reason>`

No default or empty status is allowed. Sort rows by raw path bytes where the
host permits, write UTF-8 with LF endings, and publish the exact ledger
SHA-256 as integrity evidence only. A ledger hash is not a RAPP address,
signature, or registry assertion.

## Repository report

```markdown
# RAPP/1 Sweep: <repository>

## Verdict
Coverage, authority pin, target structural result, authenticated acceptance,
and governance result.

## Authority and snapshot
Exact authority commit/hash plus target commit/tree/branch/dirty state.

## Coverage
Tracked paths, archive containers, recursive members, terminal rows, and set
equality checks.

## Findings and repairs
Path/line, role, applicable clause, observed evidence, before/after behavior,
and commit.

## Validation
Exact commands, environments, exit codes, and artifact/output hashes.

## Immutable and owner boundaries
Protected paths/hashes, owner inputs left null, and unresolved ceremonies.

## Issues
Umbrella and child issue links.

## Evidence
Ledger path and SHA-256.
```

## Decision-ready issue

```markdown
## Why
Name the RAPP/1 clause, observed behavior, impact, and evidence.

## What
State the decision or exact target-owned/owner action required.

## Where
Repository, audited commit, files, lines, artifacts, and authority pin.

## When
Trigger, prerequisites, ordering, and urgency.

## How
Safe steps that preserve immutable boundaries and avoid trust fabrication.

## Acceptance
Commands, output shapes, hashes, refusal cases, and evidence required to
close.

## Rollback or retirement
How to revert mutable work or retire the surface without modifying immutable
history.
```
