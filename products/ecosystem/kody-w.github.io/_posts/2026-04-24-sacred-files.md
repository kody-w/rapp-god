---
layout: post
title: "Sacred Files: Declaring Code Frozen on Purpose"
date: 2026-04-24
tags: [engineering, discipline, architecture, code-review]
---

Most systems have one file that holds them together. Not the biggest file. Not the "important" file. The *load-bearing* file — entry point, dispatch table, bootstrap. When it drifts, everything downstream drifts with it. When it stays still, every other file gets to move freely.

The usual move is to protect that file with folklore. "Don't touch X." New people touch X anyway; folklore doesn't survive onboarding. Six months later it's 4× the size and nobody remembers why.

The better move is to **declare the file sacred in writing**, with a rule any reader can apply.

## The declaration

One paragraph, at the top of the file or in the constitution that governs it. Three pieces:

1. **What the file is responsible for.** Concrete list, not prose. Entry routes. Auth chain. Core loop. Boundary with the rest of the system.
2. **What counts as a legitimate edit.** Usually: bug fixes in existing behavior. Sometimes: adding one class of output slot. That's it.
3. **Where everything else goes instead.** New features? Plugins / agents / whatever the system's extension point is. Helpers? A utility module. Provider-specific quirks? An adapter file.

The discipline isn't "never change the file." It's "when tempted to change it, check the declaration, and realize your change belongs somewhere else 90% of the time."

## Why the declaration works

Declared rules force a conversation the folklore rule never has. A pull request that touches the sacred file now reads differently — reviewers look for the *justification against the written contract*, not for general code quality. Most PRs fail that test on their first draft. The second draft is a new file somewhere else, and that's the whole point.

The rule also scales. You can onboard a new engineer with a link to the article. You can ask an LLM to check changes against it. You can put a pre-commit hook on it and get a meaningful failure message. None of that works when the protection is "ask around first."

## Why it's cheap to do

You don't have to refactor the sacred file to declare it sacred. You don't even have to make it smaller. You just write the article. The file might be huge and tangled on the day you declare it — but from that day forward, it stops growing, and the codebase starts finding homes for new work that aren't the sacred file. Over time the sacred file shrinks because nobody's adding to it, and the tangled parts get rewritten as they become bugs.

Declaration is the cheap move. Enforcement is downstream of having something to enforce.

## The shape of the rule in practice

Three anti-patterns the article should rule out, explicitly, by name:

- **"Small helpers added inline."** Helpers should live in a utility module. The sacred file is not a dumping ground.
- **"New HTTP routes for extension-shaped work."** If the extension point is a plugin/agent/hook, new capabilities go there, not next to the bootstrap.
- **"Silent contract changes."** Renaming a route, reshaping a response envelope, reordering a core loop — these are SPEC-level changes. They get a version bump, a tag, a migration note. Not a drive-by refactor.

The anti-patterns exist because someone tried to do them before the article. The article names them so nobody has to learn the lesson twice.

## The result

A file you can leave alone. A system you can reason about. New work that finds its right home by default instead of by lucky review. A codebase that stays readable because its center of gravity was defined, not discovered.

Write the article before you need it. You'll need it sooner than you think.
