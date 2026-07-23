---
layout: post
title: "Honest framework comparison — the bake-off pattern for putting numbers behind your claims"
date: 2025-10-17
tags: [engineering, benchmarking, framework-comparison, software-evaluation, ai-frameworks]
description: "Frameworks compete on adjectives. Smarter, faster, simpler, better. The numbers are almost never published alongside the adjectives. The bake-off pattern is a reproducible way to put numbers on framework comparisons so the conversation stops being a vibe contest."
---

Every six months, in any active corner of software engineering, a new framework announces it has solved what we thought we solved. The claim lands as a tweet, a conference talk, or a launch post. "Smarter orchestration." "Better memory." "Fewer hallucinations." "Production-ready." The numbers behind those adjectives are almost never published alongside the adjectives.

The standard response from competing frameworks is more adjectives. *Our* orchestration is also smart. *Our* memory is also good. The discourse becomes a vibe contest, and whoever can write the most confident marketing copy wins until the next launch. Nothing converges. Nothing settles. The field stays loud and uninformative.

I am tired of writing rebuttals in prose. Prose is slow and I forget the details by the third paragraph. So is anyone else who has tried to defend their framework choice during a code review. The fix, when this happens often enough, is to stop arguing in adjectives and start producing **a reproducible bake-off**.

This post is about the pattern. It is small. It is reusable. It is the only thing I have found that makes "we are better than X" a tractable conversation instead of a tribal one.

## The thesis, sharpened

A bake-off is not a benchmark. It is a measurement protocol that any contender can run against any baseline, on the same task, with the same inputs, and emit the same shape of result. The output is a table. The columns are the same every time. The numbers come out the way they come out, and people who disagree about the rankings have to disagree about specific cells in a specific table, not about adjectives.

This sounds boring. It is. That is the point. The boring part is what produces the convergence. As long as the numbers are arguable, the conversation is arguable. As long as the conversation is arguable, the field stays in adjectives.

## What a bake-off measures

The columns are the most important design decision. Get them wrong and the whole exercise becomes another vibe contest with prettier formatting. Here is the column set I have settled on after running this exercise enough times.

