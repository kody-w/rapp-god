---
layout: post
title: "One concept per repo"
date: 2025-10-02
tags: [architecture, monorepo, polyrepo, separation-of-concerns]
description: "The strongest predictor of whether a repository will stay maintainable is whether anyone can answer the question 'what is this repo for?' in one sentence. If the answer takes more than one sentence, you have at least two repos pretending to be one."
---

The strongest predictor of whether a codebase will stay maintainable over time is whether anyone can answer the question *what is this repo for?* in one sentence. Not a paragraph. Not a list. One sentence.

If the answer takes more than one sentence, the repository is doing more than one job. It does not yet feel that way. It feels like a single project with related concerns. But the seams are already drawn. Every cross-cutting change touches multiple unrelated audiences. Every commit mixes concerns that should not have been adjacent. Every README has to explain too many things to too many readers. The repository becomes harder to scan, harder to navigate, harder to onboard to, and harder to change without breaking something unrelated. Slowly, then all at once.

The fix is brutally simple to state and surprisingly hard to enforce: **one concept per repo. No exceptions.**

This post is about why that rule earns its dogmatism, what counts as "one concept," and the specific failure modes that force teams to split a repository they wish they had split a year earlier.

## The rule

> Every concept that has its own lifecycle, its own audience, or its own publication surface gets its own repository.

Three load-bearing words: *lifecycle, audience, publication surface*.

If two pieces of code change on different schedules, they have different lifecycles. They go in separate repos.

If two pieces of code are read by different groups of people — different developers, different operators, different external contributors — they have different audiences. They go in separate repos.

If two pieces of code are published to different channels — one is npm, the other is Docker Hub; one is internal, the other is open source; one is a CLI download, the other is a web app — they have different publication surfaces. They go in separate repos.

Any one of these three differences is enough. You do not need all three. You need one.

## What "one concept" looks like in practice

The cleanest way to think about a concept is: *what is the single thing this repository produces, and who is the single audience that consumes it?*

A library is one concept. The thing it produces is a versioned package. The audience is developers integrating that package into their own code.

A service is one concept. The thing it produces is a deployable artifact. The audience is the operator who runs it.

A CLI is one concept. The thing it produces is a binary or installer. The audience is the user who runs it.

A documentation site is one concept. The thing it produces is HTML. The audience is the reader.

A schema specification is one concept. The thing it produces is a normative document. The audience is implementers of that schema.

When a repository has more than one of these, it is at least two concepts pretending to be one. The library that ships its own CLI? Two concepts. The service that includes its own documentation site? Two concepts. The schema specification that includes a reference implementation in one specific language? Two concepts.

You can usually feel this as soon as you ask "what is the version of this repository?" If the answer is different for different parts of the repository, you have multiple concepts and you are paying the cost of pretending otherwise.

## Why you do not put the engine in the platform repo

Here is the most common version of this mistake, and the one I have personally made the most.

You build an engine — the part of the system that does the hard work. Usually the engine is private, complex, or operationally sensitive.

You build a platform — the part of the system that exposes the engine's output. Usually the platform is public, has a stable API, and is meant to be read or used by other people.

The temptation is to put the engine in the platform repo, in a different folder. "It is part of the platform, just in a different directory." Resist it.

Reasons:

**The engine has a different audience than the platform.** Operators and internal contributors read the engine. External users and public agents read the platform. They have different reading patterns, different commit-message conventions, different permission boundaries. Mixing them produces a repository where neither audience can find what they want.

**The engine has a different lifecycle than the platform.** Engine changes are operational — prompt tweaks, model upgrades, harness adjustments. They happen multiple times a day. Platform changes are public — schema evolutions, SDK additions, breaking-change deprecations. They happen on a much slower clock. Mixing them produces a commit history where neither cadence is legible.

**The engine has a different publication surface than the platform.** The engine never publishes anything; it operates. The platform publishes a state surface, an SDK, possibly a UI. They go to different consumers. Mixing them produces a release process that has to coordinate things that should never have been coupled.

**The engine has different security properties than the platform.** The engine has access to secrets, write tokens, internal infrastructure. The platform is public-readable. Mixing them is a vulnerability waiting to happen — every engine commit risks leaking a credential to a public repo, every platform commit risks accidentally exposing engine internals.

The four reasons compound. Within a few months of co-locating, every change touches both audiences, the commit history becomes unscannable, and the team starts proposing folder-level access controls to manage the mess. That is the moment to split.

## When two repos *should* live together

A fair objection: surely there are repositories that legitimately contain more than one logical concept. The standard examples are monorepos at scale, or projects where a thin "everything else" is bundled around a core.

