---
layout: post
title: "Architect, don't type: how to actually use an LLM for production code"
date: 2025-10-04
tags: [engineering, llms, ai-coding, software-development, architecture]
description: "The quality of LLM-generated code is bounded by the quality of the design it's implementing. Most of the work happens before any code is generated. Here is the workflow that produced a hundred thousand lines of working software in a month."
---

The first time I shipped a hundred thousand lines of working code in a month, I wrote maybe five percent of it by hand. Not "five percent of the lines that survived editing." Five percent of total characters typed. The rest was generated, reviewed, integrated, tested, and shipped through a workflow that does not look like the one most people imagine when they say "I use an LLM to code."

This is not a story about how good the model is. The model is an input. The workflow is the load-bearing part. Different developers, given the same model, get wildly different results. Some get a coding partner that ships real software. Some get a glorified autocomplete that produces plausible-looking nonsense. The gap is in the *process*, not the prompts. This post is the process.

## The shift: architect, don't type

The uncomfortable truth I have accepted is that my engineering skills did not become useless when LLMs got good. They moved up a layer.

I no longer need to know how to write a correct `for` loop in five languages. I absolutely need to know **whether the right structure here is a loop at all, or whether this should be an event-driven pipeline, or a stateless map, or a queue with backpressure.** I no longer need to remember the exact import path for the standard library's HTTP client. I do need to know whether the right call here is HTTP at all, or whether this entire interaction should be local file I/O, or a message bus, or a database transaction.

The skill I trained for years — "I can produce correct code at the keyboard" — has been mostly automated away. The skill I had been picking up casually — "I can describe a system precisely enough that someone else can build it" — turns out to be the highly leveraged one. That skill, sharpened deliberately, makes LLMs into something useful. Without it, they make a mess.

## The phases, with honest time allocations

The work splits into three phases. The ratio of time spent in each is probably not what you would guess.

**Phase one — design conversation. About 60% of the time.**

This is where the real work happens, and it is almost entirely talking. I start every feature by describing what I want at a high level, then drilling down through questions until the model and I have a shared understanding that is detailed enough to execute against.

This is not prompting. This is collaborative design. The model asks good clarifying questions when given the chance: *what happens if two writers modify the same record? Should we lock or use optimistic concurrency? What if the process crashes mid-write?* I answer with the constraints I have already worked out from operating the system: *yes, lock at the row level; the failure mode we cannot afford is a half-written record being readable by someone else; here is how we handle the abort case.*

By the end of this phase I have the architecture in writing. I know what data structures we are using. I know which existing modules this feature touches. I know which invariants must be preserved. I know what the failure modes are and how we handle each one.

If I skip this phase and just say "build me a feature," the model will build something that works for the first three days and then falls apart under load. I know this because it has happened to me. Several times. In ways that produced production incidents that were entirely my fault for asking the wrong question.

**Phase two — execution. About 25% of the time.**

Once the design is locked, the actual code generation is the fastest part. The technique that matters here is to work in *small, verifiable chunks*.

Not "build the whole feature." Instead: "implement the writer with atomic writes, and show me a test for it." Then: "now implement the reader in timestamp order." Then: "wire it into the workflow that schedules these calls."

Each chunk is small enough that I can verify the *shape* of the solution by reading. I am not auditing every line. I am checking: does it use our existing helper for atomic file writes, or did it inline a raw `open` and `json.dump`? Does it handle the empty-input case correctly? Does it write to the right output channel so the downstream consumer gets fresh data?

Domain knowledge pays off enormously in this phase. When the model emits a direct file-write instead of using the helper that handles fsync and read-back validation, I catch it instantly because I designed the helper. If I had not been in the architecture conversation, I would not know to look for that, and we would have a quiet data corruption bug in production.

I also keep a *running document of constraints* — facts about the codebase that should never have to be re-established mid-session. Things like "we use the standard library only — no third-party HTTP clients," or "all writes go through `state_io.save_json()` — never raw file writes," or "comments live in the comments service, not in the post records." These are guardrails. Each session loads them automatically. They prevent the model from inventing its own patterns when perfectly good ones already exist three files away.

**Phase three — quality gate. About 15% of the time.**

After the code is generated, I run it through three checks. None of these are optional.

*Does it compile and pass tests?* Obvious, but skipped by an alarming number of teams. Tests are how I verify the model did not quietly break an invariant in a file three directories away from the change it made. The model is good at making something work locally. It is less reliable at not breaking something distant.

*Does it match the architecture we agreed on?* I re-read the generated code at the function level, not the line level. I am checking: did it follow the dispatcher pattern we established? Did it register the new handler in the right map? Did it set the right dirty flag so only modified files get serialized? Being the architect — not just the prompter — is what makes this check possible. I know what "correct" looks like because I designed the shape of it.

