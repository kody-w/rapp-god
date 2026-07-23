# RAPP estate publication status — CANDIDATE QUARANTINE (NOT YET LIVE)

This branch proposes a deterministic, read-only status surface for
`kody-w/rapp-estate`. It is **not yet the live publication** and does not prove
that GitHub `main` or Pages has changed.

## Candidate deployment status

The **quarantine takes effect only when** a reviewed commit containing these
bytes reaches `main` and byte-matching responses are verified from both raw
GitHub and GitHub Pages. At this candidate's audit time, remote `main` and live
Pages still served baseline
`24c8fdc1e770c790b98724002d719d515d5e5465`.

`live_deployment_verified` is therefore `false`; the verified commit and UTC
are `null`. The Parent/release coordinator will push and verify before closing
the review. Until that verification completes, consumers must treat the live
site as the unremediated baseline, not as quarantined.

## Exact authority

| Field | Value |
|---|---|
| Repository | `kody-w/rapp-1` |
| Commit | `6723c7add2aed36bb68992fc71a56b0a4bd5ad81` |
| Path | `SPEC.md` |
| Status in document | Draft standard for ratification (rev-5) |
| Bytes | `41880` |
| SHA-256 | `6d06daba65d7c045716f3d6e95db8401ab58e727820e4114466d847f62cae49b` |

Immutable authority:
<https://raw.githubusercontent.com/kody-w/rapp-1/6723c7add2aed36bb68992fc71a56b0a4bd5ad81/SPEC.md>.
The same pin is machine-readable in
[`RAPP1_AUTHORITY.json`](RAPP1_AUTHORITY.json).

## Audit basis

- Baseline:
  `24c8fdc1e770c790b98724002d719d515d5e5465`
- Baseline surface: exactly five tracked files; no archives.
- At audit time, every baseline byte matched both local git and the live
  `main` raw publication. All five paths were also served by GitHub Pages.
- The two baseline JSON surfaces emitted **18 provisional occurrences**:
  `estate.json` emitted 17 (one `owner.rappid` plus 16
  `created[].rappid`), and the network beacon emitted one
  `operator_rappid`.
- The beacon value duplicated the estate owner value, so those 18 occurrences
  represented **17 distinct baseline identifier values/lookups**. The estate
  contained no membership entries.
- Of those 17 lookup records, 16 resolved publicly across 15 distinct public
  repository paths; one did not resolve publicly. All resolved source records exposed
  syntactically current 64-hex candidates and migration assertions.
- No owner-signed re-anchor record, out-of-band estate-owner anchor, or
  authenticated, monotonic, freshness-checked section 13 registry was found.
  Syntax and GitHub authorship are not substitutes for that evidence.
- [`RAPP1_EVIDENCE.json`](RAPP1_EVIDENCE.json) records every lookup as a
  public-safe, non-authoritative point-in-time observation. Moving refs were
  discovery-only; the manifest cannot promote trust.

## Findings and fixes

1. **Identity:** the baseline surfaces emitted 18 provisional occurrences
   representing 17 distinct lookups. This candidate removes them rather than
   converting or re-minting them. Current candidates in other repositories
   were not copied because their required authorization evidence is absent.
2. **Labels and authority:** the estate, beacon, and metropolis labels were
   defined outside the pinned authority and were presented as canonical. This
   candidate does not emit them as protocol schemas or specifications.
3. **Frames, wire, and registry:** the retired metropolis prose described a
   different frame shape and extra substrate behavior, while also denying the
   registry that RAPP/1 section 13 requires. The candidate path makes no such
   claim; the live baseline remains unchanged pending deployment.
4. **Map semantics:** created inventory was presented as ownership and
   reachability. The candidate surface exposes only aggregate historical
   counts and empty current claim sets.
5. **Moving links:** moving authority links, moving identity paths, an
   unresolved non-public target, and a missing well-known path are removed from
   candidate trust-bearing output. The authority link is commit-pinned and
   hash-pinned.
6. **Rendering safety:** client-side fetch, HTML injection sinks, generated
   links, and inline event handlers are removed by the candidate. Its
   `index.html` is static and carries no script or external asset.
7. **Public data:** personal display text and non-public repository locators
   are removed from candidate bytes. Historical bytes remain available through
   git history only.

## Candidate surfaces

| Path | Candidate role |
|---|---|
| `index.html` | Static human-readable quarantine status |
| `estate.json` | Fail-closed machine-readable publication status |
| `.well-known/rapp-network.json` | Fail-closed discovery status; not a beacon |
| `METROPOLIS.md` | Candidate retirement notice; not a specification |
| `RAPP1_AUTHORITY.json` | Exact structural authority pin |
| `RAPP1_EVIDENCE.json` | Non-authoritative, commit-pinned lookup observations |
| `RAPP1_OWNER_ACTIONS.json` | Owner-only blocker with null inputs |
| `RAPP1_STATUS.md` | Candidate status and live deployment checklist |
| `tests/test_publication.py` | Offline invariants and optional pinned-source verification |
| `.nojekyll` | GitHub Pages literal-file control |

No candidate identity, membership, frame, wire, or registry claim is accepted.
This statement becomes the live publication posture only after the deployment
condition above is verified.

## Role and subordination

The normative authority above is technical and commit-pinned. Under RAPP/1
section 11, any Router/Mirror is subordinate to `kody-w/RAPP`. This repository
does not route. If its static status is treated as a mirror, that mirror is
subordinate and must serve provenance-stamped, hash-matching bytes only.

## Remaining owner action

The owner-only decision and evidence fields remain `null` in
[`RAPP1_OWNER_ACTIONS.json`](RAPP1_OWNER_ACTIONS.json). Until they are supplied
and independently verified, consumers must refuse this repository as a live
estate, beacon, registry, or identity source.

## Live deployment verification checklist

The Parent/release coordinator must complete and record every item before
closing:

- [ ] Review the candidate commit, complete diff, file ledger, and public-safe
  handoff.
- [ ] Run `python3 tests/test_publication.py --online` and retain the passing
  result.
- [ ] Run the RAPP floor from the exact pinned authority checkout and retain
  the `CLEAN` result.
- [ ] Push or merge the reviewed candidate commit to `main` without rewriting
  it.
- [ ] Resolve remote `main` to a full 40-hex commit and confirm it contains the
  reviewed candidate.
- [ ] Fetch every tracked raw path at that resolved commit and verify its byte
  count and SHA-256 against the git tree.
- [ ] Poll GitHub Pages until the index, both machine status surfaces, authority
  pin, evidence, owner actions, status, and retirement notice all return HTTP
  200 with the reviewed bytes.
- [ ] Confirm the live index is script-free and both live machine surfaces
  remain fail-closed with empty/null claims.
- [ ] Re-fetch the immutable authority and verify `41880` bytes and SHA-256
  `6d06daba65d7c045716f3d6e95db8401ab58e727820e4114466d847f62cae49b`.
- [ ] Record the deployed commit, verification UTC, raw/Page hashes, and final
  result in the parent handoff before closing.

This status is dated `2026-07-17`. A moving branch is not provenance:
consumers must resolve and pin the serving commit before citing these bytes.
