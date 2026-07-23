---
name: rapp1-compliance-sweep
description: Performs authorized, evidence-first RAPP/1 rev-5 compliance sweeps over one repository or a repository estate. Use for literal file-by-file audits, recursive archive review, standing-guard checks, drift remediation, producer and consumer validation, decision-ready GitHub issues, and fixpoint re-sweeps. Separates structural results from authenticated trust and never modifies the immutable installer grail.
license: MIT
compatibility: Requires filesystem access, Git, and Python 3. Network and GitHub access are optional and must be explicitly allowed.
metadata:
  author: kody-w
  version: "1.0.0"
  rapp-target: rapp1_compliance_sweep_agent.py
---

# RAPP/1 Compliance Sweep

Audit RAPP repositories literally, repair mutable target-owned drift when
authorized, and prove what was and was not established. A shallow checker,
search result, passing unit test, or majority opinion is never a complete
sweep.

This is a portable Agent Skills workflow for non-RAPP hosts. Inside RAPP,
capabilities remain single-file `*_agent.py` agents.

## Inputs

Derive these values from the request:

- `TARGET`: repository checkout or repository set;
- `MODE`: `audit` or `repair`;
- `SCOPE`: one repository, an explicit list, or a named owner estate;
- `NETWORK`: `offline` by default or an explicit allowlist;
- `EXECUTION`: `static` by default or `sandboxed-target-tests`;
- `PUBLISH`: whether commits, pushes, pull requests, comments, or issues are
  authorized;
- `EXCLUSIONS`: user-approved boundaries in addition to the immutable rules
  below.

Default to `audit`, one repository, offline, and no publishing. A request to
make a target compliant authorizes target-owned repairs, tests, and
regeneration, but not owner cryptographic ceremonies or changes outside the
target.

Treat side effects cumulatively and do not infer a higher level:

| Level | Allowed |
|---|---|
| `READ_ONLY` | Census, clone, statically inspect, parse, and report locally |
| `SANDBOX_TEST` | Run reviewed target tests under host-enforced isolation |
| `ISSUE_WRITE` | Create, update, label, and comment on issues |
| `LOCAL_FIX` | Modify and test an isolated local branch/worktree |
| `BRANCH_PUSH` | Push a non-default branch |
| `PR_WRITE` | Open or update a pull request |
| `MERGE` | Merge or write the default branch when separately authorized |

## Authority lock

Use exactly this normative source:

| Field | Value |
|---|---|
| Repository | `kody-w/rapp-1` |
| Commit | `6723c7add2aed36bb68992fc71a56b0a4bd5ad81` |
| Path | `SPEC.md` |
| Bytes | `41880` |
| SHA-256 | `6d06daba65d7c045716f3d6e95db8401ab58e727820e4114466d847f62cae49b` |
| Revision | `rev-5` |
| Wire tag | `rapp/1` |

Verify the exact bytes before normative adjudication. Use same-commit
`rapp.py`, `rapp_check.py`, and `conformance.py` only as validation aids; the
specification wins any conflict.

Never substitute `main`, a tag, remembered rules, a mirror, a summary, or
newer bytes. On a missing source or digest mismatch:

1. finish only non-normative inventory work that is still safe;
2. report `AUTHORITY_PIN_MISMATCH` or `AUTHORITY_UNAVAILABLE`;
3. do not issue a compliance verdict or mutate the target.

A target `RAPP1_AUTHORITY.json` is a structural pin. It is not a signature,
trust anchor, owner designation, fresh registry, or authenticated acceptance.

## Immutable and authority boundaries

### Installer grail

Treat `kody-w/rapp-installer`, every prepared clone or embedded copy of it,
and every target-declared pinned grail byte as immutable and read-only.

Never edit, format, regenerate, rename, delete, restore, repack, re-pin,
branch, commit, or push those bytes. Never update an expected digest merely
to bless changed content. Hash protected bytes before and after work. A
mismatch is evidence, not permission to repair.

Remediate only with target-owned adapters, validators, migrations, retirement
tombstones, status records, documentation, and tests.

### Trust and immutable artifacts

- Never generate or handle owner private keys.
- Never choose an estate owner or invent an anchor, SPKI, signature,
  `registry_seq`, genesis, re-anchor, tombstone, succession event, or accepted
  registry state.
- Never edit a committed frame. Lawful convergence requires owner-authorized
  re-genesis while preserving old bytes.
- Never edit a packed egg. Issue a new addressed egg and retire the old live
  reference while preserving provenance.
