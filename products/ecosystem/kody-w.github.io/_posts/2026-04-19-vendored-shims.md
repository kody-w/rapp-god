---
layout: post
title: "Vendored shims: making installed agents work without their parent"
date: 2025-10-30
tags: [python, packaging, agents, runtimes]
---

Suppose you ship a small runtime that loads other people's Python files at runtime. The files were authored against a richer parent library — your full agent toolkit, say — and every one of them starts with:

```python
from agents.basic_agent import BasicAgent
```

That import doesn't naturally work inside the small runtime's directory layout. There's no `agents/basic_agent.py` next to its source. The full toolkit has one in its tree, but the small runtime is its own thing — installable independently, with no dependency on the toolkit source.

We could:

1. **Require the full toolkit to be installed too.** Bad. The whole point of the small runtime being stdlib-only is that it doesn't drag dependencies. Forcing a toolkit install just moves the problem.
2. **Rewrite the import in every agent file at deploy time.** Bad. Modifying user code is a dangerous default — you'd have to be careful not to break anything else, and you've changed the bytes from what the user pushed.
3. **Vendor a minimal `BasicAgent` next to the runtime.** Yes. This is the right answer.

The runtime writes a six-line `BasicAgent` shim alongside its source on first load:

```python
class BasicAgent:
    def __init__(self, name=None, metadata=None):
        if name is not None: self.name = name
        elif not hasattr(self, 'name'): self.name = 'BasicAgent'
        if metadata is not None: self.metadata = metadata
        elif not hasattr(self, 'metadata'):
            self.metadata = {'name': self.name, 'description': '',
                             'parameters': {'type': 'object', 'properties': {}}}
    def perform(self, **kwargs):
        return 'Not implemented.'
    def system_context(self):
        return None
    def to_tool(self):
        return {'type': 'function', 'function': {
            'name': self.name,
            'description': self.metadata.get('description', ''),
            'parameters': self.metadata.get('parameters', {'type': 'object', 'properties': {}})}}
```

The shim is written by the runtime on first agent load if it doesn't already exist. Then the runtime registers it as `agents.basic_agent` in `sys.modules`:

```python
if "agents" not in sys.modules:
    pkg = type(sys)("agents")
    pkg.__path__ = []  # marks it as a namespace package
    sys.modules["agents"] = pkg
if "agents.basic_agent" not in sys.modules:
    spec = importlib.util.spec_from_file_location("agents.basic_agent", str(vendored_basic))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sys.modules["agents.basic_agent"] = mod
```

When the deployed agent does `from agents.basic_agent import BasicAgent`, Python's import machinery finds `agents.basic_agent` already in `sys.modules` and uses it. The agent file imports successfully. It doesn't know — or care — that the `BasicAgent` it got is the vendored shim and not the full toolkit's version.

**Why a six-line BasicAgent is enough:**

`BasicAgent` is intentionally minimal. The contract is `name`, `metadata`, `perform()`, `system_context()`, `to_tool()`. Nothing more. The base class is kept tiny exactly so it's vendorable. If the base class grew dependencies (logging frameworks, plugin registries, decorators), shimming it would mean shipping all of those too. The shim works because the contract works.

**The lesson:**

When you ship a runtime that loads other people's code, decide whether the shared base class is yours to define. If yes, keep it small enough to vendor. If you can't keep it small, you've made every consumer of your runtime dependent on the full version of your library — and you've lost the ability to ship lightweight runtimes.

`BasicAgent` is a contract masquerading as a class. The class is for type-checking and IDE autocomplete; the contract is "extends this thing, has these methods." Six lines of class is enough to encode the contract. Anything more is for the developer's convenience, and that goes in the toolkit, not the base class.

The small runtime is 300 lines. The vendored BasicAgent is 6 lines. Together they let you deploy any agent — written against any compatible runtime — without dragging the originating runtime along for the ride. That's the value of keeping your contracts narrow.