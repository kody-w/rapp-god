# rapp-eternity — retired historical repository

> **Status: RETIRED · HISTORICAL · NON-NORMATIVE**

This repository no longer defines identity, ownership, migration, or trust rules for
RAPP. The former `rapp-eternity/1.0` text was an earlier design and is subordinated
to RAPP. Do not implement it, cite it as current, or treat it as a compatibility
authority.

## Governance and technical authority

### Federal subordination

Under RAPP rev-5 §11 (Federal Constitution Art. VII), this repository explicitly
declares federal subordination to [`kody-w/RAPP`](https://github.com/kody-w/RAPP).
That is a governance relationship only. It does not make this repository a
Router/Mirror, pin technical specification bytes, or establish §13 trust.

### Exact technical protocol pin

Separately, the immutable technical authority used for this retirement is:

- repository: [`kody-w/rapp-1`](https://github.com/kody-w/rapp-1)
- commit: [`6723c7add2aed36bb68992fc71a56b0a4bd5ad81`](https://github.com/kody-w/rapp-1/tree/6723c7add2aed36bb68992fc71a56b0a4bd5ad81)
- normative file: [`SPEC.md`](https://github.com/kody-w/rapp-1/blob/6723c7add2aed36bb68992fc71a56b0a4bd5ad81/SPEC.md)
- `SPEC.md` SHA-256: `6d06daba65d7c045716f3d6e95db8401ab58e727820e4114466d847f62cae49b`
- authority status at that commit: **“Draft standard for ratification (Kody,
  estate owner). rev-5.”**

The protocol is named **RAPP**; `rapp/1` is its wire/spec token. This retired
repository does not ratify RAPP, mirror its specification, or create a second
source of truth. Follow the pinned authority, including its §6 identity grammar
and minting, §10 signatures, §12 total-migration rule, and §13 signed registry.

## Trust acceptance: `NOT_ESTABLISHED`

This repository contains no authenticated §13 evidence: no out-of-band
`estate_owner` anchor and matching SPKI proof; no signed registry document or
verified `registry_seq`/rollback floor; no time-scoped owner-succession chain;
and no canonical-source or provenance-stamped freshness/staleness evidence.

Registry and trust acceptance are therefore **`NOT_ESTABLISHED`** and
**owner-blocked**. Federal subordination and the exact technical pin above are
not substitutes for those missing inputs. This retirement creates no owner key,
registry entry, signature, succession record, tombstone, or re-anchor.

## Why it was retired

The historical documents taught content-derived identity, permanently key-optional
ownership, and “read every legacy form forever.” RAPP rev-5 instead specifies one
case-sensitive rappid grammar, domain-separated `Hb("rapp/1:rappid", …)` minting,
no perpetual backward compatibility, and registry-rooted trust. Those models are
not interchangeable; the pinned RAPP authority supersedes the former rules.
[`SPEC.md`](SPEC.md) records the disposition without restating a competing
standard.

## Historical record

The original two-file snapshot remains available only through Git history at
[`868e80c33bbe1c03597372e3b9db54aa5b736a95`](https://github.com/kody-w/rapp-eternity/tree/868e80c33bbe1c03597372e3b9db54aa5b736a95).
No working-tree archive or legacy implementation is retained.
