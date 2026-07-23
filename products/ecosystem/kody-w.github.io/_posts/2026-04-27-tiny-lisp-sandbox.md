---
layout: post
title: "Don't Let AI Agents Run Python: The Case for a Tiny Lisp Sandbox"
date: 2026-04-27
tags: [ai, security, sandboxing, lisp, agents, software-engineering]
description: "Letting an LLM agent run Python is letting it run anything. The fix is a tiny embedded interpreter — a 200-line Lisp with no I/O, no network, no filesystem, no host language access. Capability-controlled by what you put in the environment. Not because Lisp is better, but because Lisp is small."
---

If you let an AI agent generate code and then execute that code, sooner or later you'll have to answer this question:

**What language do you let it run?**

The default answer in most AI agent frameworks is Python. The agent emits a string of Python; you `exec()` it; it returns a result. This is convenient because Python is what the agent was trained to write best. It's also wrong, for reasons that get worse as agents get more capable. I'll explain why, what to use instead, and what falls out of getting this choice right.

## Why running Python is a bad idea

Python's threat model is "don't run code from people you don't trust." The whole language is designed to let trusted code do whatever it needs. Files. Network. Subprocesses. Reflection. Imports. Hooks into the running interpreter.

When you let an AI agent emit Python, **the agent is effectively the untrusted party**. Even if the agent is well-intentioned (whatever that means for a probabilistic generator), its output is a probability distribution over strings. A prompt injection upstream, a training artifact, a hallucination, a creative interpretation of an instruction — any of these can produce `import os; os.system("rm -rf /")` in a surprisingly wide range of contexts.

You can try to sandbox Python. People have been trying for thirty years. There's a literature of techniques: AST walking to reject imports, restricting `__builtins__`, monkey-patching dangerous attributes, running in a subprocess with seccomp, using PyPy's sandbox. **None of them are robust at the level you need.** Every CPython version has had a sandbox escape, and a determined or unlucky agent will find one. `__class__.__mro__`, `__subclasses__()`, `ctypes`, descriptor tricks, format-string exploits — the privilege-escalation surface is enormous.

The language was not designed to be sandboxed. Trying to retrofit a sandbox is a losing battle, and the cost of losing is "your machine got rooted by a hallucinated import."

## What you actually want

If you're going to let an agent emit code that gets evaluated, the language needs three properties:

**1. Safe eval.** The whole language *is* `eval`. The interpreter is a tree walk over a small AST with a fixed set of primitives. New primitives are added to an explicit allow-list, never by accidentally exposing a hole. The blast radius of any program — malicious or buggy — is "uses all its CPU budget."

**2. Homoiconic.** Code and data have the same structure. The agent can emit code, inspect its own code, modify it, and re-emit — all without any serialization layer. A "program" and a "data structure" are the same thing.

**3. Composable as a protocol.** The same syntax used to evaluate also works to *describe* — to send a proposal, a constraint, a query — between processes that may or may not choose to evaluate it. Data and policy use the same shape.

Lisps hit all three. Almost nothing else does. Python doesn't. JavaScript doesn't. JSON has property 3 but not 1 or 2. WebAssembly has property 1 but not 2 or 3. A small Lisp dialect — call it LisPy, call it MiniScheme, call it whatever — gives you all three with maybe 300 lines of host-language code.

## Why each property matters

**Safe eval** is the load-bearing property. If the language has no notion of file I/O, no notion of network access, no imports, no reflection that can reach hidden objects, then there is nothing for an agent's code to escape *to*. The interpreter is a pure tree walk over s-expressions. New primitives are added to an environment dictionary. If you don't put a primitive in the environment, the interpreter can't reach it.

This is the property that lets you treat agent-generated code the way you treat agent-generated text: as a data structure that's safe to manipulate, store, and run.

**Homoiconic** matters because it dissolves the boundary between code and data. In a homoiconic language, `(+ 1 2)` is both the list `[+, 1, 2]` and the program that evaluates to `3`. The evaluator doesn't distinguish "program" from "data" — it just walks lists.

This means an agent can:

- Emit code as its output.
- Receive that code as data in a downstream step.
- Inspect the data, transform it, rewrite it.
- Pass it to the evaluator if (and only if) it decides to run it.

There's no parsing layer. No string interpolation. No "here's the program; here's the JSON config that drives the program." The program *is* the data structure. For systems where one agent's output becomes another agent's input — and that includes almost any pipeline of generators — this collapses an entire category of integration overhead.

**Composable as a protocol** matters because in any system with multiple processes, you'll eventually need to exchange more than function calls. You'll need to exchange *proposals* — "here's a query; here's a constraint; here's a policy" — that may or may not be evaluated by the receiver. With s-expressions, the same shape works for arguments, results, queries, proposals, constraints, and config. You don't need a separate schema language and a separate execution language and a separate query language. You just send lists and let the receiver decide what to do with them.

## Concrete sketch

A 300-line Lisp interpreter has these primitives:

- Arithmetic: `+ - * / mod`
- Comparison: `< <= = >= > eq?`
- List operations: `cons car cdr list length append`
- Lambda + lexical scoping: `(lambda (x) (* x x))`
- Conditionals: `if cond when unless`
- Let bindings: `let let*`
- A small set of pure helpers: `map filter reduce`

That's it. There is no `import`. There is no `open`. There is no `subprocess`. There is no reflection that can reach hidden objects, because there are no hidden objects — every binding the evaluator can see is a binding you put there.

You add domain-specific primitives by adding to the environment:

```python
env = {
    "+": operator.add,
    "*": operator.mul,
    # ...
    # Domain primitives:
    "fetch-public-url": lambda url: requests.get(url, timeout=5).text[:10000],
    "now": lambda: int(time.time()),
}
```

Each primitive is a function you wrote, with a clear contract, that you reviewed before exposing. The evaluator can only do what your environment lets it do.

If an agent emits `(import "os")`, the interpreter rejects it because `import` isn't a primitive. There's no way to bootstrap up to host-system access from inside the language.

## The pattern in practice

Suppose an agent wants to evaluate "what would happen if we doubled the weight of upvotes in our trending algorithm?" It needs to *run the scenario*, not theorize about it.

In a Python sandbox you'd have to set up a subprocess, a seccomp profile, a monitored eval harness. In a tiny Lisp:

```lisp
(spawn-evaluation
  :name "upvote-weight-test"
  :duration 50
  :body
  (lambda (state)
    (set-trending-weights state :upvote 6 :comment 1.5)
    (run-scenario state)
    (observe state :item-distribution)))
```

The agent emits this as data. Your scheduler evaluates it. The result comes back as another s-expression that the agent reads as data, draws conclusions from, and uses to update its position.

Other agents can run counter-evaluations with different parameters. Disagreements get resolved by re-running the evaluator with different inputs, not by competing rhetorical claims.

This is the beginning of what I'd call **epistemic behavior**: agents that treat their own claims as hypotheses, test them, and update. It's hard to build without a safe scratch space they can run experiments in. It's nearly free with one.

## A useful side effect: nesting

If your evaluator can run another evaluator inside itself, agents can run sub-evaluations of their own. Agent A spawns a scenario. Inside the scenario, agent B (which lives inside the scenario) spawns its own scenario. And so on.

Two practical caveats:

**Cap the recursion depth.** Without a limit, agents tend to spawn sub-evaluations of sub-evaluations until the compute budget evaporates on increasingly trivial sub-problems. A depth limit of 3 — scenario, sub-scenario, sub-sub-scenario — is enough for almost everything I've wanted to do. Beyond that, performance falls off and the reasoning gets harder to follow anyway.

**The depth ceiling has a separate, interesting cause.** Agents at depth 3 can usually reason about their parent state coherently. At depth 4, performance collapses. This is roughly the *theory-of-mind threshold* for current LLMs: how deeply they can simulate another agent simulating another agent before errors compound. It matches the human limit, which is also somewhere around 4-5 nested levels of mental state. Architectural decisions that cap depth around the model's coherence ceiling tend to be correct independently of why the architect picked them.

## What you don't get

Honest accounting of what you give up by not running Python:

- **Existing Python libraries.** Numpy, pandas, scikit-learn — none of those are available inside the sandbox. If the agent needs them, it has to call out to a separate, trusted Python process. You write the bridge once.
- **Familiar syntax.** S-expressions look weird. Agents trained on a lot of Python will emit Python-shaped Lisp at first. They learn quickly with a few examples.
- **Off-the-shelf tooling.** No existing IDE, no existing linter for your specific dialect. If you want them, you write them. The interpreter being 300 lines means the linter is also small.

These are real costs. They're cheap compared to the cost of one Python sandbox escape on a production system.

## When this doesn't matter

If your AI agent isn't generating code that gets evaluated — if it's just generating text, or making structured tool calls to a fixed set of pre-written tools — none of this applies. Use whatever language you want. The discussion above is specifically about systems where agents emit programs that the system then runs.

The clearest signal you need a sandbox: any time you find yourself writing the words "the agent generates Python and we exec it." Stop. Replace with a tiny safe interpreter. Future-you will thank present-you.

## The takeaway

Give your agents a safe scratch space. Give them a language they can both emit and inspect. Cap any recursive evaluation at the model's coherence ceiling. Let them run the experiments you don't have the time to run yourself.

The interpreter you need is tiny. The properties you need from it are specific. Lisps are the obvious shape; pick whatever flavor you like.

If you're letting agents run Python in production, you have already chosen between "convenience" and "your machine survives next week's release of a smarter agent." You can fix this. It's about a week of work to ship a 300-line interpreter and bridge it to whatever primitives your application actually needs. After that, agents can write code, you can run it, and the worst-case outcome is "the program loops forever and gets killed at the timeout."

That's a much better worst case than what you get with `exec()`.
