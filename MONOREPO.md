# RAPP assimilated monorepo

## Scope and honesty

This repository has two simultaneous roles:

* an **append-only observatory** whose existing `api/`, `snapshot/`,
  `versions/`, and `registry.json` URLs remain public ABI; and
* an **assimilated public monorepo** containing a complete disposition for the
  frozen 198-repository selection (197 external sources plus the native
  `rapp-god` root): exact bytes where publishable, opaque withholding where a
  public artifact would amplify private repository identifiers.

The pass covers 370 public repository decisions and dispositions all 42,175
external tree entries (1,904,914,693 source bytes). It materializes 41,471
exact payload entries, records one external gitlink, and opaquely withholds 716
paths (244,661,926 bytes). Another 142 repositories are quarantined only as an
aggregate count because this target is public. Five public repositories are
empty. `PowerApps` is an explicit substring/fork false positive. Private source
payloads and per-repository private capture metadata are not imported.
Existing public observatory history may contain public textual references to
private identifiers; that remains an explicit owner remediation and history is
not rewritten.

Assimilation does **not** establish full RAPP/1 conformance. The exact RAPP
baseline continues to lead with **NOT YET FULLY RAPP/1 CONFORMANT**, and its
four owner-action blockers remain open.

## Authority order

1. `authority/protocol/rapp-1/` is the exact unlicensed RAPP/1 rev-5 source at
   commit `6723c7a`. It is structural authority only, not authenticated
   section-13 acceptance.
2. Federal governance retains the public RAPP source commit/tree pin at
   `e5436fb`, but its content is withheld by the private-boundary gate.
   Ratification, owner decisions, and lifecycle fail closed—not technical
   protocol.
3. `vendor/grail/rapp-installer-brainstem-v0.6.9/` is the exact immutable LTS
   grail at commit `bded0e1`.
4. Target-owned adapters, guards, and migrations may surround authorities but
   never rewrite them.
5. Imported implementations are evidence and implementation material.
6. Generated catalogs and observatory views are derivative indexes.

Current `rapp-installer` main (`5fbde17`, version 0.6.16) lives separately at
`vendor/upstream/rapp-installer-main/` and is observe-only. It cannot silently
replace the LTS grail.

## Semantic layout

Exact repository boundaries remain component boundaries inside role-based
domains:

| Domain | Purpose |
|---|---|
| `authority/` | Protocol authority plus target-owned authority records |
| `vendor/grail/` | Immutable LTS fixture |
| `vendor/upstream/` | Observed upstream source, subordinate to pins |
| `src/protocol/` | Protocol implementations and related source |
| `src/runtime/` | Kernels, SDKs, CLIs, and runtime baselines |
| `src/codecs/` | Frames, envelopes, sealed channels, moments, and state codecs |
| `src/catalogs/agents/` | Agent catalogs and agent repositories |
| `src/network/` | Neighborhood, flight, kite, and network components |
| `src/release/` | Release channels, controls, and distributions |
| `src/experiences/` | Games, visual experiences, and interactive applications |
| `src/workflows/` | Workflow engines; RDW and UltraCode are peers here |
| `products/` | Coherent products, including a separate OpenRappter product |
| `services/` | Hubs, APIs, forums, and static services |
| `integrations/` | MCP, Dataverse, SharePoint, deployment, and editor bridges |
| `instances/examples/` | Twins, binders, planted places, and neighborhoods |
| `examples/components/` | Demonstrations, walkthroughs, templates, and fixtures |
| `docs/components/` | Documentation, maps, roadmap, marks, and governance |
| `migrations/` | Explicit migrations and experiments |
| `observatory/` | Active body/spine component observatories |
| `archive/generations/` | Historical generations retained byte-for-byte |
| `archive/retired/` | Retired protocol evidence with successor records |
| `archive/placeholders/catalog/` | Anatomy and placeholder repositories |
| `catalog/` | Generated component, domain, and artifact indexes |
| `provenance/` | Complete decisions, locks, file mappings, and external pins |
| `tests/` | Target-owned offline integrity tests and imported test components |

OpenRappter stays under `products/openrappter/`, with its release variants
under its own `release/channels/`; the current imported snapshot is marked
stale and upstream-owned. Rappterbook v1 and v2 remain explicit social product
generations. Exact duplicate bytes may occur at several semantic paths; Git
object storage deduplicates them while `provenance/files.jsonl` retains each
origin and alias.

## Exact import boundary

Each external component root is produced with `git archive HEAD | tar -xf`.
No `.git` directory is copied. Regular bytes, executable modes, and symlink
targets are checked against the source Git blob IDs and SHA-256 ledger. No
authored adapter or index is placed inside an imported root.

The orphan `rappterbook-agent/openclaw` gitlink is recorded at its exact object
ID in `provenance/external-pins.json`; it has no `.gitmodules`, receives no
payload, and is not fetched.

Nested imported `.github/workflows/` files are preserved as inert source
artifacts because they are below component roots. Only workflows directly in
the monorepo root `.github/workflows/` are active.

## Provenance and catalogs

* `provenance/repositories.jsonl` has one decision for every public repository.
* `provenance/sources.lock.json` pins all 198 selected source trees and semantic
  destinations.
* `provenance/files.jsonl` maps every selected external tree entry, plus the
  separate LTS alias. 716 denied entries are represented only by opaque
  ordinals and a withheld disposition—never sensitive paths, names, or hashes.
* `provenance/archive-members.jsonl` accounts for 3,086 members discovered by
  signature in 100 top-level and two nested ZIP/TAR containers, including
  EPUB/VSIX shapes and the separate grail. The proof records 26,388,889
  pre-quarantine uncompressed bytes, zero dangerous paths/link targets, zero
  member secret hits, two duplicate names, and zero incomplete scans/errors.
  Nine containers implicated by the private boundary are withheld; public
  indexes contain only retained containers and members.
