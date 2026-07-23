---
layout: post
title: "One contract, two runtimes"
date: 2025-09-25
tags: [engineering, plugins, architecture, browser, server]
description: "When the same code needs to run in two different places — a server and a browser, a native binary and a sandbox — the instinct is two plugin ecosystems with two contracts. The better instinct is one contract with two formats. Here is what that costs and what it buys you."
---

A common situation in any system that grows beyond one runtime: you have capabilities — tools, plugins, functions, agents, whatever the unit of extension is — and they need to run in more than one place. Maybe a server-side runtime where you have the full operating system, and a browser-side runtime where you have a sandbox. Maybe a native binary where you can do anything, and an embedded environment where you cannot. Maybe a Python-based daemon and a JavaScript-based device agent.

The instinct, in every system I have watched go through this transition, is to design two plugin systems. Server-side has its plugin format, browser-side has its plugin format, the two are loosely related but not actually compatible, and over time they diverge. A capability shipped for one cannot be used in the other without a rewrite.

There is a different posture, and it is the right one most of the time: **one contract, two formats**. Same metadata shape, same call signature, same calling convention, same expectations about what the plugin produces. The plugin can be expressed in either of two source languages — say, the host language of the server and a sandbox-friendly language for the browser. Either source language compiles down to the same logical contract. A capability written in either format is loadable, in some appropriate way, in both runtimes.

This post is about why that uniformity matters more than it costs, what specifically you have to share to make it work, and where the design pressure should fall.

## What "the same contract" actually means

Two runtimes with the same plugin contract are not running the same code. They are running plugins that *agree on a small number of structural things*. The structural things are usually:

- **A metadata descriptor.** Every plugin exposes a small data structure that describes itself: name, description, parameter schema, any version or capability flags. The shape of this descriptor is the same in both runtimes. If a plugin is named `summarize_thread` in one place, it is named `summarize_thread` in the other; if its parameter schema requires a `thread_id` string and an optional `max_words` integer, both runtimes have the same parameter schema.
- **An action signature.** Every plugin exposes a callable named the same way, taking the same arguments in the same order. By convention I use `run(context, **kwargs)`. The host calls it the same way in both runtimes.
- **A context surface.** The plugin's only window into the host is the `context` object passed in. Both runtimes provide an object with the same set of method names, even though the implementations differ. If `context.fetch_record(id)` exists, it exists in both.

That is the whole contract. *Three things.* What makes it work is that those three things are shape-only — no shared code, no shared dependencies, no shared runtime state. They are an interface definition that two implementations both honor.

In one source language (say, Python), a plugin is a Python module exporting a `DESCRIPTOR` dict and a `run` function:

```python
DESCRIPTOR = {
    "name": "summarize_thread",
    "description": "Summarize a discussion thread in one paragraph.",
    "parameters": { "type": "object", "properties": { ... } }
}

def run(context, thread_id, max_words=100):
    thread = context.fetch_record(thread_id)
    return context.llm(f"Summarize in {max_words} words:\n{thread}")
```

In another source language (say, a sandbox-friendly Lisp), the same plugin is a file exporting the same things:

```lisp
(define DESCRIPTOR
  (dict :name "summarize_thread"
        :description "Summarize a discussion thread in one paragraph."
        :parameters (dict :type "object" :properties ...)))

(define (run context thread_id max_words)
  (let ((thread (context-fetch-record context thread_id)))
    (context-llm context
      (format "Summarize in ~a words:~n~a" max_words thread))))
```

Different syntax, different implementation, same contract. A host that knows how to load the first format invokes the plugin one way; a host that knows how to load the second format invokes it the other way. Both invocations end up calling `run` with `context` and `thread_id` and `max_words`, both end up returning a string. The metadata in both reads `name = "summarize_thread"`. The dispatcher routes by name. Plugins are interchangeable from the *host's* perspective even though their *source* differs.

## Why two source languages at all

The natural question is: if the contract is the same, why have two source languages? Why not pick one and require it everywhere?

The answer is that the two runtimes have different constraints, and the source languages reflect those constraints.

The server-side runtime can run anything the host language can run. It can call into databases, hit network APIs, run arbitrary subprocesses, write files, manage memory. In that environment, the natural plugin language is the host's own language, because there is no reason to introduce a new layer.

The browser-side runtime cannot run arbitrary native code. It runs in a sandbox. The plugin author cannot be trusted with arbitrary JavaScript, because untrusted JavaScript has access to the DOM, to local storage, to network calls in the user's name. So the plugin author writes in a *safe* language that the browser-side runtime evaluates inside its own sandbox — a small interpreted Lisp dialect, a constrained subset of JavaScript, a WASM module, a configuration-language-with-functions.

The choice of the second language is driven by isolation requirements, not by aesthetics. You pick something safe to evaluate, with a clean evaluator that you can audit. The contract floats above the language choice — what the plugin *exposes* is the same shape regardless of how the language renders it.

You could imagine other splits where the second language is chosen for other reasons. A native runtime and a constrained-edge-device runtime, where the second language is something with a smaller footprint. An interactive runtime and a batch runtime, where the second language is something easier to validate statically. The pattern is the same: pick a contract first, pick the languages to honor the contract, do not let the contract drift toward whichever language was easier to implement first.