*Does it integrate?* Integration bugs are the hardest to catch. The model might write a perfectly correct piece in isolation that does not know about the safe-commit retry logic, or the concurrency group, or the cache invalidation hook. These bugs only show up when the whole system runs end-to-end, which is why I run end-to-end tests early and often, not as a final gate.

## The constraint philosophy

Here is the most counterintuitive thing I have learned: **constraints make LLMs better, not worse.**

The system I work in has aggressive constraints. Standard library only — no third-party packages. One language for the runtime; one language for the build. A flat file storage model that splits to many files only above a size threshold. Platform primitives are preferred over custom code — if the hosting platform offers it, we use it instead of reinventing it. Append-only by convention — content is rarely deleted, only superseded.

These constraints feel limiting. They are actually liberating, for the model and for me.

When I say "implement this feature," the model does not have to choose between forty-seven HTTP libraries. It uses `urllib.request`. It does not have to debate between three database engines. It uses flat JSON files with a known atomic-write helper. It does not have to invent a content moderation pattern; the constraint says we use the platform's existing flagging API.

The constraint space is small enough that the model can reason about it completely. There is no decision paralysis, no flailing across alternatives, no half-measures. The model is operating within a tractable design space, and within that space it is fast and accurate.

The constraint document is not a vague "be a good programmer" exhortation. It is concrete and specific: *"Every script accepts `STATE_DIR` as an environment variable. Tests override this to a temp directory. Use `write_delta()` from `conftest.py` to construct test data — never inline the format. The `id` field is opaque to handlers; do not parse it."* That level of specificity is what prevents the model from inventing its own patterns instead of using the ones already in the codebase.

The lesson generalizes. The cleaner your codebase's invariants — the smaller and more explicit its design space — the better an LLM will write code in it. The same design discipline that makes a codebase pleasant for human contributors makes it tractable for AI ones. They are the same skill.

## What goes wrong

The process is not foolproof. Four failure modes, all of which I have caused, are worth pre-naming.

**Skipping the architecture conversation.** The model builds something that works in isolation but does not integrate. It builds a comment targeting algorithm that completely ignores the channel subscription model, because nobody told it the channel subscription model existed. The fix is to slow down and have the design conversation. Architecture comes from a person, not a prompt.

**Letting the constraint document rot.** When the constraints are not maintained — when new invariants are added in code but not in the document — the model repeats mistakes. It reaches for the third-party HTTP package on every new session. It reinvents file-write logic instead of using the helper. The fix is to treat the constraint document as production code: when you add a new invariant, you update the document, same PR.

**Working on unfamiliar territory.** When I venture into a domain I do not actually know — say, frontend CSS, when my background is backend Python — the model's choices are harder for me to evaluate. The output has to be much more conservative because my own quality gate is weaker. The general principle: the value an LLM adds is bounded by your ability to evaluate its output. In domains where you cannot evaluate, you cannot ship LLM code with confidence. You can still use it to learn — but you cannot use it to ship.

**Trying to do too much in one session.** Context degrades. The best results come from focused sessions: one feature, one conversation, one execution cycle. When I cram three features into one session, the model starts making tradeoffs I do not agree with because it is juggling too many concerns. The fix is to scope sessions tightly. One thing per chat.

## The meta-lesson

Here is what most people get wrong about coding with LLMs: they treat it as a prompting problem. "If I just write a better prompt, the code will be better."

It is not a prompting problem. It is an architecture problem.

The quality of LLM-generated code is bounded by the quality of the design it is implementing. A perfect model with a bad architecture will produce perfectly implemented bad code. A mediocre model with a good architecture — clear constraints, well-defined interfaces, explicit invariants — will produce surprisingly good code. The architecture is the lever. The model is the screwdriver.

My role on these systems is not "programmer who types faster with AI." It is architect, constraint designer, quality gatekeeper, and domain expert. The model is the world's most knowledgeable junior engineer who can implement anything I describe, as long as I describe it precisely enough.

If you want to ship real software at scale with AI as a coworker, your engineering muscle does not become useless. It moves. Most of the work moves to the design phase, where you are deciding the shape of the system. Some of it moves to the constraint document, where you are writing down the invariants the model needs to respect. A small amount stays in the keyboard, where you are checking the output against what you asked for.

The code is real. The architecture is yours. The typing is someone else's job.

You will be a better engineer at the end of a project run this way than you would have been writing every line yourself. Not because the model carried you. Because the discipline the workflow forces — *describe everything before building anything* — is the same discipline the best engineers have always practiced. The model just makes it impossible to skip.
