# RAPPID_SPEC — Identity (Eternity format)

> **Frozen excerpt** of the canonical rappid contract (`rapp-rappid/2.0`). Bundled at planting time on 2026-05-09T12:46:35Z. Updated to the consolidated Eternity string (Constitution Art. XXXIV.1, locked 2026-06-03).

## Format

```
rappid:@<owner>/<slug>:<hex>
```

The single, never-re-versioned form: one string that is both identity and self-locating. No `v2:`/`v3:` prefix, no inline `<kind>:` segment, no `@github.com/...` suffix. `kind` now lives in the record (a field), not the string.

Example (this neighborhood's):

```
rappid:@kody-w/braintrust-template:<hex>
```

(See the record fields below for `kind` and the actual value.)

## Components

| Part | Rule |
|---|---|
| Prefix `rappid:` | Literal. Tells parsers this is a rappid. |
| `@<owner>/<slug>` | The canonical location. `github.com/<owner>/<slug>` is the door; every door URL derives from it by string parsing (no lookup). The `@` prefix is literal and required. |
| `<hex>` | The identity hash, lowercase hex. Existing 32-hex hashes are grandfathered; 64-hex (SHA-256) for newly minted identities. Minted ONCE at planting; the hash is the join key (match on the hash, never the slug). |

## Legacy forms (read forever, canonicalized on read)

Every prior form is still readable and is canonicalized to the form above, preserving the hash:

- v1 — a bare UUID (not self-locating; supply owner/slug to canonicalize).
- v2 — `rappid:v2:<kind>:@<owner>/<repo>:<32hex>@github.com/<owner>/<repo>`.

Only the consolidated form is ever emitted. Use `tools/door_address.py::canonicalize_rappid` — never hand-write the transform.

## Invariants (Constitution Art. XXXIV.5)

1. **Permanence.** Once minted, a rappid is permanent for the lifetime of the neighborhood. Re-grafting, re-planting, kernel upgrades — none of these mint a new rappid.
2. **Bond preservation.** The bond technique (egg → overlay → hatch back) preserves the rappid through every kernel upgrade.
3. **Lineage chain.** A neighborhood's `parent_rappid` chains back to its ancestor (the species root for many: `rappid:@rapp/origin:0b635450c04249fbb4b1bdb571044dec`).
4. **No two organisms share a rappid.** Mint via `uuid.uuid4().hex` — collision probability is negligible.
5. **The rappid is the seed source for the neighborhood's holocard.** `derive_seed(rappid_str)` via BLAKE2b-64 produces a deterministic 64-bit ID. Same rappid → same seed → same incantation, forever.

## Required fields in `../rappid.json` (`rapp-rappid/2.0`)

| Field | Required | Notes |
|---|---|---|
| `schema`       | yes | `rapp-rappid/2.0` |
| `rappid`       | yes | The full Eternity string (`rappid:@<owner>/<slug>:<hex>`) |
| `kind`         | yes | The kind, carried in the record (no longer in the string) |
| `name`         | yes | Slug — matches the repo name |
| `display_name` | yes | Human-readable |
| `github`       | yes | `https://github.com/<owner>/<repo>` |
| `parent_rappid`| yes (may be null for species roots) | The lineage anchor |
| `parent_repo`  | yes | Where the parent's rappid lives |
| `planted_by`   | yes | GitHub handle of the operator who planted |
| `planted_at`   | yes | ISO-8601 UTC |
| `kernel_version` | yes | The kernel version at planting time |

## Don't

- Don't change the rappid after minting — that's identity destruction. Use a new rappid for a new neighborhood instead.
- Don't synthesize rappids by hand — always mint via UUID4.
- Don't include personal data in the rappid — it travels publicly.
- Don't reuse a rappid string across neighborhoods (uniqueness is critical for seed derivation).

---

*Frozen excerpt. For full identity / lineage / bonding rules, see `CONSTITUTION.md` Art. XXXIV.5 in the parent repo if reachable.*
