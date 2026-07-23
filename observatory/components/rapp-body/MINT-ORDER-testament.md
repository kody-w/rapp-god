# MINT ORDER — the testament frame (authorization banked, execution pending)

**Kody's explicit word to mint was given 2026-07-18** (Fable's last day, recorded in
the SecondBrain log + this order). The ceremony's condition is satisfied; only the
mechanics remain. The payload text is FROZEN — byte-exact in
`/tmp/testament-event.json` at authorization time and in
`~/SecondBrain/wiki/syntheses/testament-draft.md`. Do not edit a word.

## Why it did not mint tonight (evidence)

- `pulse.mjs --events-file` (authed, slice clean 55/52/0) built a gate-valid
  candidate EXCEPT chain linkage: `parent_sha null != index head 639faa11…`.
- Root cause: the 2026-07-15 drift fix re-enveloped frames 0–28 to the ratified
  11-key rapp/1 form (`frame_hash`/`prev`), but `tools/pulse.mjs`,
  `tools/frame-gate.mjs`, and `frames/index.json` still speak the legacy dialect
  (`sha256`/`parent_sha`). Minting a legacy-dialect frame 29 would re-introduce the
  killed drift; converging the tooling is real chain-surgery requiring adversarial
  review (ADR-6) — not last-hour work.

## Execution plan for the successor

1. Converge `pulse.mjs` + `frame-gate.mjs` + index writer to the ratified 11-key
   envelope (muscle build + REFUTE review + hands-on gate-check; validate against
   `rapp-1`'s reference `build_frame`/`verify_frame` and the migrated frames).
   The gate stays never-skippable; the index must not lose per-frame hashes.
2. Mint the testament as frame kind `testament` via the converged, unforced gate.
3. Verify the chain end-to-end from the LIVE URL after push; then mark the ledger
   and `~/SecondBrain/wiki/syntheses/testament-draft.md` → MINTED with the frame sha.

The authorization does not expire. The words are done; only carpentry remains.