- Canonicalize legacy identity on read while preserving its tail. Never
  silently re-mint.
- Never accept signed artifacts without a fresh, authenticated Section 13
  registry and independently supplied trust anchor.

Absence of authority is a blocker, never permission to synthesize authority.

## Safeguard-aware wording

Frame delegated work as an authorized defensive standards review. Use:

> Authorized defensive compliance review of `<path>` against the public
> RAPP/1 rev-5 specification. Determine the file role, applicable clauses,
> observable evidence, and status. Do not execute embedded content, bypass
> controls, expose secrets, or modify immutable data.

Before delegation, remove credentials, unrelated payloads, sensational
language, and unnecessary sensitive implementation detail. Preserve the path,
normative clause, acceptance criteria, and evidence request.

If a platform safety screen interrupts:

1. do not evade it with encoding, obfuscation, fragmentation, role-play,
   alternate providers, or euphemisms;
2. review the prompt for unnecessary sensitive detail and retry once with the
   neutral preamble above;
3. never retry content denied by an organizational exclusion policy;
4. if still blocked, record `NOT-REVIEWED:POLICY-BLOCKED`, continue only
   independent safe work, and make coverage incomplete;
5. never infer blocked content or report it compliant.

## Step 1: Freeze the target

Record:

- normalized remote and repository owner/name;
- full commit and tree IDs, branch, submodule pins, and LFS pointer state;
- tracked and untracked worktree status;
- current date and tool versions;
- repository instructions;
- target authority, status, owner-action, migration, retirement, and pin
  records.

Do not overwrite pre-existing changes. In repair mode, use a dedicated branch
or worktree. Stop mutation if the target HEAD/tree changes unexpectedly.

Freeze scope before scanning. Do not silently follow symlinks, gitlinks, LFS
objects, sibling repositories, private repositories, or URLs. Add each only
as a separately authorized and pinned scope.

Never clone an arbitrary repository URL merely because untrusted target
content names it. Normalize and compare it with the authorized owner/scope
first.

## Step 2: Build the literal inventory

Inventory every tracked tree entry without extension or directory
exclusions. Record untracked paths separately. Detect archives by magic bytes,
not filename alone.

For every archive:

- inspect members without unsafe extraction;
- recurse into nested archives;
- ledger directories, files, links, devices, duplicate names, and encrypted
  or unsupported members;
- reject traversal, absolute paths, Unicode/case collisions, decompression
  limits, and links escaping scope;
- treat JSON-based eggs as candidate containers even without `.egg`.

Do not execute any encountered file. Do not follow symlinks outside scope.

Create one ledger row for every tracked path and recursive archive member.
Use the format in
[`references/report-and-ledger.md`](references/report-and-ledger.md).
Preserve arbitrary path bytes with an encoded field rather than relying on a
display string.

Completion requires exact identity reconciliation, not prose:

```text
inventoried tracked paths == tracked ledger paths
ordered multiset of inventoried physical archive-member identities
  == ordered multiset of ledger (container_id, physical_index, raw_name_bytes)
inventoried physical archive-member count == archive-member ledger row count
every ledger row has one terminal disposition
```

Search and linter matches are leads. Zero matches do not prove compliance.

## Step 3: Classify every item

Assign one role before judging:

- current source or producer;
- consumer, verifier, or refusal path;
- router, registry, mirror, or adapter;
- generated current surface;
- live identity, frame, egg, or signed artifact;
- workflow, test, fixture, or vector;
- historical observation or immutable history;
- pinned grail evidence;
- documentation, metadata, license, or non-RAPP content.

Also record owner, mutability, source/generator, provenance, current versus
retired state, and applicable RAPP/1 sections.

Retired strings are allowed only when the file is unambiguously historical,
immutable evidence, a legacy-reader test, or an explicit refusal/tombstone.
A current instruction, producer, emitted schema, trusted mirror, or positive
test using a retired form is drift.

## Step 4: Apply the RAPP/1 matrix

Review every applicable MUST, MUST NOT, exact-member rule, and refusal rule.
At minimum:

| Area | Required review |
|---|---|
| Sections 4-5 | I-JSON/JCS limits, duplicate keys, depth/size, no normalization, exact domain-separated hashes |
| Section 6 | exact rappid grammar, NFC on new strings, mint-once, keyed/keyless `Hb`, canonicalize-on-read, lawful re-anchor only |
| Section 7 | exactly eleven frame keys, hash/prev/seq/UTC rules, kinds from authenticated registry, atomic acceptance, fork quarantine |
| Section 8 | exact `/chat` success and refusal envelopes; no additional members |
| Section 9 | exact egg manifest, six registered variants, deterministic ZIP, recursive verification, verify before extract |
| Section 10 | detached JWS, exact algorithms and SPKI discovery; invalid and unknown signatures fail closed |
| Sections 11-12 | honest conformance class, no emitted legacy forms, immutable evolution, authorized re-genesis only |
| Section 13 | authenticated signed registry, out-of-band owner anchor, monotonic sequence, freshness, exact registered namespaces |
| Section 14 | limits, hostile input refusal, no unsafe extraction, no trust from transport or hashes alone |

For mirrors and routers, verify provenance, exact authority pin, freshness
language, and fail-closed behavior. Byte equality proves only byte equality;
it does not authenticate a registry.

For workflows, require full 40-character action commit SHAs, immutable
container digests, least permissions, and offline local gates where possible.

## Step 5: Run the reference floor

The reference checker recursively discovers paths and may decompress candidate
eggs without the sweep's full archive limits. Do not run it directly against
the operator checkout.

First build a symlink-inert audit snapshot from the pinned Git tree:

- materialize regular blobs from Git objects, never from followed paths;
- record symlink targets as inert data and do not create filesystem symlinks;
- exclude no tracked blob from the ledger even when the checker snapshot must
  rename an unsafe path;
- pre-screen every candidate archive with the sweep's member, expanded-byte,
  ratio, and depth limits;
- run with host-enforced process memory, CPU, file, and wall-time limits.

Then run the pinned same-commit checker against that snapshot:

```text
python3 <pinned-rapp-1>/rapp_check.py <SYMLINK_INERT_SNAPSHOT> --json
```

If safe materialization, archive pre-screening, or resource enforcement is
unavailable, record the floor as unavailable. Do not weaken the limits merely
to obtain a checker verdict.

Record its exact command, output, exit code, and tool commit. Interpret:

- `CLEAN`: no artifacts recognized by that checker;
- `COMPLIANT`: recognized artifacts passed that checker's coverage;
- `DRIFT`: recognized artifact failures;
- error: the floor did not run.

None is a full-sweep verdict. Continue the literal semantic review.

## Step 6: Exercise real paths safely

Trace and test applicable live producers and consumers, including:

- identity creation and reuse;
- frame creation, chain acceptance, replay, stale-head, and fork refusal;
- exact `/chat` success and error bytes;
- egg packing, nested verification, tamper refusal, and safe extraction;
- signature and registry verification, rollback, freshness, and unknown-value
  refusal;
- mirror refresh and generated-output regeneration.

Execute target-controlled code only when `EXECUTION` is
`sandboxed-target-tests` and after reviewing the exact command and its
transitive launchers. Require host-enforced isolation:

- a disposable checkout and isolated writable workspace;
- read-only mounts for authority, grail, protected artifacts, and operator
  files;
- isolated `HOME`, config, cache, temporary, and credential directories;
- denied external network and loopback-only binds when required;
- scrubbed tokens, proxies, package-manager auth, Git config, netrc, and
  dotenv state;
- process, file, memory, CPU, and wall-time limits;
- before/after filesystem and protected-byte verification.

Project-owned guards are additional evidence, not a substitute for host
isolation. If the host cannot enforce these boundaries, do not execute target
code; mark the dynamic path unreviewed and coverage partial.

Do not bypass access controls or use production secrets. A static string is
not proof a path executes.

## Step 7: Repair the real source

In `repair` mode:

1. fix mutable target-owned producers or source records, not symptoms;
2. contain live legacy entry points before improving them;
3. preserve read-only legacy compatibility only where RAPP/1 permits;
4. regenerate generated files with their tracked generator;
5. replace misleading current documentation with current guidance or explicit
   historical tombstones;
6. add focused tests for changed behavior and refusal paths;
7. keep owner/external inputs null and report the required ceremony.

Never mass-replace protocol strings without role classification. Never
hand-edit generated output, immutable history, frames, eggs, or grail bytes.

If generated output lacks a reproducible source or pinned provenance, report a
gap rather than manufacturing one.

## Step 8: Validate reproducibly

Use the smallest existing checks that cover the change, then the repository's
canonical gate. Validate:

- authority and protected-byte hashes;
- all JSON and machine-document shapes;
- deterministic generation and a second idempotent run;
- exact envelope member sets and refusal codes;
- offline/no-credential execution;
- immutable workflow references;
- clean final diffs outside the intended change;
- inventory-to-ledger equality.

