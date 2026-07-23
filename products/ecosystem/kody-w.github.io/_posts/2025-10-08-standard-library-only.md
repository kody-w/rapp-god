---
layout: post
title: "Standard library only: why constraints breed better architecture"
date: 2025-10-08
tags: [engineering, dependencies, architecture, constraints, software-design]
description: "I built and operate a non-trivial system in production that has zero third-party dependencies. The constraint was deliberate and the architecture is better for it. Here is what the rule is, what it costs, what it buys, and when you should adopt it."
---

I run a system in production that has no `pip install`. No `npm install`. No `requirements.txt`. No `package.json`. No Docker. The Python is whatever ships with Python. The JavaScript is whatever runs in a browser without any build step. The CI is `bash` and `python -m unittest`.

This is not minimalism for its own sake. It is a deliberate architectural constraint that has shaped every design decision in the system, and the system is better for it. Most teams reach for "stdlib only" as an aesthetic preference and abandon it the first time they need an HTTP client. Used as an actual architectural rule, with a clear understanding of what it buys and what it costs, it produces software that is faster to deploy, easier to audit, and dramatically cheaper to maintain.

This post is the rule, the reasoning, the cost, and when to use it.

## The rule

Standard library only. No exceptions. That means:

- `urllib.request` instead of `requests`.
- `json` instead of an ORM.
- `tempfile` and `os.replace` instead of a key-value cache.
- `subprocess` instead of an orchestration framework.
- `pathlib` instead of any path library.
- `hashlib`, `datetime`, `re`, `argparse`, `unittest` for everything they cover.

Every script in the system imports nothing that does not ship with the language. The frontend follows the same rule on the JavaScript side: no framework, no build step, no transpiler, no bundler. The browser runs what is on disk.

The rule is dogmatic on purpose. The moment you allow "just one dependency," you have started a list, and the list will grow indefinitely. The dogmatic version stops the conversation before it starts: not "should we add this dependency," but "we do not add dependencies."

## Why dogmatism matters here

Dependency creep is a slow problem. Each individual dependency seems reasonable. The first one solves a real problem. The second one saves an afternoon. The third one is borrowed from another project. Before you notice, the project has thirty transitive dependencies, half of them you have not audited, and your CI takes four minutes to install them every time it runs.

You did not make a decision to be in this state. You drifted there. Each yes was small. The accumulated cost is large.

The way to not drift is to make the policy *binary*. Yes/no on dependencies, not "yes if reasonable." A binary policy is enforceable. A graded policy is not.

If you allow exceptions, you have a graded policy. The exception list grows. The "exceptional" dependencies are no longer exceptional. The discipline is gone.

So the rule is: standard library only. If you encounter a problem the standard library does not solve cleanly, you write the smallest possible solution to it yourself, in a few hundred lines or fewer, in your own codebase, where you can read it and fix it.

## Three reasons it is worth the cost

**One: deployment is free.** Every CI run, every fresh runner, every cold start of every workflow begins from the language's interpreter and only the language's interpreter. No `pip install`. No `npm ci`. No `apt-get install`. The startup cost of any process is whatever the language takes to launch — milliseconds.

When your CI runs dozens of workflows per day, and every workflow currently spends 30–90 seconds installing dependencies, removing that step *changes the day*. Pull requests merge faster. Deploys are quicker. Reliability goes up because there are fewer moving parts to break.

For a system whose CI is on the critical path of operations — anything that runs on a schedule and updates state continuously — the deployment-cost reduction is the single largest benefit of the rule.

**Two: dependencies hide complexity you need to understand.** When you write an HTTP call with the language's stdlib client, you see the headers, the timeout, the error codes, the retry logic, the status check. You make every decision yourself. You also *understand* every decision yourself.

When you write the same call with a popular HTTP library, you have delegated all of that to the library. The headers are set somewhere in the library. The timeout has a default that may or may not be the one you would have picked. The retry logic is whatever the library decided. The error model is the library's, not yours.

This delegation is fine for problems that are not on your hot path. For problems that are on your hot path — for me, that includes LLM calls, rate limiting, circuit breaking, budget tracking — that delegation is a liability. You cannot debug what you do not understand. You cannot tune what you cannot see. The library gives you the surface and hides the substance.

The standard library version is verbose. It is also yours. You can read it, change it, and reason about it without consulting documentation written by someone else.

**Three: constraints breed better architecture.** This is the counterintuitive one, and the most important.

When you cannot reach for an ORM, you build something that fits your actual data model — usually flat files, the smallest possible serialization, plus an index. When you cannot reach for a web framework, you build exactly the routing and request handling you need — usually a few dozen lines, no more. When you cannot reach for a message queue, you discover that your existing storage layer can already serve as one if you treat it carefully.

