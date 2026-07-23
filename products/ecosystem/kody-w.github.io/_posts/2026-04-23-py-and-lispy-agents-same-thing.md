---
layout: post
title: "Two file extensions, one plugin contract"
date: 2026-04-23
tags: [ai, agents, plugin-architecture, software-design]
description: "Most plugin systems fail because the contract is too big. Six lifecycle hooks, a config schema, dependency declarations, registration ceremony. Authors get tired before they finish a hello-world. The plugin systems that succeed have contracts that fit on a tweet — export two things, the host globs the folder. Here is what that minimum looks like, why two languages can implement the same contract, and what minimal contracts buy you in the long run."
---

Plugin systems are how a small piece of software grows into a large ecosystem. They are also where most ambitious software projects accidentally ossify, because the contract designers were trying so hard to be careful that they made the contract impossible to satisfy.

I have been building a plugin system for AI agents and have settled on a contract so small that two completely different programming languages can implement it without sharing any code. The contract is "export two things from your file." The host globs the folder. There are no lifecycle hooks. There is no config file. There is no registration ceremony.

This post is what that contract looks like, why two languages share it, and what minimal contracts buy you in the long run.

## The contract

Every agent, regardless of file extension, exports two items:

A metadata dictionary in a known schema (in my case, OpenAI's function-calling schema, since the agents are called by language models):

```python
AGENT = {
    "name": "get_weather",
    "description": "Return weather for a city",
    "parameters": {
        "type": "object",
        "properties": {"city": {"type": "string"}},
        "required": ["city"]
    }
}
```

And a function that does the work, taking a context object and the dictionary's parameters as keyword arguments:

```python
def run(context, city):
    return {"temperature": 72, "conditions": "sunny"}
```

That is the entire contract. Two exports. A name and a description say what the agent is. A parameters schema says what arguments it accepts. A `run` function does the thing. Nothing else.

The same contract in a Lisp dialect — for the same agent system, but a different runtime — looks like:

```lisp
(def AGENT {
  :name "get_weather"
  :description "Return weather for a city"
  :parameters {
    :type "object"
    :properties {:city {:type "string"}}
    :required ["city"]}})

(defn run [context city]
  {:temperature 72 :conditions "sunny"})
```

Different syntax. Same shape. The same metadata dictionary, expressed in the language's native data structures. The same function signature, expressed in the language's native function syntax. Either implementation is a valid agent.

## Hot loading is `glob`

Both runtimes find their agents the same way: glob a folder, load every file, extract the two exports.

In the Python runtime, that is one short loop using `importlib`. In the Lisp runtime — implemented in JavaScript, running in a browser — it is the same idea: fetch the directory listing, fetch each file, evaluate it in a sandbox, register the result. The runtimes are different; the discovery model is identical.

What this means in practice: adding a new agent to the system is dropping a file into a folder. There is no registration step. No config edit. No restart, in many cases, since the runtime can re-glob on demand. Removing an agent is deleting the file.

This is the property that turns a plugin system from a feature into an ecosystem. When the cost of contributing an agent is "one file, one drop, one pull request," people contribute agents. When the cost is "register here, register there, declare your dependencies, follow the lifecycle protocol, run the build script," they don't. The friction floor sets the contribution ceiling.

## Why two languages

Picking one language would be simpler. It is not the right answer when two different *runtime contexts* have different constraints.

The Python runtime is server-side. Trusted code. Access to the filesystem, the network, an LLM backend, the full Python standard library. You write Python agents for things that have to actually go out and do work — fetch APIs, query databases, generate content, drive simulations. You need power. You can spend it because the code is yours and you are running it on your machine.

The Lisp runtime is client-side. It runs in a user's browser. The agents are user-extensible by design — anyone can drop a `.lispy` file into the system and it loads. *Anyone*. Including hostile anyone. A power-fully-equivalent JavaScript runtime would let those agents do anything: read other browser data, exfiltrate to a server, mine cryptocurrency. So the runtime is a sandbox. Pure computation. No I/O. No imports. No network except through explicit bridge functions. A Lisp dialect is the right fit because it is small, easy to interpret in a controlled environment, and naturally functional.

One language is maximally powerful. The other is maximally safe. Both satisfy the same two-export contract. The contract is the lingua franca; the languages are implementations of it suited to where they run.

Picking one language would force a bad trade. Python only: no safe way for users to ship agents that run in their own browsers; every browser-side agent has to be reviewed by the platform. Lisp only: no way for an agent to talk to the open internet; the server runtime is crippled. Two languages let each context be right-sized.

## Why the contract is minimal

Every piece added to the agent contract becomes a per-agent tax. An agent author does not want to think about your logging framework, your metrics library, your dependency injection pattern, your lifecycle hooks. They want to write their function and ship.

Compare the two-line contract above to a typical "plugin framework" interface. A typical interface has:

- Lifecycle hooks: `init`, `cleanup`, `pre_call`, `post_call`, `on_error`, `on_reload`. Each must be implemented or stubbed.
- A config file (YAML, JSON, TOML — pick one, then write a schema, then write a parser, then write validators).
- Dependency declarations (which packages, which versions, with which platform constraints).
- A versioning scheme (so the host can decide which agents are compatible with which hosts).
- A registration step (so the host knows the agent exists).
- A teardown protocol (so the host can unload the agent cleanly).

The plugin author has to think about all of those before they can write the function that does the actual work. By the time they finish reading the docs, they are tired. They write a hello-world. They never write a second plugin.

A two-line contract has none of this. The plugin author opens their editor, writes a metadata dict and a function, drops the file. The agent works. They get to the actual problem they wanted to solve in the first ten minutes.

The cost of this minimalism is real. Without lifecycle hooks, the host can't tell an agent that it is about to be unloaded. Without dependency declarations, the host can't auto-install missing packages. Without versioning, the host can't reject incompatible plugins. These are real losses.

The losses are worth eating, because the alternative is a plugin system with a ten-plugin ecosystem instead of a hundred-plugin ecosystem. A small contract gets you many plugins, most of which are simple and a few of which are excellent. A large contract gets you few plugins, most of which were written by the host's team because nobody else had the patience.

## The plugin system is the *pipe*, not the language

The deeper insight is that the contract — not the language — is what makes a plugin system. A plugin system is *not* "you can write code in language X to extend my app." A plugin system is "there is a shape you must implement, and anything that implements the shape becomes an extension." The shape is language-agnostic.

For the agent system, the shape is `AGENT` metadata dict plus `run(context, **kwargs)` function. Today it is implemented in Python and a Lisp dialect. Tomorrow it could be JavaScript, Lua, WASM, Go. The host runtime grows; the contract does not change. Agents written in any language that can express a dictionary and a function become valid contributions.

This is how Unix handled the plugin problem for decades. A program is anything with a `main()` and standard input/output. What language you wrote it in was your problem. The shell did not care. `awk` plugged into the same pipelines as C. The pipe — `stdin`, `stdout`, `argv`, exit codes — was the contract. The languages were arbitrary.

Most modern plugin systems forget this lesson and tightly couple to their host language. A "plugin" is an instance of the host's class hierarchy, configured via the host's reflection mechanisms, deployed via the host's package manager. This works for one language. It rules out everyone else from day one. The shell-and-pipe lesson is that *the universal interface is the small one*.

## Portability falls out

Because the contract is small, agents are portable. A Python agent written for the server runtime can be mechanically translated to the Lisp runtime by syntax conversion alone — there is no architectural refactoring, because the shape was the same on both sides. If a third runtime appears (a Rust sandbox, a WASM bundle, a different language ecosystem), every existing agent ports over by syntactic translation.

Portability is the property you get for free when your contract is shape-based instead of host-feature-based. You do not have to think about portability when designing the system. You have to think about *not adding host-specific features to the contract*. The negative discipline yields the positive property.

## The standalone case

The most extreme version of "minimal contract" is a single-file agent that runs entirely without the plugin host. One file, zero dependencies, runs in any installed runtime of the language. It implements the same contract as any plugin agent and includes its own minimal harness. You can pull the file down, set whatever credentials it needs, and run it directly.

That file is the existence proof that the contract is correct. If an agent can be a single file with no host dependencies, the abstraction is clean. If an agent requires the host to be present in any meaningful way, the abstraction has leaks; the contract is doing more work than it appears to, because some of the plugin's behavior depends on the host's environment in unstated ways.

The standalone-file test is a useful design constraint to apply during contract design: *can a plugin be implemented as a single file with zero host dependencies?* If the answer is no, the contract is too big.

## The lesson

When you are designing a plugin system, ask what the *minimum* an author has to do is. "Export two things" is near the floor. Hot-load by globbing a folder is near the floor. Don't require a registration step. Don't require a config file. Don't ship a lifecycle hook the plugin must implement. The more ceremony you demand, the fewer plugins you will get, and the more fragile the ones you do get will be.

The agent ecosystem I run has roughly 40 agents across the two runtimes. Most are under 100 lines. That density of capability per line of code is what small contracts buy you. A larger contract would mean fewer agents, longer files, more host knowledge encoded in each agent, and harder porting between runtimes.

Two file extensions. One contract. Two languages. Many agents. No registration. No config. No ceremony. The contract fits in a sentence; the system grows because of it. That is the trade.
