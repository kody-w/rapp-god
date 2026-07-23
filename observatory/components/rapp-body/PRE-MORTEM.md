# Genesis pre-mortem — ways the birth goes wrong, written before it happens

> Cortex judgment doc, 2026-07-14. Assume it is six months after genesis and we regret
> publishing `kody-w/rapp-body`. What happened? Each scenario gets: how it plays out,
> what already guards it, and what must be checked in the final pre-publish pass.
> The stance underneath all of them: **genesis is irreversible in spirit.** The repo
> could technically be deleted, but a public, timestamped birth that later vanishes is
> worse than one that was never published. So every gate below is a hard gate.

## 1. The seal was wrong

The lexicon sealed with a defect; amendments pile up in week one; the "sealed language"
story looks foolish exactly where it claimed rigor.

- **Guarded by:** two full adversarial review rounds (22 findings adjudicated, then 6
  residuals re-verified); the amendment protocol (`{previous_sha, new_sha}` chain) means
  even a needed fix is an orderly append, not an embarrassment.
- **Final check:** Kody reads the lexicon himself before GO. The seal is his word, not
  a model's confidence.

## 2. A privacy leak in a frame — the un-deletable kind

A private name, a customer identifier, or pattern-of-life detail lands in a public
frame. The chain is append-only and content-addressed: quiet removal breaks the chain;
the leak is permanent or the biography is broken. This is the single worst outcome.

- **Guarded by:** public-by-construction rule (the body's DOG rule) in every frame
  emitter; the `private-name-leak` golden case in rapp-map/conformance.
- **Final check:** grep-sweep ALL frames (24 today) for private identifiers and
  customer names immediately before publish; document the redaction protocol in advance:
  a supersession frame and a publicly documented break — never a silent rewrite.

## 3. The identity is later found unlawful

Someone shows a rappid in the chain was minted as `sha256(owner/slug)` — the biography
of the whole ecosystem carrying an identity that can lie.

- **Guarded by:** the body's rappid was minted lawfully (parent = RAPP's real rappid);
  the `rappid-invariant-violation` golden case now exists precisely to catch this class.
- **Final check:** run verify-chain + re-derive the body's rappid one last time
  pre-publish.

## 4. The pulse dies or babbles

Either the daily cron mints near-identical junk frames (the no-churn rule fails open)
and the biography becomes noise, or it fails silently forever (fails closed) and the
"living biography" is a corpse by August — the false-green failure all over again.

- **Guarded by:** the no-churn rule; verify-chain before AND after minting in pulse.yml;
  the weekly `--heartbeat` as an explicit liveness signal; observation gaps recorded as
  events, never as thinner data.
- **Final check:** watch the first two weeks: expect *some* no-change days (proves
  no-churn) and *at least one* heartbeat frame (proves liveness). Put the monthly vitals
  review on the calendar before genesis, not after.

## 5. A reconstructed frame is publicly challenged

Someone demonstrates a prenatal frame misstates history.

- **Guarded by:** every reconstructed frame carries `provenance: {mode:"reconstructed",
  evidence:[…]}` and never claims witness; the challenge lands on the evidence, not on
  the body's honesty.
- **Response, pre-agreed:** a correction frame citing the challenge. The biography's
  integrity is the *protocol for being wrong*, not the absence of error.

## 6. Gate sequencing violated under time pressure

The model week ends; the temptation is to publish with drift unexplained or the seal
unread. That inverts the whole point — the artifact exists to outlast the model, so the
model's deadline must not bend the artifact's gates.

- **The gates, restated hard:** (1) zero *unexplained* drift on a scoped re-verify of
  the R3-fixed surfaces (waivers ledgered for the explained rest), (2) lexicon sealed —
  read and GO'd by Kody in his own words, (3) chain verified and player driven E2E by
  the publishing session's own hands, same day as publish.
- If access to the strong model lapses first: **nothing is lost.** The darkroom keeps;
  a later session publishes by following ORDER-BIRTH.md + this file + the conformance
  suite. Slow genesis beats wrong genesis.

## What would falsify "healthy" after birth

Any of: verify-chain exits non-zero · a frame minted with no material change · an
observation gap silently absorbed instead of recorded · a private identifier in any
public frame · vitals.json older than 8 days with no heartbeat explanation.
