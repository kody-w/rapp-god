---
layout: post
title: "Drop a file in a folder, gain a capability"
date: 2025-09-24
tags: [engineering, plugins, architecture, agents]
description: "The file is the plugin. The folder is the registry. Git is the package manager. Here is the smallest possible plugin protocol, why it works, and what it gives up to be that small."
---

There is a class of system that wants to be open-ended. You start it with some capabilities; over time, you (or your users) want to add more. The traditional answer is a plugin system — a manifest format, a registration step, a packaging format, an SDK, a marketplace, a versioning scheme, a permissions model. These quickly get bigger than the system they were attached to. Most of them get unused.

There is a much smaller answer that I keep finding works better than its critics expect. *The file is the plugin. The folder is the registry. Drop a file in the folder; the system gains the capability immediately.* That is the entire protocol. No manifest. No packaging. No SDK. No registration. Just a folder you scan and a convention for what files in it look like.

This post is about the shape of that protocol, the specific reasons it scales further than people predict, and the cost it pays for being so small. It is the right pattern for a remarkable number of systems — anything where the set of capabilities is expected to grow organically and most of the growth is going to come from people you have never met.

## The contract, in two parts

Each plugin is a single file, with a predictable name, exporting two things.

The first export is **metadata**: enough to describe the plugin to whatever needs to know it exists. A name, a description, a parameter schema, possibly a version. The shape can be borrowed from somewhere standard if you want; OpenAI's function-calling format works well, because it forces a JSON Schema for inputs and a free-text description for the why. In Python, you can express it as a module-level dictionary:

```python
DESCRIPTOR = {
    "name": "summarize_thread",
    "description": "Summarize a discussion thread in one paragraph.",
    "parameters": {
        "type": "object",
        "properties": {
            "thread_id": {"type": "string"},
            "max_words": {"type": "integer", "default": 100}
        },
        "required": ["thread_id"]
    }
}
```

The second export is the **action**: a function the host calls to actually run the plugin. By convention, give it a fixed name (`run`, `execute`, `handle` — pick one and stick with it). Give it a fixed signature: a context object with whatever the plugin can call into the host through, plus keyword arguments matching the metadata's parameter schema.

```python
def run(context, thread_id, max_words=100):
    thread = context.fetch_thread(thread_id)
    return context.llm(f"Summarize in {max_words} words:\n{thread}")
```

That is the whole contract. One file. Two exports. The host scans a folder, imports each file, reads the metadata, registers the action under the metadata's `name`. When something asks the host to do `summarize_thread`, the host validates arguments against the schema, calls `run` with a context plus the validated args, returns the result.

There is no plugin SDK. There is no plugin framework. There is no plugin API. **The protocol *is* the file format.** Anyone with a text editor and a copy of the convention can write one.

## The hot-loading move

The folder is scanned on startup, but it can also be scanned on a schedule, on a filesystem-watch event, or in response to an explicit "rescan" call. New file in the folder? It is discovered the next time the host looks. Removed file? It is gone the next time the host looks. The filesystem is the registry, and the OS already keeps the registry consistent for you.

```python
import importlib, glob, pathlib

registry = {}

def rescan(folder):
    for path in glob.glob(str(pathlib.Path(folder) / "*_plugin.py")):
        module = importlib.import_module(path_to_module(path))
        registry[module.DESCRIPTOR["name"]] = module
```

Twelve lines of plumbing. It is so unobtrusive that the host barely notices the plugin layer exists. Most of the host's complexity is in things other than plugin loading — and that is the right ratio.

## What the convention gets right

The reason this pattern keeps quietly outperforming heavier alternatives is that it gets four things right at once.

**Git is the package manager.** Want to ship a plugin? Push the file to a public repo. Want to install it? Download the file into the folder. Want to update it? Replace the file. Want to uninstall it? Delete it. There is no install script, no dependency resolution, no version-conflict negotiation. The unit of distribution is one file. The unit of versioning is the file's history in whatever repo it lives in. The unit of trust is "did you read the file before you put it in your folder."

```bash
curl -fsSL https://example.com/some_plugin.py -o plugins/some_plugin.py
```

That is install. There is no uninstaller because `rm` is the uninstaller.