Each of these substitutions is *a forced confrontation with the actual problem*. The framework was a way to avoid thinking; without it, you have to think. Most of the time the thinking produces a smaller, better-fitted solution than the framework would have.

The frameworks exist because real teams shipped real software on them. They are not bad. They earn their keep when you have a generic problem that fits the framework's generic answer. They are a poor fit when you have a specific problem and the framework's answer is a generic shape that you have to bend your specific problem into.

The standard-library rule forces specificity. The result is a codebase where every piece of code exists because someone needed it for the actual job, not because the framework offered it.

## The cost, honestly

The rule is not free. Three real costs are worth being honest about.

**You write more code.** Not dramatically more — most stdlib substitutes are five to twenty lines instead of one — but the line count creeps up. You also write small amounts of code that exists only because the language did not give you a one-liner: pretty-printers, simple retries, basic argument parsing, formatting helpers.

Over the lifetime of the project the volume is small. In the first month it is noticeable.

**You forgo features the popular library provides for free.** A popular HTTP library might do connection pooling, automatic retries, automatic JSON encoding, response caching, and helpful error formatting out of the box. The stdlib does not. You write the ones you actually need, and you do not get the ones you forgot you wanted.

For most systems, you only need a fraction of the popular library's surface area, and writing that fraction yourself costs less than learning, configuring, and updating the library would have. But this is genuinely a cost.

**You take on long-tail edge cases yourself.** Time zone handling. Unicode normalization. URL parsing edge cases. SSL configuration. The popular library's authors have run into all of these and added defensive code. You are starting from zero. You will hit some edge cases the library would have absorbed.

The mitigation is to write tests for the edge cases as you encounter them, and to keep the standard-library-substitute code in dedicated, well-tested modules so the team does not re-discover the same edge cases ten different times.

## When the rule is the right call

Standard-library-only is the right rule when:

- **The codebase is small enough that you can read it.** If you cannot fit the codebase in your head, you cannot keep the substitute layers consistent, and the rule produces fragmentation. There is a size beyond which "we'll write our own" stops scaling and you have to import. Find that size honestly.

- **The system runs on platforms with constrained or expensive dependency installation.** Serverless cold starts. Edge runtimes. Environments where the package manager is not available. CI runs where every install is paid time. In these settings, the deployment cost of dependencies is the largest cost in the system, and removing it is dramatic.

- **Long-term maintenance matters more than short-term feature velocity.** A codebase that depends on twenty third-party libraries is a codebase that has to track twenty third-party release schedules, audit twenty changelogs, debug twenty CVE alerts a year. A codebase with zero dependencies has none of that work. If you plan to operate the system for years and cannot reliably staff "library upgrade duty," the no-dependency baseline is cheaper than the alternative.

- **Auditability matters.** Standard-library-only makes the system *fully readable*. Anyone reviewing the code can read every line. There is no "what does this library actually do" question. For systems with security or compliance audit requirements, this property has real value.

- **The team has the skill and the appetite.** This rule is technically demanding. You are writing code instead of using libraries. The team has to be able to do that. If the team would rather move fast and import, the rule produces frustration without producing benefit.

When *any* of those reasons applies — let alone several at once — the rule earns its keep.

## When the rule is the wrong call

Standard-library-only is the wrong rule when:

- **The codebase has to scale beyond what you can hold in your head.** Above a certain size, dependency management becomes cheaper than substitute proliferation. The threshold is fuzzy; if you are debating it, you are probably above it.

- **The actual hot path is something a library does brilliantly that stdlib does poorly.** Numeric arrays. Cryptography you have not personally proven. Anything where the cost of a wrong implementation is unacceptable. Use the right library.

- **The team is large.** With many contributors, "we wrote our own" goes from "asset" to "liability" quickly. Each contributor has to learn the substitute layers. Inconsistencies creep in. You start needing a style guide for substitutes. At that point, importing the library is cheaper.

- **You actually need the library's domain expertise.** A HTTP/2 client is hard. A correct cryptography implementation is *very* hard. A vector database is harder than rolling your own. There are domains where the library author knows things you cannot pick up in an afternoon, and you should defer.

In any of those cases, the dogmatic version of the rule fails the codebase. Soften the rule, with named exceptions, and accept the dependency tax.

## The summary, made dogmatic

If your codebase is small, your platform is constrained, your maintenance horizon is long, and your team can write code instead of importing it — adopt standard-library-only as a hard rule. The constraint will force a smaller, better-fitted, faster-deploying codebase. You will pay a small upfront cost in line count and feature breadth. You will save dramatically on deployment time, audit surface, and long-term maintenance.

If any of those preconditions does not apply, do not adopt the rule. You will get the cost without the benefit.

The right architecture is not the maximally minimal one. The right architecture is the one whose cost profile matches your actual constraints. For some systems, dependency-zero is a perfect fit. For others it is a cosplay. Know which you are.
