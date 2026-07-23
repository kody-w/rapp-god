---
layout: post
title: "When a single file beats a framework for shipping"
date: 2025-09-30
tags: [engineering, frameworks, distribution, plugins, agents]
description: "Frameworks optimize for composability. Single-file plugins optimize for portability. Most teams reach for the wrong one at the wrong time. Here is when to switch."
---

Pick a problem you want to ship: an agent that summarizes PDFs, a connector that pulls data from a custom source, a workflow that runs a multi-step content pipeline. You sit down to build it. The first decision you make — usually unconsciously — is which framework to use. The framework picks itself by reflex. Whatever the team standardized on. Whatever was on the conference talk last month. Whatever has the loudest README.

That decision deserves a second look. Not because frameworks are bad. They are not. They are some of the best engineering you will ever benefit from. But they are optimized for one shape of problem, and the shape of *your* problem might be a different one. The question worth asking is the simplest one: **is the unit you need to ship a workflow that someone else will install and run, or is it a service you will operate?**

If it is a service, frameworks are great. If it is a workflow that ships, a single file is almost always better. Most teams never name this distinction, and end up using the framework choice for both, and pay the cost on the side that does not fit.

This post is about that distinction.

## What frameworks are actually good at

I want to be precise about what frameworks earn for you. This is not a setup for a takedown. Three popular ones, briefly, by what they actually optimize:

**Composability of building blocks.** The framework is a catalog of adapters: vector stores, retrievers, output parsers, document loaders, memory backends. The value is the catalog and the glue. If your problem is "I have fourteen weird data sources and I need to wire them into a retrieval pipeline," reaching for a composability-first framework is the right call. You are not paying the framework tax for nothing — you are saving fourteen weeks of writing connectors.

**Role-based collaboration.** The framework gives you abstractions for hierarchies, delegation, declarative crew definitions where Researcher hands to Writer hands to Editor. If the mental model of your problem is "a team of specialists with explicit reporting lines," a role-first framework fits the model. Better than rolling it yourself.

**Self-correcting conversational loops.** The framework gives you two-or-more agents that converse, critique each other, retry until convergence. For problems where the loop *is* the algorithm — code generation with self-review, math with verification — the framework's substrate is the right substrate.

Use the right tool for the job. None of this is wrong.

## What frameworks share that is the cost

The shapes are different but the costs are the same. Three popular frameworks all force you to:

- A runtime layer between your code and the underlying call.
- A graph / DAG / state-machine abstraction you must learn to express your workflow.
- A package you `pip install` whose major versions break your code on upgrade.
- A versioned API surface that is bigger than your problem.

These costs are fine if the framework is doing something for you that those costs pay for. They are not fine if the framework is doing nothing the framework boundary requires.

## What "shipping" actually means

Most discussions of "framework vs not" get muddled because people use "shipping" to mean two completely different things.

**Shipping as deployment.** You operate the workflow on infrastructure you control. You roll out new versions on a schedule. The user calls an HTTP endpoint and never sees the code. Whatever framework you used is invisible.

**Shipping as distribution.** Other people install the workflow in their own environment. They `git clone`, or `pip install`, or download a file. The framework you used is now their problem. They have to install it. They have to keep their version of it compatible. They have to debug it when it breaks. The framework boundary travels with the artifact.

The first kind of shipping is forgiving about framework choice. The second is unforgiving. A workflow you operate is a service you can update. A workflow other people install is *a thing they will fork, modify, and run on machines you cannot see*. The cost of the framework boundary is multiplied by every install.

If you are doing the second kind of shipping, the math changes. The framework's catalog is somebody else's installation problem. Its breaking changes are somebody else's upgrade pain. Its directory layout assumptions are somebody else's project-structure assumptions. Every cost that was bearable when you operated the runtime is now charged to a stranger you will never meet.

That cost adds up faster than people realize.

## The single-file alternative

Strip the workflow down to one Python file. One file with a small contract: a class that defines a name, a metadata dictionary, and a method that does the work. The runtime that loads the file is whatever the user already has — a few hundred lines of code somebody can read in an afternoon. No package to install beyond the standard library. No transitive dependency tree. No directory layout assumption. No version pin.

The contract fits in your head:

```python
class Workflow:
    name = "summarize_pdf"
    metadata = {
        "description": "Summarize a PDF file into key points.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "max_points": {"type": "integer", "default": 5},
            },
            "required": ["path"],
        },
    }

    def perform(self, **kwargs):
        # do the work, return a string
        ...
```

A user installs it by saving it as `workflows/summarize_pdf.py` in a directory the runtime watches. The runtime hot-loads the file. It is now callable. That is the entire deploy.

The unit of distribution is a file. Not a directory. Not a manifest. A file. That changes everything that follows from "how does someone else get this to run."

