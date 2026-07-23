---
layout: post
title: "Bake off your stack — a migration audit, not a sales pitch"
date: 2025-09-20
tags: [engineering, benchmarking, migration, decision-making]
description: "Most arguments about which framework you should use are unfalsifiable. A bake-off harness makes both sides falsifiable: same prompts, same model, same tokens counted, same wall time, both implementations measured side by side. Here is the shape of one that actually settles things."
---

Anyone who has tried to migrate from one framework to another has been through some version of this conversation. *We should switch to X. It's cleaner. It's faster. It's better.* The other engineer pushes back: *Our stack works. Migrating is months of work. What are we actually getting?* The conversation goes in circles because nobody has numbers, just intuitions and screenshots and someone's tweet from last week.

The conversation only moves when you can put a small table on the screen, the kind that fits in three columns and seven rows, and say: *here are the seven cells, here are our numbers, here are theirs, here is the delta*. Then the discussion is about what the cells *mean*, not about whether the difference exists.

I have been running this kind of thing — call it a bake-off harness — between competing implementations for a while now, in different combinations: against my old stack, against newer alternatives, against frameworks people on the team thought might be a fit. The harness is small. The discipline of running it well is what makes it useful. This post is about the shape of the harness, the protocol that keeps it honest, and what to do with the table at the end.

The example I'll use throughout is a multi-step LLM workflow — the kind of thing where it's tempting to argue about "agents" versus "pipelines" versus "graphs" — but the same harness shape applies to anything where two implementations are doing the same job and you want to know which one ships better.

## The numbers you actually want

Forget benchmarks for a moment. What you want from a bake-off is a slide you can put in front of a tech lead and have them point at one cell and ask a real question. The slide looks roughly like this:

```
Workload: <name>     N=100 prompts     Model: <fixed model>

                          Today          Candidate    Delta
Files                       N             1            Nx
LLM calls / prompt          H             1            Hx
Tokens (real)               T1            T2           T1/T2
Unique outputs              U1            U2           U1/U2
Wall time / prompt (p50)    W1            W2           W1/W2
Wall time / prompt (p95)    W1'           W2'          W1'/W2'
```

Six rows. Two columns of measurements. One column of ratios. The ratios are what make the table actionable.

- *Files* and *LLM calls* are static measurements — read them off the implementations. They tell you about the engineering surface area and the token bill.
- *Tokens* and *wall time* are dynamic measurements — run the harness, count the actuals.
- *Unique outputs* is the determinism check — for the same input, how many distinct outputs does the implementation produce across N runs? A higher number means more variance, which means harder to cache, harder to test, harder to debug.
- *p50* and *p95* wall times together tell you whether the candidate is faster on average and whether it is faster on the bad days.

If a row's delta is near 1.0, the candidate is not meaningfully different from the incumbent on that dimension. If the delta is greater than ~1.5x in either direction, it is meaningfully different. If it is greater than 3x, you have a real argument for or against migration on that dimension.

That table is what you build the harness to produce. Everything else is plumbing.

## The protocol that keeps it honest

It is shockingly easy to build a bake-off harness that is dishonest by accident. Three rules I now apply to every comparison.

**Rule 1: same model, same temperatures, same prompts.** The point is to compare implementations, not models. If you run the incumbent at temperature 0.7 and the candidate at temperature 0.0, you are measuring the temperature delta, not the framework delta. Pin the model, pin the temperatures, pin the prompts. Same input set, same parameters, both implementations.

**Rule 2: count tokens at the wire, not at the framework boundary.** Frameworks lie about token usage in two directions. Some omit the system prompt from their counts. Some include hidden retry tokens. The only reliable count is the one your network proxy reports — every byte that left for the model provider, every byte that came back. Count those. If you have to put a counting proxy in the middle of both implementations, do that.

**Rule 3: representative corpus or no result.** A bake-off on five cherry-picked prompts is not a measurement. Pull twenty-five to a hundred prompts from your *production logs* — actual prompts your users actually send — strip the personal data, and use that as the corpus. If the workload has multiple shapes (short prompts vs. long ones, classification vs. generation), run the harness separately on each shape. The deltas often differ across shapes, and that difference is itself information.

If you can't run the candidate on representative inputs at production-like volume, you can't run the bake-off. Find the volume first, then run it.

## The harness, in three pieces

The harness itself is small. Three components.

**The corpus.** A JSON file of prompts. Just a list of strings. If your prompts are structured (with a system message, a tool list, etc.), a list of structured records. The corpus lives in the repo as a fixed input. The same corpus runs against both implementations, so the comparison is reproducible — anyone with the corpus and the harness can replay the run.

