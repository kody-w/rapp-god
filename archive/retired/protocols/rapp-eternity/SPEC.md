# rapp-eternity/1.0 — retired historical specification

> **Disposition: RETIRED · SUBORDINATE TO RAPP · NON-NORMATIVE**

This file is a tombstone, not a specification or a compatibility profile. The
former `rapp-eternity/1.0` rules are withdrawn from the active RAPP surface.
Normative words in the historical version have no present authority.

## 1. Federal subordination and technical authority

### 1.1 Federal subordination

Under RAPP rev-5 §11 (Federal Constitution Art. VII), this historical repository
declares federal subordination to
[`kody-w/RAPP`](https://github.com/kody-w/RAPP). This declaration is a
governance relationship. It does not make this repository a Router/Mirror,
technical specification authority, registry, or trust anchor.

### 1.2 Exact technical authority and status

Separately, the sole pinned technical authority for this retirement is
[`kody-w/rapp-1@6723c7add2aed36bb68992fc71a56b0a4bd5ad81`](https://github.com/kody-w/rapp-1/tree/6723c7add2aed36bb68992fc71a56b0a4bd5ad81).
Its normative file is
[`SPEC.md`](https://github.com/kody-w/rapp-1/blob/6723c7add2aed36bb68992fc71a56b0a4bd5ad81/SPEC.md),
whose SHA-256 is
`6d06daba65d7c045716f3d6e95db8401ab58e727820e4114466d847f62cae49b`.

The authority file labels itself **“Draft standard for ratification (Kody,
estate owner). rev-5.”** The authority repository's README reports **RAPP
rev-5** and its conformance results. This tombstone makes no stronger status
claim: it neither declares ratification nor changes the authority.

The protocol name is **RAPP**. `rapp/1` is the wire/spec token. The repository
name `rapp-1` and the informal label “RAPP1” do not establish another protocol
or another authority.

## 2. §13 trust acceptance: `NOT_ESTABLISHED`

No authenticated §13 evidence is present in this repository or supplied by this
retirement:

- no out-of-band `estate_owner` rappid anchor or SPKI whose
  `Hb("rapp/1:rappid", SPKI_DER)` tail has been verified against that anchor;
- no authenticated registry bytes, detached owner signature, or verified
  `registry_seq` with a persisted no-rollback high-water mark;
- no §13.2 time-scoped owner-succession evidence or authenticated §13.3
  re-anchor chain; and
- no canonical-source or provenance-stamped registry retrieval, freshness
  observation, staleness policy, or latest-sequence evidence.

Accordingly, §13 registry/trust acceptance is **`NOT_ESTABLISHED`** and
**owner-blocked**. Nothing in this repository is an accepted registry, anchor,
owner designation, succession record, freshness proof, or authorization.
Federal subordination (§1.1), a technical spec hash (§1.2), and a historical
tombstone are not substitutes for authenticated trust inputs.

## 3. Disposition of the former rules

| Former `rapp-eternity/1.0` rule | Disposition under the pinned RAPP authority |
|---|---|
| Identity tail was the SHA-256 of a selected canonical content body. | Retired. RAPP §5 domain-separates addresses, and §6.2 mints the identity tail exactly once with `Hb("rapp/1:rappid", …)`. |
| A key could never be required; GitHub collaboration plus file possession was the permanent ownership default. | Retired. RAPP permits both keyless and keyed minting, but authorship and operations that require signatures follow §10, while key discovery, revocation, succession, and ownership resolve through §13. |
| Every legacy form remained valid forever and readers matched on a content hash without migrating stored identity. | Retired. RAPP §6.3 defines canonicalization-on-read and provisional identifiers; §12 requires total migration and deletion of old live forms rather than perpetual backward compatibility. |
| `rapp-eternity/1.0` was the estate-wide identity authority. | Withdrawn. This repository is historical, federally subordinate to `kody-w/RAPP`, and technically subordinate to the pinned `kody-w/rapp-1` authority. |

## 4. Exact identity pointer

Implementations must use
[RAPP §6](https://github.com/kody-w/rapp-1/blob/6723c7add2aed36bb68992fc71a56b0a4bd5ad81/SPEC.md#6-identity--the-rappid-l2)
directly. For audit orientation only, its case-sensitive ABNF is:

```abnf
rappid    = %s"rappid:@" owner "/" slug ":" hash
owner     = lclabel
slug      = lclabel
lclabel   = lcalnum *( ["-"] lcalnum )
lcalnum   = LCALPHA / DIGIT
LCALPHA   = %x61-7A
hash      = 64HEXDIGLC
HEXDIGLC  = DIGIT / %x61-66
```

The normative bounds and semantics remain in the authority: `owner` is the
lowercase GitHub login and is 1–39 characters; `slug` is 1–100 characters;
labels have no leading, trailing, or adjacent hyphen; the tail is exactly 64
lowercase hexadecimal characters. The self-locating form is the only conformant
form. This quotation is deliberately non-normative; on any discrepancy, the
pinned authority governs.

## 5. Exact minting pointer

RAPP §5 defines:

```text
Hb(space, b) = lowercase_hex(SHA-256(utf8(space) || 0x0A || b))
```

RAPP §6.2 then defines the two mint-once inputs:

- keyless: `Hb("rapp/1:rappid", uuid4_octets)`, using the 16 binary UUIDv4
  octets in RFC 9562 field/byte order;
- keyed: `Hb("rapp/1:rappid", SPKI_DER)`, using the master key's DER
  `SubjectPublicKeyInfo`.

Owner/slug or other names are not minting inputs. Existing stored tails are
reused on read. The only re-mint mechanism is the tightly enumerated,
owner-authorized re-anchor in RAPP §6.3 and §13.3.

This repository mints nothing. It supplies no owner key, SPKI, estate-owner
rappid, registry entry, tombstone, signature, or re-anchor record. None may be
inferred from this retirement commit.

## 6. Migration and trust pointers

- [RAPP §10](https://github.com/kody-w/rapp-1/blob/6723c7add2aed36bb68992fc71a56b0a4bd5ad81/SPEC.md#10-trust-and-signatures-l2)
  governs detached, unencoded JWS signatures, registry-based SPKI discovery,
  key rotation, and tombstones. Keyless rappids assert location, not authorship.
- [RAPP §12](https://github.com/kody-w/rapp-1/blob/6723c7add2aed36bb68992fc71a56b0a4bd5ad81/SPEC.md#12-versioning-evolution-no-legacy)
  requires a canonical-form change to land as a total migration of every
  instance plus deletion of the old live form; sealed re-genesis history is its
  stated exception.
- [RAPP §13](https://github.com/kody-w/rapp-1/blob/6723c7add2aed36bb68992fc71a56b0a4bd5ad81/SPEC.md#13-the-registry--the-estates-signed-root-of-trust-append-only)
  defines the signed, append-only registry root of trust, its bootstrap anchor,
  rollback protection, owner succession, and exact entry types.

The working tree now contains no active `rapp-eternity/1.0` standard and no
archive copy. Because this repository has no identities, frames, eggs, keys,
registry, or executable producer/consumer, there is no local operational object
to migrate or re-anchor. Any estate-wide owner-authorized action remains the
authority owner's work and is not fabricated here.

## 7. Historical preservation

The superseded README and 288-line specification remain available through Git
history at
[`kody-w/rapp-eternity@868e80c33bbe1c03597372e3b9db54aa5b736a95`](https://github.com/kody-w/rapp-eternity/tree/868e80c33bbe1c03597372e3b9db54aa5b736a95).
They are historical evidence only. Consumers and implementers should not vendor,
mirror, or revive them as a live standard.