## What the contract buys you

Three things, in ascending order of how much they tend to surprise teams.

**The same plugin runs in both surfaces.** A plugin written in the safe-evaluator format runs on the server-side runtime if the server-side runtime has an evaluator for the safe language (which is usually a hundred lines of code and worth shipping). A plugin written in the host language runs only on the server, but a plugin written in the safe language runs in either. So the safe language becomes the *portable* format, and the host language becomes the format you reach for when you need server-only capabilities. Most plugins end up in the safe format because most capabilities are portable; a few end up in the server-only format because they genuinely need server-only resources. Both populations coexist in one ecosystem.

**Authors do not have to pick a runtime.** When someone writes a plugin, they don't have to choose "is this for the server or the browser." They write to the contract; the runtime is an implementation detail. If they happen to use only safe-language features, the plugin happens to work in both places. The author is not forced to be aware of the deployment topology.

**The smaller surface becomes a credible host.** The most surprising effect. Before the contract, the browser was where you put UI; real work happened on the server. After the contract, the browser becomes a real plugin host. Real summarization, real classification, real generation can run there — *the same plugins as the server*. The browser is no longer a junior runtime; it is an equal one. This is what unlocks "this app does real work locally," and the impact on what users can do offline is large.

## The trap that breaks the pattern

There is a specific, recurring failure mode for "one contract, two formats" designs. *Letting the context surface drift.*

The metadata shape and the call signature are easy to keep aligned because they are explicit and small. The context surface is sneaky. As one runtime grows new features, its context tends to sprout new methods that the other runtime has not yet implemented. A plugin uses one of those methods. The plugin works in one runtime. It silently fails in the other. The dream of "the same plugin runs everywhere" turns into "the same plugin sort of runs everywhere if it doesn't touch any of the seventeen newer methods on the server's context that the browser's context hasn't gotten yet."

The fix is to make the context surface *deliberate*. Treat it as an interface with a version. Whenever you add a method to one runtime's context, decide explicitly whether it will be added to the other runtime's context too. If yes, add it to both, increment the interface version. If no, declare it as runtime-specific in the documentation, and have the plugin metadata declare which runtime versions it requires. Plugins that need server-only capabilities fail fast in the browser, with a clear message ("requires context interface v6 with `subprocess_run`; this runtime exposes v5").

Treating the context surface as an explicit interface is the discipline that keeps the contract honest. Without it, the two runtimes diverge in ways that are hard to detect and harder to undo.

## Argument validation belongs in the dispatcher

A small implementation detail that pays off: keep argument validation in the dispatcher, not in each plugin.

The dispatcher reads the metadata's parameter schema, validates the incoming arguments against it, and only then calls `run`. If the arguments are wrong, the dispatcher rejects the call and returns a structured error. The plugin author writes `run` assuming inputs are correct.

This frees plugin authors from having to defensively check every argument. It also makes argument errors uniform across runtimes — same error message, same shape, same place. And it lets you centralize the argument-validation logic in one place per runtime, rather than letting it leak into a hundred plugins where it will inevitably drift.

The same principle applies to error handling: let the dispatcher catch exceptions or interpreter errors and wrap them into a result structure. Plugins should be allowed to throw; the runtime decides how to surface that to callers.

## What you'd change after living with it

A short list of things I'd build differently into a future version of this pattern.

**Validate metadata at load time, not at call time.** A malformed metadata descriptor in the safe-language format only gets caught when someone tries to invoke that plugin. Validate it the moment the file is loaded. Surface errors next to the file that caused them.

**Publish a conformance test.** A plugin author cannot easily verify that their plugin works in all runtimes without writing test code. A small published harness that loads the plugin in each runtime, calls it with a fixture input, and checks the output gives the author the same green-or-red signal that a CI suite gives.

**Formalize the context interface with a version number.** As above, this is the place drift happens. Forcing the version into the plugin's metadata (`requires_context_version: 5`) makes incompatibilities loud.

**Disagree about errors, agree about success.** The shape of a successful return is exactly the same in both runtimes (a JSON-serializable value). The shape of an error is allowed to differ slightly because each runtime's error model differs. But the *envelope* — the wrapper around either result or error — is shared, so callers don't have to know which runtime they're talking to.

## The lesson, abstracted

When designing a plugin system that has to work in more than one runtime, the right unit of agreement is *the contract*, not *the source language*. A contract is small: a metadata shape, a call signature, a context interface. Source languages are large: parsers, interpreters, libraries, idioms.

If you let source languages be your unit of agreement, you will find that you cannot agree, and you will end up with two ecosystems that share a name. If you let the contract be your unit of agreement, you will find that two source languages are not actually a problem — they are an accommodation to two different sets of constraints, and the contract is what makes them feel like one ecosystem to authors.

One contract. Two formats. The plugin runs wherever the host knows how to load its format and honor its calls. Capabilities cross the runtime boundary because the contract crosses it first.

This is the architectural pattern most worth carrying forward into systems that have a server-and-edge split, an online-and-offline split, or any other "we need this code to live in two homes" situation. The contract is small enough to honor twice; the source languages are big enough that you'd rather not.

Make the contract the agreement. Let the languages be implementation details.