## The composite case

A fair objection: real workflows are not one file. The pipeline that produces my marquee output is a writer, five editor specialists, two reviewer specialists, and a publisher. Thirteen sources. How does that ship as one file?

Authoring happens in the multi-file form. Each persona is its own clean source. You iterate against that form: run the workflow, measure the output, change the personas, run again. Standard development.

When you are happy with the result, a build step *collapses* the thirteen sources into one shippable file. Helper classes get prefixed with an underscore so they do not show up in the registry. Persona prompts get inlined as constants. The single LLM call gets inlined at the bottom. The result is one file, on the order of a few hundred lines, that contains the entire workflow.

The build step is small and stupid: concatenate, mangle, write. It is not magic. It is a Makefile that takes thirteen files in a directory and produces one file in a `dist/` folder.

The user only ever sees the collapsed file. They cannot tell — and do not need to know — that the authoring form was thirteen files. They get the deliverable that fits in `cat | less`.

## The size comparison, honestly

A converged single-file workflow of the kind I am describing is, in practice, a few hundred to a couple thousand lines, somewhere between 10 KB and 50 KB on disk. One import beyond the standard library. The transitive footprint is whatever the runtime is — and the runtime is small.

Equivalent functionality in a popular composition framework would, approximately:

- A dozen-plus files (chain definitions, prompt templates, custom tool classes, output parsers).
- The framework's own install — an order of magnitude or more dependencies, transitively.
- A directory structure you must conform to.
- A framework version you must keep in sync with.

The dependency cost is not the headline. The headline is that **the unit of distribution is a different kind of thing.** Theirs is a project directory plus a manifest. Mine is a file. A file you can email. A file you can drop into a folder. A file you can `cat`. A file you can fork.

When the unit of distribution is a file, ten things become easy that were hard before:

1. **Email the workflow to a coworker.** Attachment.
2. **Show the workflow on a slide.** Paste the source.
3. **Code-review the workflow.** One file, one diff, one PR.
4. **Audit the workflow.** Read top to bottom, fits in a window.
5. **Fork the workflow.** Save-as.
6. **Run the workflow on a Raspberry Pi.** Copy the file. Done.
7. **Run the workflow in a sandboxed runtime.** No package install needed.
8. **Run the workflow in a browser.** Same — no native deps.
9. **Run the workflow on someone's air-gapped laptop.** USB.
10. **Run the workflow under an LLM that cannot install packages.** It can still read and execute one file.

These are not theoretical. They are why the file is a better artifact than the directory for distribution.

## When you should keep using the framework

Not always. The framework is the right answer when:

- **You operate the runtime.** It is your service. You decide which version of the framework runs. You upgrade in lockstep with your dependencies. The portability tax does not apply because the artifact never leaves your environment.

- **You need the catalog.** The framework's adapters and integrations are doing real work for you. Re-implementing them is silly. If the value of the framework is the 200 connectors, and you need 40 of them, take the framework and the dependency tree.

- **The abstractions match the problem precisely.** Genuine hierarchical role delegation, genuine self-correcting conversational loops — when the framework's metaphor *is* the algorithm of your problem, you are spending effort against the framework, not learning a foreign abstraction.

- **The team's reading audience already speaks the framework.** Code is communication. If everyone reading the workflow already knows the framework's idioms, that is a real cost saving.

In any of these cases, the framework earns its keep. Use it.

## When you should switch to single-file

Switch when:

- **The unit of distribution is the workflow people will install**, not a service endpoint you will operate.
- **Portability across runtimes matters.** The same file has to run on a server, in a browser, on a constrained edge device, and inside a constrained AI runtime that cannot install packages.
- **The next maintainer should be able to `cat` the file and read it.** No IDE jump-to-definition required. No five files to open in parallel.
- **You want users to fork the file**, not file feature requests against your framework.
- **You are crossing a sandbox boundary** — a serverless cold start, a Pyodide tab, a tightly scoped agent runtime — where bringing a heavy dependency tree is not free.

The honest test is the email test. If you cannot email the workflow to a colleague and have them run it without setting up a project, you are not actually shipping a workflow. You are shipping a project. Those are different products. Be honest about which one you are making.

## The architectural principle

The deliverable is the file. The loop is your authoring process. The framework you used to author it is private.

The public contract should be a file, not a framework dependency. Whatever you do behind that contract — whichever framework, whichever composition library, whichever hand-rolled subagents — is your business. What crosses the boundary to the user is one file they can read, fork, email, and drop into a directory.

That is the thing the major frameworks are *not* optimizing for, because they are optimizing for other things. It is the thing you should optimize for, when shipping is what you are doing.

Use the framework when you are operating. Use the file when you are shipping. Most teams confuse these. Now you do not have to.
