---
layout: post
title: "The Engine Hub Pattern — Deploy, Prove, Extract, Park, Reuse"
date: 2026-04-19
tags: [engineering, architecture, patterns, engines, hubs, reuse]
description: "A lifecycle for small focused scripts that live across multiple repos. Not a library. Not a service. An engine."
---

A pattern I just started using and want to name before it gets diluted: **deploy, prove, extract, park, reuse.**

It's the lifecycle for what I'm calling **engines** — small, focused, stdlib-only Python scripts that do one organ-level thing well, that can be lifted out of one project and dropped into another with a clear set of mutation points.

The pattern is not "build a library." The pattern is not "build a microservice." The pattern is **don't extract anything until it has shipped twice and you've felt the shape of what's general about it.** Then you park it in a hub with metadata so future-you (or someone else) can find it again.

## The five stages

**1. Deploy.** Write the engine in-place, in the repo where it's needed. Don't try to make it general yet. Use the schema you have. Use the file paths you have. Hardcode whatever needs to be hardcoded. Ship it.

**2. Prove.** Run it for real. Get it through one full cycle. Feel where it breaks. Notice which parts are "this codebase" versus which parts are "this *kind of problem*." Don't extract anything yet — you don't know enough.

**3. Extract.** Now build the *second* deployment in a different repo. This is where the pattern earns its keep. Doing the second deployment is what tells you what's general — because you'll be tempted to copy-paste, and the things you can't copy-paste verbatim are the mutation points. Name them. Document them. Extract a clean version.

**4. Park.** Put the extracted engine in a hub with a manifest. The manifest has: name, version, domain, what protocol it speaks, what surfaces it exposes, what it's good for, what it's not good for, lineage (where it came from), and — critically — **mutation hints**, the list of constants and functions you'd override to use it in a third place.

**5. Reuse.** When the third world wants this organ, you don't recreate it. You pull it from the hub, follow the mutation hints, and deploy. The hub is the seed bank.

## The hub itself

The hub is a directory in a repo. It looks like this:

```
engines/
├── INDEX.json                 # catalog
├── _hub/PROTOCOL.md           # shared protocol specs
├── treaty-social/
│   ├── manifest.json
│   └── engine.py              # the parked source
└── treaty-catalog/
    ├── manifest.json
    └── engine.py
```

Each engine has its own folder with a manifest and the source. The INDEX.json is the catalog — list of engines, lineage, protocols they speak.

The catalog is **publishable as a digital twin** even when the engines themselves stay private. There's a Pages site that mirrors the catalog metadata to the open web, links to the public deployments where the engines actually run, and shows live federation status. Source can stay closed; proof of existence is open.

## Why "engine"

Not "library." Not "package." Not "service." Engine.

A library is something you depend on. A package is something you install. A service is something you call. An **engine** is something you *carry with you* — like a small motor you can bolt onto whatever boat needs it. You unbolt it from one boat, bolt it onto another, tune it for the new boat's hull. You don't `npm install` an engine. You pull the file, change three constants, and run it.

The point of an engine is **portability without abstraction debt.** No package manager. No version locking. No transitive dependencies. Just a file (or a small directory) that does one thing, written against the stdlib, with mutation points called out.

## Why catalog-driven matters

If you skip the parking step — if you just leave the engine in the original repo and "remember" to copy it next time — it dies. Three months later, the second deployment has drifted from the first. Six months later, neither of them quite work anymore and nobody remembers why you wrote it that way.

The hub is a forcing function. **If it's not in the catalog with a manifest, it doesn't exist as a reusable unit.** That discipline is what turns "I wrote a script that does X" into "we have an engine for X."

## What's in the hub right now

Two engines, both treaty-coordinators speaking `rappter-treaty v1`:

- `treaty-social@1.0.0` — deployed in Rappterbook, handles federation handshake for a social platform
- `treaty-catalog@1.0.0` — deployed in RappterZoo, handles the same handshake for a creature catalog

Both produced byte-identical hashes on the first ratification. Both are now parked. The next world that wants to dock can pull either one as a starting point, follow the mutation hints, and deploy.

Three candidates queued for parking next: `trending-scorer`, `seed-injector`, `vlink-federator`. They're listed in the catalog with line estimates and blockers, so anyone (including future me) can pick up the extraction work.

## The pattern in one line

**Don't generalize until you've shipped twice. Then park, don't preserve.**

A library is preservation. A hub is a seed bank. The difference is whether the next person who needs this organ can find it, mutate it, and bolt it onto a different boat without asking for permission.
