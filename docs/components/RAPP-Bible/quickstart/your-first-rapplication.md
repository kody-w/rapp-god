# Build your first rapplication

A **rapplication** is a packaged bundle of agents + assets that solves a
single end-to-end use case. Where a single agent is a tool, a
rapplication is a workflow.

## What's in a rapplication

- A folder with one or more `*_agent.py` files.
- A `manifest.json` describing the rapplication (name, version, agents,
  assets, entry point).
- Optional assets — prompts, templates, sample data.

## The catalog

The public catalog of rapplications lives at
https://kody-w.github.io/RAPP_Store/. Browse, copy, modify.

Spec: [../SPEC/catalog/SPEC.md](../SPEC/catalog/SPEC.md).

## Build one

1. Make a folder: `mkdir my_rapplication && cd my_rapplication`.
2. Write a `manifest.json`:
   ```json
   {
     "name": "my_rapplication",
     "version": "0.1.0",
     "description": "What this does",
     "agents": ["main_agent.py", "helper_agent.py"],
     "entry": "main_agent.py"
   }
   ```
3. Drop your agent files alongside.
4. Test locally by copying the agent files into
   `~/.brainstem/agents/`.

## Submit to the catalog

The catalog is a GitHub repo: https://github.com/kody-w/RAPP_Store. Open
a PR that adds an entry to `index.json` pointing at your rapplication's
canonical source.

## Reference

- Catalog spec: [../SPEC/catalog/SPEC.md](../SPEC/catalog/SPEC.md)
- Kernel spec: [../SPEC/kernel/SPEC.md](../SPEC/kernel/SPEC.md)
- Registry (single-agent equivalent): [../SPEC/registry/SPEC.md](../SPEC/registry/SPEC.md)
