# Conformance — `rapp-moment/1.1`

A conforming implementation **MUST** satisfy every clause below. Each maps to a section of
[`SPEC.md`](SPEC.md). These are the rules an outside system agrees to in order to interoperate — to
"play ball by the standard."

## MUST

1. **Birth-proof permanence (§4).** Never alter a genesis frame (a keyframe with **no** `u`).
   `verifyCoordinate(record)` — regenerate the genesis genome from `pk` and assert the `u`-less frames are
   byte-identical — MUST hold at **every** historical revision.
2. **Frozen generator (§4).** The genome generator is frozen; do not change it, even to fix cosmetic
   quirks (e.g. two genesis keyframes rounding to the same `at`). Be robust to those quirks instead.
3. **Signed-body hygiene (§2, §6).** Any field whose name begins with `_` is local metadata and MUST be
   excluded from the signed body. The canonical body is the record with keys sorted, excluding `sig`,
   `pub`, and any `_`-prefixed key.
4. **Ownership (§6).** Ownership is an **ECDSA P-256** signature; `pub.x`'s fingerprint is the owner
   identity (a *zookeeper*). A rappid is a transferable deed resolved over a hash-linked transfer chain.
5. **Append-only harness (§9, §10½).** Every edit/harness operation (grow, checkout, fork, merge) is
   **append-only** and birth-proof-gated. Public history is **never rewritten**.
6. **Read-all, emit-canonical (§6.1).** Read **all** historical/legacy record shapes forever (a `pk`, a
   bare UTC ms, a `|` separator). Emit only canonical. **Never version the string — add record fields.**
7. **Growth gate (§5).** Gate all growth by **weave + reconcile**; never let growth break homeostasis or
   the birth-proof. `STRESS_LIMIT = 12`.
8. **Serverless (§10).** Static data + client-side queries. Introduce **no** backend, database, or account
   system as a condition of participation.
9. **Unknown fields inert (§2, §11⅞).** Render the organism and **ignore record fields you don't recognize**
   (e.g. `embed`); never fail or reject a Moment for carrying a trait you don't know. The schema is open.

## Addressing & identity (MUST)

- The **`pk`** is the eternal join key — globally unique, immutable, self-describing
  (`born = int(pk.split('·')[1])`). Key all per-organism operations on `pk`, never on array index or title.
- Time domain: `sky·<utc_ms>`. Place domain: `<geohash9>·<utc_ms>`.
- The canonical share token is `base64url(JSON.stringify(record))` with padding stripped (see
  [`examples/TOKENS.md`](examples/TOKENS.md)). A conformant player accepts it as `?m=<token>`.

## SHOULD

- Expose the **Gateway** document (§11¾): ERC-721/OpenSea-compatible `name/description/image/animation_url/
  external_url/attributes` plus the RAPP Eternity extensions (`rappid/pk/born/owner/sig_suite/chain/
  dimension`) and an extensible `sources[]`.
- Render the live hologram as an embeddable surface (an `<iframe>` whose `src` is `?m=`/`?dial=`), so the
  Moment is portable card art that loops its 100 frames.
- Honor the **`embed`** trait (§11⅞): render a child Moment (or `"self"`) as an in-world portal, with a
  **finite recursion depth cap**. The whole nesting travels in the token — the record is the link, all the way down.

## How to test

The reference engine [`kody-w/rapp-hologram`](https://github.com/kody-w/rapp-hologram) ships a pure,
dependency-free test suite (`tests/test_*.js`) covering the generator, birth-proof, homeostasis,
fingerprint, ownership, and resolve. Port the vectors to your stack; if your implementation reproduces
them, you interoperate. Conformance is **observable**: a record minted by any conformant client must
verify, resolve, and play in any other.