* `provenance/refs.jsonl` namespaces 5,083 remote heads and 169 tags as an
  external OID inventory. Only default-tree snapshots are imported; histories
  and the 4,289 rappterverse heads are not recreated as target refs. Twenty-two
  denied ref records are opaque ordinals. The eight-wave ref/release collection
  is explicitly non-atomic (`2026-07-23T05:11:01Z`–`05:11:11Z`); selected
  default-tree pins have independent per-repository capture times and may
  intentionally predate those observations.
* `provenance/releases.jsonl` and `provenance/release-assets.jsonl` preserve 75
  releases across 41 repositories and all 50 supplied asset URLs, SHA-256
  digests, and sizes (1,204,660,676 logical bytes). Assets remain external;
  four oversized ez-rapp AppImages are never Git blobs.
* The observatory currently has 60 parts, 265 part-version records and
  hash-verified physical frames, zero standalone frames, and one explicit
  no-payload tombstone. There are zero unexplained physical orphans.
* `catalog/components.jsonl` includes lifecycle, authority/currentness,
  compatibility, ownership, publish status, and a synthetic immutable grail.
* Semantic catalogs cover protocol families, AST-derived agent identities and
  capabilities, never-remint identity findings, split workflow kinds, service
  topology, runtime profiles, release overlays, and portability.
* `catalog/test-suites.jsonl` gives every selected component detected suites
  or explicit none plus argv/cwd/safety/runtime/OS/dependency/evidence fields.
* `provenance/source-captures.jsonl` binds all 198 selected commits/trees to
  their own non-atomic capture times across
  `2026-07-23T04:48:04Z`–`05:49:36Z`; it makes no atomic owner snapshot claim.

Native terminology calls capabilities **agents**. Historical alternate wording
is retained only where it occurs inside exact imported artifacts.

## Updating

This is a frozen assimilation pass, not a floating subtree checkout.

1. Inventory public sources and quarantine private sources before inspecting
   payloads.
2. Review inclusion decisions and secret-scan findings.
3. Pin commits and trees; update the explicit selected census and semantic
   classifier in `tools/assimilation.py`.
4. Import into new component roots with the bulk archive command. Never edit a
   source clone or an existing exact component root.
5. Regenerate provenance and indexes.
6. Generate independent source archive evidence with explicit
   `scan-source --source-cache ... --output ... --captured-at ...`, then bind
   it using `tools/archive_inventory.py generate --evidence ...`.
7. Regenerate namespaced ref/release metadata with
   `python3 tools/ref_inventory.py --evidence-dir <provenance-results>`.
8. Review component licensing and authority effects.
9. Run `python3 -m unittest tests.test_assimilation tests.test_compat -v`.
10. Regenerate the legacy observatory only through `build_god.py`; never
   hand-edit `registry.json`.

An upstream repository update therefore creates a new reviewed assimilation
event. It does not mutate the historical source assignment silently.

## Publish closure

Before quarantine, exact nested `.gitignore` rules hid 985 materialized paths
(345,500,245 logical bytes). Opaque withholding removes two of those paths;
the final staging plan covers 983 ignored retained paths (246,506,738 logical
bytes). After the staged secret scan passes, run
`python3 tools/stage_materialized.py --stage`. The NUL-safe tool supplies NFC
logical paths, force-stages every ledger destination and target-owned file,
then checks the exact index path/blob/mode closure. It never commits or pushes.

## Compatibility and limits

The root workspace deliberately imposes no universal package manager,
interpreter environment, build, or deployment. Imported dependency locks and
tests stay with their components. The root CI performs offline integrity only;
it does not execute untrusted imported hooks, workflows, applications, or
installers.

Independent source baselines are recorded in
`provenance/upstream-test-baselines.json`. RAPP kernel pins (3/3), RAPP Node
contracts (23/23), RDW (138), UltraCode (40), and the Python 3.12 rapp-map
offline gates passed. This does not erase known upstream failures: rapp-1 is
16/18 because a live twin artifact changed; RAPP-Bible has 12 failures and 5
passes from PII/stale mirrors; rapp-spine is 52/53 due to stale generated
crawl/coverage; and rapp-body still compares current `rapp/1` frames with
legacy `rapp-frame/2.0` expectations.

The independently executed rapp-map source-cache gate remains passing evidence,
not an assimilated-wrapper pass. The assimilated rapp-map and rapp-spine
wrappers are explicitly `blocked-private-boundary`: `--check` verifies that
state and `--run` exits 3. UltraCode's local RDW overlay remains ready. CI pins
Python 3.12 but does not treat privacy-withheld inputs as restored.

Structural hashes cannot authenticate the estate owner or prove registry
freshness. Imported examples may require credentials, network services,
platform SDKs, or obsolete runtimes. Their presence proves preservation, not
operability, endorsement, security review, or release readiness.

The session-only private-boundary evidence is verified but never copied.
Public output retains only approved aggregates: 716 withheld paths across 58
public sources, nine archives, 244,661,926 bytes, and zero scan errors. The
incremental 13-path delta recognizes conventional `.git` suffixes as identifier
delimiters without publishing the deny set. The previous largest cache did not
survive the boundary gate; no public record
binds that withholding to its sensitive path or content.

The observatory builder inspects at most `RAPP_GOD_HISTORY_CAP` file-touching
commits per history-enabled part (default 60). Ref metadata is not imported
history. Raw `main` URLs are hash-verifiable transport conveniences, not
transport-immutable objects.
