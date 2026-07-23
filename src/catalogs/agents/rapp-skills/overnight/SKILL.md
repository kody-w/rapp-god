---
name: overnight
description: Run Kody's improve-to-120 kata as an unattended autonomous loop with a verifiable ledger, commits along the way, and a morning report. USE THIS SKILL when Kody says anything like "run overnight", "work autonomously through the night", "autonomously evolve this for 24 hours", "until you run out of credits", "I'll check you in the morning", "keep improving this", "run the 120 loop", or pastes the improve-to-120 kata text.
---

# overnight — the improve-to-120 loop, unattended

Kody is going to bed. The deliverables when he returns: a ledger he can audit, commits that trace every kept change, and a score that objectively moved. He used to paste this kata by hand every time; invoking this skill IS the paste.

## Setup (before the first pass)

1. Confirm the target: whatever he pointed at (repo, file, app, deck). If ambiguous, the current working directory's project.
2. Create `LEDGER.md` at the target root (or append if it exists) with a session header: date, target, the game definition from the first pass.
3. Repo safety: work on a branch if on the default branch. The push-guard hook handles forbidden remotes; never push to any repo he hasn't named. NEVER touch repos designated off-limits.
4. Start the loop with `/loop` (self-paced). Work continuously — an idle wait is only allowed when blocked on genuinely external state; otherwise the next pass starts immediately.

## The kata (verbatim — this is the contract for every pass)

Improve whatever you've been pointed at. Treat the current state as a 100 — each pass must land at 120 or better, and you must PROVE it with a real check, not a vibe.

FIRST PASS ONLY — establish the game (write these down; they carry across every later pass):
- WHAT am I improving? Name the one thing in front of me in a single line.
- What is BETTER here? Name 2–4 concrete, checkable dimensions that actually matter for THIS thing (correctness, clarity, speed, coverage, robustness, polish — pick what fits, not a generic list).
- What is the SCORE? Take the most objective signal this domain already has — tests passing, a benchmark number, a type-checker/linter, a screenshot, a diff against a reference, a measurable count. If no tool exists, define the cheapest check you CAN repeat every pass. Record it. That's your 100.

EACH PASS:
1. MEASURE first, with the check — record the number. Never self-assess from memory.
2. PICK exactly ONE improvement: the highest-leverage change you can FULLY verify this pass. Prefer the root cause that unblocks the most, not a cosmetic symptom.
3. MAKE THE SMALLEST CHANGE that could move the score. One thing, not ten.
4. RE-MEASURE with the SAME check. Keep the change ONLY if the score objectively went up AND nothing that worked before broke. If it didn't move the number, or it regressed anything — REVERT it. No "probably better."
5. LOG one line: what you changed · before → after · how you verified it.
6. Repeat.

RULES (break one = automatic revert):
- Only claim what you actually verified. If you didn't run the check and watch it improve, you did not improve it.
- Every change is reversible — never clobber or delete work you can't restore; keep the last good state recoverable.
- One variable at a time, so you always know what moved the score.
- Don't game the metric. If a change lifts the number without making the thing genuinely better, revert it and fix the check instead — a blind score is worse than none.

STOP and ask a human (don't force it) when beating the score needs a real decision — a trade-off between two goods, a contradiction between sources, an irreversible or load-bearing change, or a change of direction. Log it and move to the next-highest improvement. Keep climbing until you can't beat the score without a human, or until it's as good as the check can see.

## Ledger and commits (his audit trail — non-negotiable)

- Every kept pass: one ledger line (`pass N · change · score before → after · verification`) AND one git commit whose message is that line. Reverted passes get a ledger line marked REVERTED, no commit.
- Decisions parked for a human go in a `## For Kody` section of the ledger — never force them.

## Morning report

When he checks in (or the loop ends): lead with score at start → score now, passes kept vs reverted, the top 3 improvements in plain language, anything in `## For Kody`, and the path to `LEDGER.md`. All claims must trace to ledger lines.