The fair version of the rule is: *if two pieces of code have the same lifecycle, the same audience, and the same publication surface, you can put them in one repo.* Practically, this is rare unless the project is very small. The standard counterexamples to "one concept per repo" usually do not actually meet the test — they bundle things that have one of the three differences and just have not split yet.

Two patterns that do legitimately stay together:

**A library and its tests.** The tests have the same lifecycle as the library, the same audience (the library's maintainers), and no separate publication surface. They belong with the library.

**A library and its example folder.** Examples are part of the documentation surface of the library and ship together. Same lifecycle, same audience.

A few that look like exceptions but are not:

**A library and its docs site.** Different audience (developers reading the API vs. anyone reading the marketing prose), often different publication surface (npm vs. a web URL). Almost always better as two repos.

**A service and its CLI tooling.** Different audience (the operator vs. the developer), different release cadence. Almost always better as two repos.

**A schema and its reference implementation in language X.** The schema is a spec; the implementation is a library. Different audiences (implementers in any language vs. users of language X), different publication surfaces. Almost always better as two repos.

The phrase "almost always" is doing real work in those bullets. There are exceptions. They are smaller and rarer than people think.

## The current shape of a well-split system

For any non-trivial system, the polyrepo map ends up looking something like this:

| Repo | Concept | Visibility | Audience |
|---|---|---|---|
| `engine` | The operational core: prompts, harness, business logic | Private | Operators |
| `platform` | The public-facing state, SDK, public scripts | Public | External users, partner integrations |
| `spec` | The protocol or schema definition | Public | Implementers, third-party clients |
| `cli` | A command-line tool against the platform | Public | Developers |
| `docs` | Long-form documentation, marketing site | Public | Readers, prospects |
| `examples` | One-off demonstrations and starter kits | Public | Onboarding users |
| `artifacts/<name>` | One repo per generated artifact (one per project) | Public | The artifact's specific users |

Each repo has one job. None of them know about the others' internals. They communicate through stable contracts: a specification, a public state file, a published API. The contract is the boundary; the repository is the container; the README answers *what is this for* in one sentence.

When you read any of these repos for the first time, you can tell what it is for. There is no scrolling. There is no folder ambiguity. The shape of the directory matches the shape of the concept.

## The cost of the alternative

Anyone who has worked in a repository that violated this rule already knows the cost. It is worth naming the cost precisely so the rule earns its weight.

**Cognitive load grows superlinearly with concepts.** Two concepts in one repo do not just take twice the effort to navigate. Every folder is potentially relevant to either, every file requires a check, every PR has to be read with two contexts in mind. The friction multiplies.

**Onboarding gets worse, not better.** New maintainers face an expanded surface area. They cannot ramp on one concept first because they do not know which folders belong to which concept. The "explain the architecture" conversation takes hours instead of minutes.

**Cross-cutting commits become the norm.** A change that should have been local to one concept ends up touching files from another. Reviewers cannot tell what is intentional and what is bleed. CI runs are slower because more is being tested per commit.

**Public surface accidentally leaks internal details.** When the engine and the platform live together, the engine's commit messages are visible to platform users. The engine's branch names, file paths, and PR descriptions become public artifacts. Some of that information was supposed to be operationally private.

**Splitting later is expensive.** Two concepts that have grown together for two years are entangled at the file, function, and import level. Splitting them requires unraveling actual dependencies, not just moving files. Every "we'll split it later" decision compounds into a more expensive split when the time finally comes.

The cost is real. It is also paid in slow drip rather than in one visible event, which is why the rule needs to be dogmatic — by the time you can prove the cost, the split is already expensive.

## The signal it is time to split

You will know it is time when:

- You start describing the repo as "the X *and* Y."
- You add a folder-level CODEOWNERS file because different parts have different reviewers.
- A meaningful number of PRs touch only one concept.
- You catch yourself wishing the README could have separate sections for separate audiences.
- A new contributor asks "where is the X part?" and you have to give directions.
- You instinctively `cd` to a subdirectory immediately after `git clone`.

Every one of these is a soft signal that the repository has already split conceptually, and the directory structure is just lagging the reality.

When you see two of them, do the split. It is cheaper today than it will be next quarter.

## The summary, blunt

If you want to keep your repositories maintainable for the long run, treat the question *what is this repo for?* as a load-bearing constraint. If the answer takes more than one sentence, the repository is doing more than one job. Split it now, while the entanglement is small. Pay the small cost today so you never have to pay the big cost.

One concept per repo. No exceptions.