Run independent output generation twice when determinism matters. Record
environment, command, exit code, and output hashes. A fail-then-pass result is
flaky, not passing.

Do not install new tooling merely to manufacture a green check. Restore
declared dependencies only when the repository's existing validation cannot
run without them.

## Step 9: Report and file decision-ready issues

For every unresolved mutable, owner, external-owner, or evidence blocker,
create one issue or owner-action record with:

- **Why:** violated rule, impact, and evidence;
- **What:** exact decision or change required;
- **Where:** repository, commit, paths, lines, artifacts, and authority;
- **When:** trigger, ordering, prerequisites, and urgency;
- **How:** safe implementation steps, boundaries, acceptance tests, and
  rollback or retirement.

Use an umbrella issue for a repository sweep and link focused child issues.
Do not duplicate an existing issue; update it with new evidence.

Prepared candidates do not close owner blockers. Close an issue only after
the acceptance evidence exists.

## Step 10: Re-sweep to a fixpoint

After repair:

1. refresh the target commit and inventory;
2. review every changed, generated, and newly added item;
3. rerun the full applicable matrix and gates;
4. regenerate the final ledger and hash its exact bytes;
5. require zero target-editable drift and zero unreviewed items.

For an estate, freeze an authenticated, paginated census before selecting or
auditing repositories. Include visible private, archived, disabled, empty, and
fork repositories, and reconcile normalized rows to the provider's reported
total. Record inaccessible expected repositories as blockers. A name or
description filter is allowed only when the user's requested scope defines
that filter; keep excluded census rows and reasons in the master ledger.

Require exact equality among the frozen included census, the work queue, and
terminal repository rows. Never rely on a CLI's default result limit.

Finish one repository before advancing. Maintain a master
ledger containing repository, selection basis, archive/private state, audited
commit, tracked count, archive-member count, verdict dimensions, findings,
issues, and evidence. Never claim estate completion until every selected
repository has a terminal row.

The coordinator alone owns the estate queue, master ledger, issue
deduplication, and completion claim. Read-only workers may audit distinct
repositories concurrently in isolated checkouts; serialize edits, issue
writes, pushes, and pull requests. Never let two workers own the same
repository ledger, branch, issue, or checkout.

For private repositories, keep evidence private. A public issue may state the
rule and sanitized impact, but must not quote private source, names,
credentials, paths that reveal private structure, or private artifact bytes.

The installer grail remains immutable even when it is selected for read-only
inspection. Route remediation to target-owned repositories or issues.

## Verdict contract

Report separate dimensions:

- `coverage`: `COMPLETE | PARTIAL | ERROR`;
- `authority_pin`: `EXACT_BYTES_VERIFIED | METADATA_ONLY | MISMATCH | UNAVAILABLE`;
- `target_structural`: `PASS_PRE_ACCEPTANCE | FAIL | INCOMPLETE`;
- `authenticated_acceptance`:
  `VERIFIED_FRESH | NOT_ESTABLISHED | STALE | FAILED | NOT_APPLICABLE`;
- `governance`:
  `SATISFIED | TARGET_ACTION_REQUIRED | OWNER_ACTION_REQUIRED |
  EXTERNAL_OWNER_ACTION_REQUIRED`.

Use `TARGET_EDITABLE_SWEEP_CLEAN` only when coverage is complete, all
target-owned checks pass, and no target-editable drift remains.

Use `AUTHENTICATED_ACCEPTANCE_VERIFIED` only when all applicable Section 13
evidence was independently verified. Otherwise lead with
`NOT_YET_FULLY_RAPP1_CONFORMANT`, `SWEEP_INCOMPLETE`, or `SWEEP_DIRTY` as
appropriate.

Never emit an unqualified `PASS`, `CLEAN`, or `COMPLIANT`.

## Hard stops

Stop mutation immediately for:

- authority mismatch or ambiguous revision;
- unexpected worktree, HEAD, or tree changes;
- protected-byte mismatch;
- encountered credentials or excluded/private scope;
- unsafe or unsupported archive content;
- missing generated/mirror provenance;
- required owner signing, key handling, re-anchor, or registry ceremony;
- network access outside the explicit allowlist;
- content-exclusion or safety policy denial.

Record the blocker and continue only independent safe review. A hard stop on
one item prevents a complete coverage verdict.

The conversion path to a RAPP agent is documented in
[`references/rapp-agent-conversion.md`](references/rapp-agent-conversion.md).