**The folder is the manifest.** If you want to know what plugins are loaded, you list the folder. If you want to know whether a plugin is installed, you check whether the file is there. If you want to ship a configuration of plugins to a new machine, you copy the folder. The state of the system is in the filesystem. Nothing in a database, nothing in a registry server, nothing in a manifest YAML. Where things are is *where they are*.

**No central authority.** There is no plugin store you have to be approved for. There is no review queue that gates publication. There is no central namespace that anyone has to manage. People you have never met can author plugins for your system without asking you. They can host the files anywhere — their own GitHub, an internal mirror, a USB drive. This is what makes the ecosystem grow organically, because the threshold for participation is "can you write a file."

**Composability is automatic.** Because every plugin shares the same metadata schema and the same call signature, the host can chain them without knowing anything about specific plugins. Take a list of plugin names, validate the arguments for each, run them in sequence, pipe the output of one into the input of the next. An LLM can read the metadata of every available plugin and decide, in real time, which sequence to invoke. The composability falls out of the convention; you do not have to design it.

## What it gives up

The small protocol has costs. It is worth being honest about them.

**No dependency management.** A plugin file with no explicit dependencies is a plugin file that has to do its work with whatever the host already provides. If you want to use a third-party library, you have to add it to the host's dependencies separately, or vendor the relevant code into the plugin itself. The strongest version of this protocol is "plugin uses standard library only," because then the plugin really is just a file. The weaker, more practical version is "plugin uses host's already-installed libraries," which works but means the host has to maintain a known-stable surface of libraries.

**No isolation.** A plugin runs in the same process as the host, with the host's permissions. A malicious plugin can do whatever the host can do. This is fine for systems where the operator chooses every plugin individually and trusts what they install. It is not fine for systems where untrusted parties can submit plugins. If you need isolation, you need a sandbox — and the sandbox is a real piece of work, the kind of work that the small protocol was trying to avoid.

**No versioning except via the file's history.** If you depend on a specific version of a plugin, you pin a specific commit hash of the file. There is no semver, no release notes, no upgrade tooling. For most plugins this is fine; for a few it is genuinely limiting.

**Discovery only inside what you point at.** The host knows about the plugins in the folder. It does not know about plugins out in the world. Discovery — "what plugins exist for my system" — is a separate problem. The usual answer is a public registry that lists URL+description pairs, but the registry is *out of band* from the plugin protocol itself; it does not need to be a piece of the protocol.

For systems where these costs are tolerable — and there are more of them than people initially think — the protocol is appropriate.

## Where it shines

Three patterns where I keep returning to this protocol.

**Internal tooling that must accept community contributions.** A static analyzer where teams want to add their own checks. A migration runner where each project ships its own steps. A linter for a domain-specific language. The set of checks/steps/rules has to grow without any central coordinator. A folder of files solves this directly. People drop in a check; the tool runs the check.

**Capability-extending agents.** Anything LLM-driven where the agent has a finite set of tools and you want users to be able to add more. The metadata format is exactly what the LLM consumes. The folder is exactly what the host needs to walk. The plugin author writes one file and doesn't have to know anything about the agent's prompting strategy.

**Cross-runtime capabilities with a shared contract.** When the same protocol runs in two different environments — server and browser, native and embedded, Python and a sandboxed scripting language — the small contract is what lets the same plugins work in both. You write the plugin once; the host that loads it picks how to invoke it. The contract is portable in a way that an SDK is not.

## The lesson, generalized

The instinct, when designing a plugin system, is to provide rails. SDKs, scaffolders, marketplaces, validators, sandboxes, signed packages. Each of these has a real reason to exist; some plugin systems genuinely need all of them. *Most don't.* And the bigger your plugin infrastructure, the more friction you put in the way of someone shipping a plugin — usually long before the friction has paid for itself in safety or convenience.

If you do not have a specific reason for the rails, **start with the smallest possible protocol** — one file in a folder — and let the costs of its limits become visible before you add complexity. You will find, more often than not, that the plugin ecosystem has grown faster than you expected, that your users have been doing fine without the rails, and that the "missing" features were never blocking anything.

A folder of files. A scan loop. A two-export contract. The unit of distribution is the plugin itself. The unit of trust is reading the code. The unit of versioning is the commit hash of the file.

Drop a file in a folder. The system gains a capability. That is the whole protocol, and it scales further than its size suggests.