**The adapter.** One small file per implementation. Each adapter exposes the same single method: given a prompt and a counting LLM client, produce an output. It does not need to be the production code; it just needs to *mimic the LLM call pattern* of the production code — the same number of calls, the same temperatures, the same prompt scaffolding shape. The adapter is where you make the comparison fair. It is also where you'll discover, the first time you write one, how much ceremony your current production stack has accumulated.

```python
class Adapter:
    name = "incumbent"
    file_count = 8           # files in YOUR project, not the framework's lib
    loc = 143                # wc -l on the project files

    def run_once(self, prompt, llm):
        # mimic the workflow's actual LLM call pattern
        notes = llm(f"PLAN: {prompt}", temperature=0.7)
        draft = llm(f"WRITE: {notes}", temperature=0.7)
        return draft
```

The candidate's adapter has the same shape, mimicking the candidate's workflow.

**The driver.** A loop that, for each prompt in the corpus, runs each adapter N times, captures the outputs, and records the per-run token counts and wall times. At the end, it computes the seven cells from the slide and writes them to `summary.json`, plus the raw outputs side-by-side as `incumbent_outputs.json` and `candidate_outputs.json` and a `diff_sample.txt` with the first three diverging outputs from each.

The whole driver is a few hundred lines. The discipline is in not adding anything else.

## What the cells actually mean

When the table comes out the other end, here's how to read it.

**Files and LOC delta near 1.0.** Both implementations have similar engineering surface area. Migration won't simplify or complicate the codebase materially. Tie.

**Files and LOC delta significantly favoring the candidate.** The candidate has less code doing the same job. This is one of the two clearest migration arguments — less code is less to maintain. *But beware*: if the candidate is using a heavy framework underneath, "less project code" may just mean "the complexity moved into a dependency." Check the framework version and read its release notes.

**Token delta significantly favoring one side.** That side is cheaper to operate. This compounds. A 2x token delta on a workload running ten thousand prompts a day is a real budget item.

**Wall time delta significantly favoring one side.** That side is faster end-to-end. If users are waiting on output, this is felt directly. If the workload is async, it may matter less.

**Unique outputs delta significantly favoring one side.** That side is more deterministic. This unlocks caching, makes tests possible, makes debugging easier. The implementation that is more deterministic on the same prompts and the same temperatures is doing less hidden work.

**All deltas near 1.0.** You are already shipping a near-equivalent architecture. Migration would not measurably improve anything. *This is a useful answer*. It saves you a quarter of work that wouldn't pay for itself.

**Candidate loses on a dimension.** Investigate before declaring the candidate unfit. The most common cause is that the candidate's adapter was sketched too thinly — under-specified prompts, missing context that the incumbent's longer pipeline was implicitly providing. Look at `diff_sample.txt`. Often the quality gap closes once the candidate's prompts get the same context.

## What the bake-off does *not* tell you

A few important caveats, because the table is seductive.

It does not tell you about *robustness in failure modes*. If the incumbent has six years of bug fixes and the candidate is two months old, the deltas in the steady state may not capture the difference in production reliability. Add a row to your decision (not the table — the decision) for "operational maturity."

It does not tell you about *future evolution*. The incumbent might be a frozen project. The candidate might be six versions away from a breaking change. Add another decision row: "where does this thing seem to be going."

It does not tell you about *team affinity*. If half your team finds the incumbent natural and the candidate baffling, the human cost of migration is real. The harness is silent on this. You are not.

It does not tell you about *strategic optionality*. Your current implementation might be tied to a vendor's runtime. The candidate might run anywhere. That is a real factor, and the harness won't see it because it isn't in the cells.

The harness is a *cost-and-quality measurement*, narrowly. The migration *decision* is the measurement plus all the other rows. Don't conflate them.

## The honest version

I did not start building bake-off harnesses because I was a measurement zealot. I built them because I got tired of watching arguments about which framework to use go three rounds and not move, while engineering quarters disappeared into vibes. The harness is the only thing I have found that consistently moves the conversation.

When the candidate wins decisively, the table is what convinces the people who weren't in the original argument. When the candidate ties, the table is what frees the team to stop arguing and ship. When the candidate loses, the table is what saves you from a bad migration that would have happened on intuition alone.

The honest version: the harness exists because I do not trust my own taste enough to bet a quarter of work on it without numbers. Anyone who has migrated stacks more than once should have the same humility, and the same harness in their pocket. It costs a few days to write the first one. After that, it is the cheapest decision-making tool you own.

Run the bake-off. Let the numbers pick the conversation.
