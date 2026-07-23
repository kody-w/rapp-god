---
name: muscle
description: "Run the CSM delegation loop: hand grunt/bulk work (building, drafting, coding, doc generation, deep debugging) to GitHub Copilot CLI GPT-5.6 Sol as a background muscle job, then gate-check the FULL result hands-on with real inputs, fix via --resume rounds until it stands, and add the Fable-only layer last. USE THIS SKILL when Kody says: 'delegate to sol', 'muscle this', 'have sol/copilot build it', 'spawn the muscle', 'send it to the muscle', 'copilot the grunt work', 'ration fable', or whenever a task is bulk artifact generation (code, tests, docs, ports, sweeps) that does not need Fable-level judgment to produce — the output is an artifact, not a decision. Also use when a hands-on verification loop exceeds ~2 probes on the same failure (deep debugging is muscle work)."
---

# muscle — the CSM delegation loop, as one verb

Canon: memory [[csm-doctrine]] + [[fable-copilot-loop-lessons]] (read them if judgment
calls arise). This skill is the runnable mechanics. Audit evidence (2026-07-16): the
loop was performed BY HAND 129 times across 8 of the last 50 sessions, with 39
`--resume` correction calls — this skill replaces that ritual.

Division of labor (decision rule): output is a **decision** -> Fable inline. Output is
an **artifact** -> muscle. Output is a **handoff** -> spine (you, orchestrating).

## 1. Write the order (never prompt ad hoc)

Write the order to a file in the target workdir (`ORDER-<slug>.md`), then point the
muscle at it. Brief anatomy that field-tested well:

1. **Intent** — one paragraph, what and why.
2. **Inputs to study** — exact paths.
3. **Rules / do-not-touch** — includes file-ownership lines when jobs run in parallel:
   "only create the files named below; a concurrent job may be writing X — leave it."
4. **Numbered acceptance checks** — runnable commands, verbatim-output requirement.
5. **Done-when + report format** — require it to RUN its own verification, end with a
   report, and include a "flags / surprises" section ("flag uncertainty, don't paper
   over") — that section yields real gold.

## 2. Spawn the muscle (background, parallel-safe)

```bash
cd <workdir> && copilot -p "Read ORDER-<slug>.md in the current directory and execute it completely. You are the muscle in a cortex/muscle pattern: do the full grunt build, run your own verification per the Done-when section, and end with the report." \
  --model gpt-5.6-sol --allow-all-tools --log-level none 2>&1 | tail -40
```

- Big orders: `run_in_background: true` on the Bash call; several jobs in parallel are
  fine **only** with file-ownership lines in each brief.
- **Never poll with foreground `sleep`** (audit: 419 sleep-then-check calls wasted
  hours of wall clock). Background the job and use the Monitor tool / background-task
  notification; check output with `tail` only when woken.
- The output ends with `Resume: copilot --resume=<session-id>` — **capture that id**;
  it is the correction channel.
- Sanity ping if the CLI has not been used this session:
  `copilot -p "reply with exactly: MUSCLE-ONLINE" --model gpt-5.6-sol --allow-all-tools --log-level none 2>&1 | tail -3`

## 3. Gate-check: touch the FULL E2E yourself (never skip, strictly ordered)

The muscle's green suites lie — every defect that ever mattered was invisible to its
own tests and caught only by hands on REAL artifacts. Sequence (Kody-mandated):

a. **Touch the full end-to-end** — wait until the muscle is completely done, then
   exercise the entire finished artifact yourself: run it, render it, curl it, drive
   the whole flow. Re-run the acceptance commands verbatim PLUS **one probe against a
   real file / live system the brief never mentioned** (the live-system probe is the
   highest-yield test). Never trust the muscle's report.
b. **Criticize the whole** — one written adversarial critique of the complete shape:
   gaps, wrong turns, integration seams, taste failures.
c. Grunt-level defects go back via:
   ```bash
   copilot --resume=<session-id> -p "<repro command + observed error + root cause + exact fix + acceptance check>"
   ```
   Corrections written that way converge in one shot. Repeat a->b until it stands.
d. **THEN the Fable-only layer, last** — naming, architecture judgment, taste,
   partner-facing prose (Fable writes every customer/partner-facing word). Never
   interleave touches with review.

## 4. Guards

- **The slip:** verification is a bounded final touch, not an iterative debug loop.
  More than ~2 hands-on probes on the same failure -> STOP, package the loop as a
  `--resume` order with the evidence gathered so far.
- Report to Kody as **one unified result with evidence** — what was delegated, what
  the gate-check observed, what was fixed, what Fable added.