| Column | What it answers | Why it has to be there |
|---|---|---|
| **Files** | How many source files does the contender's project consist of? | Catches "I ship one file, but it imports a forty-thousand-line SDK." |
| **Lines of code** | How many lines of code in the contender's own files? | Same defense, finer grained. |
| **Calls per task** | How many times does the contender invoke the underlying expensive primitive (model call, network round-trip, database query)? | Hops are latency × cost × failure surface, compounded. |
| **Total tokens or units** | What does one task actually cost, measured at the source of truth (the provider's billing data, not estimates)? | Strips marketing claims about "efficient" pipelines down to a number. |
| **Unique outputs across N runs** | Run the same task N times. How many distinct results? | This is determinism, measured. Adjectives like "consistent" become a number. |
| **Wall time** | At equal concurrency, equal upstream provider, equal inputs, how long? | Latency is what users feel. |
| **Output quality, three samples** | Three printed outputs from the contender, three from the baseline. | The eyeball test. Numbers can mislead; samples grounded in real outputs do not. |

That is the whole table. Seven columns. No more. Nothing else can be argued about, so nothing else gets argued about.

Specifically, two things you might reasonably want to add but should not.

**Do not add an LLM-judged "quality score."** A model judging another model's output is not a measurement. It is an aesthetic preference dressed up as a number. The eyeball samples are what you have. Trust them.

**Do not add a "developer experience" rating.** Developer experience is real, but it is not measurable in this format. Put it in a separate writeup. Mixing it into the bake-off table is what destroys the bake-off, because the rating is opinion-shaped and opinions about ratings spread to opinions about the numbers.

## The shape of the harness

One entry point. One adapter per contender. One client for the underlying expensive primitive. That is the entire structure.

```
bakeoff/
├── harness.py                     # the runner
├── adapters/
│   ├── base.py                    # adapter interface + reference baseline
│   ├── framework_a.py             # one adapter per contender
│   ├── framework_b.py
│   └── framework_c.py
├── clients/
│   ├── real.py                    # real provider; pulls usage straight from the response
│   └── stub.py                    # deterministic offline dry-run
├── corpora/default.json           # the task set
└── README.md
```

An adapter is around thirty lines per framework. The contract is one method: `run_once(task, primitive)`. You pass the contender the same `primitive` callable every other contender gets. You return the final output. That is the entire coupling.

```python
class FrameworkAdapter(Adapter):
    name              = "framework-a"
    file_count        = 8           # real count of project files
    line_count        = 143         # real count of project lines
    framework_version = "1.2.0"

    def run_once(self, task, primitive):
        plan   = primitive(f"PLAN: {task}",  temperature=0.5)
        draft  = primitive(f"WRITE: {plan}", temperature=0.7)
        review = primitive(f"REVIEW: {draft}", temperature=0.3)
        return review
```

The harness loops the corpus, runs each adapter N times, captures `usage` data straight from the primitive provider's response, and prints the table. The whole runner is around two hundred lines. The whole infrastructure is something you can sit down and build in an afternoon.

## Why this works

Three properties of the design are doing the heavy lifting.

**Real numbers, not estimates.** The token count comes from the provider's response field, not from a tokenizer running locally. The wall time comes from the harness clock, not the framework's self-reported timings. The file count comes from `wc -l`, not the README. Numbers from the actual ground truth do not lie, even when the contender wants them to.

**Same primitive, every contender.** Every framework gets the same provider client, called with the same upstream parameters. If a contender's pitch is "we use the same model more efficiently," the bake-off is a fair test of that claim. If the contender wants to use a different model, they can — but they have to declare it, and the comparison becomes "framework X with model A vs framework Y with model B," which is its own honest conversation.

**Determinism is a number.** Running the same task N times and counting unique outputs converts "consistent" from an adjective to a count. Five identical outputs is `unique_outputs/N = 1/5`. Five totally different outputs is `5/5`. Frameworks that pitch reliability now have to land in a particular range on a particular column.

The combination produces a table that is hard to argue with — not because nobody can disagree, but because every disagreement has to point at a specific cell in a specific row of a specific table. The conversation collapses to "this number is wrong because of X," which is the kind of conversation that converges.

## What the bake-off catches that adjectives miss

Three patterns I have seen come out of running the bake-off honestly that the adjective-driven conversation never catches.

**Frameworks that are "minimal" in code but enormous in dependencies.** A framework that ships a hundred lines of orchestration on top of forty thousand lines of dependency code is not minimal. It is invisible bloat. The Files and Lines columns surface this immediately, because the adapter has to declare the framework's own file count, which is comparable to what the dependency size actually is.

**Frameworks that are "smart" but make eight calls per task.** The Calls Per Task column is brutal here. A framework that achieves slightly better output by quintupling the number of provider calls is making a tradeoff the user should know about. The adjective "smart orchestration" hides this. The number does not.

**Frameworks that are "fast" only when the underlying primitive is the bottleneck.** The Wall Time column at equal concurrency reveals when a framework is actually wrapping the same primitive in unnecessary serialization. If two frameworks make four calls each but one takes 50% more wall time, the framework's overhead is the difference, and that overhead is real.

These are the patterns the bake-off catches. The patterns the bake-off is not designed to catch — code style, learning curve, ecosystem maturity — are real but live in a different format. The bake-off is for the numerical claims. Everything else is the next conversation.

## The corpus is part of the contract

A bake-off is only as honest as its task set. A frequent failure mode is to design the corpus to favor your framework, accidentally or otherwise. The defenses against this:

**Publish the corpus.** The full task set goes in the repository. Anyone can run the bake-off against the same corpus. If a contender thinks the corpus is unfair, they can propose additions or substitutions, in pull request form, with a rationale.

**Diversify the corpus.** Tasks at different lengths, different domains, different difficulty levels. A bake-off corpus of all simple tasks favors frameworks tuned for simple tasks; a corpus of all hard tasks favors frameworks tuned for hard tasks. A balanced corpus favors frameworks that handle the range, which is closer to what real users care about.

**Include adversarial tasks.** Tasks designed to expose specific failure modes. A task that produces gibberish under low-effort orchestration. A task that requires multiple retrieval steps. A task that has a definite right answer the framework can be checked against. The bake-off becomes more informative as the adversarial tasks accumulate, because they convert intuitions about failure modes into measurements.

The corpus, like the harness, is a public artifact. If the contenders disagree about the corpus, that is a productive disagreement. If the contenders disagree about the numbers given an agreed corpus, that is also productive. Both are better than the alternative.

## How the conversation changes once a bake-off exists

In my experience, three things happen once a bake-off becomes the standard.

**Adjective claims become rare.** Vendors who used to write "smarter orchestration" start writing "23% fewer calls per task on the standard corpus." The new shape of the claim is checkable. The old shape was not. The vendors who refuse to make checkable claims start to look exactly like the ones who do not have numbers, which they probably did not.

**Internal evaluations get easier.** Choosing a framework for a project becomes "run the bake-off on our actual workload, look at the table, pick the row with the right tradeoffs." The conversation in the team meeting shifts from "what does everyone think" to "look at this table." The team converges faster, and the choice is defensible to people outside the team because the artifact exists.

**The framework field improves.** This is the part I was not expecting. Once a contender publishes their bake-off numbers and the numbers are bad in some specific cell, the contender has a forcing function to improve that cell. The next release ships with a new bake-off run, and the cell improves. The whole field moves up over time, because everyone knows what they are competing on.

This is not a hypothetical. Every benchmark culture in software engineering — language performance benchmarks, database benchmarks, ML model benchmarks — produces this dynamic when the benchmark is taken seriously. The bake-off is what brings the dynamic to framework comparisons.

## What I would tell a team thinking about this

Three pieces of advice.

**Build the bake-off harness once and reuse it.** The harness is small. Two hundred lines or so. The adapters are thirty lines each. Once you have it, every framework comparison costs you a new adapter and a corpus run. Not a new debate.

**Publish the corpus, the harness, and the run results.** Open source the artifacts. The point is reproducibility. If competitors can rerun your numbers and get the same numbers, the conversation is settled. If they can rerun and get different numbers, you both find out why, and the truth gets clearer.

**Resist the urge to add columns.** The seven columns are sufficient. More columns dilute the signal and create new vectors for vibe-driven argument. Keep the table boring. The boringness is the contribution.

The next launch announcement is coming. The next adjective war is coming. The next code review where someone defends their framework choice with conviction and no evidence is coming. The bake-off is the artifact that ends each of those conversations honestly.

Put up numbers, or stop. The pattern lets you put up numbers cheaply enough that "stop" stops being a defensible answer.
