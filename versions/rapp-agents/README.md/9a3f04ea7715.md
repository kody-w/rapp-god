# rapp-agents

**A RAPP Agent Stack** — drop-in `agent.py` files that hot-load into any local RAPP brainstem.

## What this is

A collection of single-file Python agents that work inside any standard [RAPP brainstem](https://github.com/kody-w/rapp-installer). Each agent is fully self-contained — drop it into your brainstem's `agents/` directory and it becomes available to the LLM at the next request. No restart. No build step.

This repo is the **public** stack. There is also a private companion (`~/rapp-agents-private/`) for sensitive or personal agents.

## How to use the whole stack (the magic drop-in)

Download just one file — `agents/rapp_loader_agent.py` — and drop it into your brainstem's `agents/` directory. That loader is the front door for everything else in this repo. From a chat with your brainstem:

> "What agents do I have available?" → the loader catalogs this repo
> "Load Scout" → the loader symlinks `scout_agent.py` into your workspace
> "Load the pentester stack" → the loader activates a named bundle
> "Unload Scout" → reverses it

The brainstem reloads agents on every request, so changes take effect immediately — no restart needed.

## How to use a single agent

If you only want one specific agent (and don't need the loader), just download that one `*_agent.py` file from `agents/` and drop it into your brainstem's `agents/` directory.

## Repo layout

```
rapp-agents/
├── agents/                  drop-in agent files
│   ├── basic_agent.py       base class (canonical copy)
│   ├── rapp_loader_agent.py the loader — the front door for this stack
│   ├── scout_agent.py       discover what twins to create
│   ├── double_down_agent.py russian-doll prompt amplifier
│   ├── twin_pulse_agent.py  DOG→GOD assimilator (rapp-twin-pulse/1.0)
│   └── ...
├── tests/                   pytest cases (pytest -v from this dir)
├── stacks/                  named bundles (JSON): {name, description, agents:[]}
└── README.md
```

## What's a "stack"?

A `stacks/*.json` file defines a named bundle of agents that work together. Example:

```json
{
  "name": "twin-builder",
  "description": "Discover twins, recommend kinds, double down on the best ideas",
  "agents": ["Scout", "DoubleDown"]
}
```

Then in chat: *"Load the twin-builder stack"* → loader activates every agent in the bundle.

## Companion: `~/rapp-agents-private/`

The private repo is the same shape, intended for personal or sensitive agents you don't want public. The loader walks both repos by default.

## Philosophy

The sacred RAPP brainstem repo (`kody-w/rapp-installer`) is the engine. This repo is the *content* — agents you author, share, and remix without ever touching the kernel.

MIT licensed. Pull requests welcome for new public agents.
