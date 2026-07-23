# Provenance

These generated ledgers make every public census decision and imported tree
entry reviewable offline. `files.jsonl` includes exact Git modes, blob IDs,
sizes, SHA-256 hashes, semantic destinations, and dispositions. A null
destination is permitted only for an explicitly unfetched gitlink.

The sensitive independent archive audit remains session-only and is not copied.
`archive-audit-proof.json` retains approved aggregate evidence and binds the
public-safe retained containers/members after opaque withholding. Nested
members are never extracted or executed. `upstream-test-baselines.json` records
both passing source baselines and known upstream failures; it is intentionally
not an all-green claim.

`native-files.jsonl` closes the fixed 284-file native baseline (278 preserved,
six evolved at the pass-one closure snapshot). `commit-objects.jsonl` retains
complete public commit object bytes where publication remains safe; 58 records
are opaque withheld ordinals. Retained OIDs and advertised trees can be
recomputed offline. `selected-repositories.txt` is digest-bound by
`census-proof.json`.

The raw ref evidence remains session-only after boundary review;
`releases.source.jsonl` preserves the safe release API evidence. `refs.jsonl`
gives retained refs namespaced metadata keys and uses opaque ordinals for
withheld records, without creating a Git ref or branch. `releases.jsonl` and
`release-assets.jsonl` retain complete supplied release metadata, download
URLs, SHA-256 digests, and sizes. Every asset is
`external-release-asset`; none is downloaded or stored as a Git blob.
GitHub-reported digests are explicitly distinguished from independent download
verification, while matches to already imported blobs are indexed.

The ref/release evidence is a non-atomic multi-repository collection window
from `2026-07-23T05:11:01Z` through `05:11:11Z`, not a generation timestamp or
atomic owner snapshot. Default-tree pins use their separate per-repository
times in `source-captures.jsonl` and may predate later ref observations.

Private source capture is represented only by the safe aggregate count in
`private-summary.json`. Existing public observatory history may contain public
textual references to private identifiers; `privacy-status.json` records that
unresolved owner remediation without claiming history is clean or rewriting it.
