# Install the RAPP brainstem

The brainstem is the local-first server that hosts your agents. One
process, one port, drop-in `*_agent.py` files. This is **step zero** of the
zero → running → planting → joining → sharing path.

## One-liner (the canonical path)

```bash
curl -fsSL https://kody-w.github.io/RAPP/installer/install.sh | bash
```

That URL shape is sacred (CONSTITUTION Art. V) — it is the single front door
every operator uses, including for bug-fix updates. The install one-liner:

- clones the kernel, sets up the agent directory, and prints the start command;
- **mints your personal rappid once** (the Eternity form, stored at
  `~/.brainstem/rappid.json`) and records a `birth` event in `bonds.json`;
- on a re-run, detects a remote version upgrade and runs the **bond cycle**
  (🥚 egg the organism → 🌐 overlay the new kernel → 🐣 hatch the egg back),
  preserving your rappid + soul + custom agents + memory + secrets.

> Windows: `install.ps1` / `install.cmd` from the same `installer/` path.

## What you get

After install, the brainstem listens on `http://localhost:7071` by default,
and you have a digital organism with a persistent identity:

- `~/.brainstem/rappid.json` — your organism identity (Eternity rappid).
- `~/.brainstem/bonds.json` — your append-only lineage log.
- `~/.brainstem/agents/` — drop `*_agent.py` files here; they hot-load.

## Verify

```bash
curl -X POST http://localhost:7071/chat \
  -H "Content-Type: application/json" \
  -d '{"user_input": "hello", "user_guid": "test"}'
```

A JSON response means you're up.

## Drop in the one agent

The single most useful thing to install first is **the one agent** — drop
`@rapp/rapp` (`rapp_agent.py`) from [RAR](https://github.com/kody-w/RAR) into
`~/.brainstem/agents/`. Now the whole ecosystem is reachable through natural
language: *"who am I"*, *"what exists"*, *"join the gate at owner/repo"*,
*"install the twin agent"*. See [`THE_ONE_AGENT.md`](../THE_ONE_AGENT.md).

## Next on the path

1. [Drop in an agent](drop-in-an-agent.md) — the unit of extension.
2. [Build your first twin](your-first-twin.md) — plant a door with its own rappid.
3. [Join a neighborhood and share](join-and-share.md) — federate with others.
4. [Build your first rapplication](your-first-rapplication.md) — a graduated rapp.

## Reference

- Install one-liner: `https://kody-w.github.io/RAPP/installer/install.sh`
- Kernel source: https://github.com/kody-w/RAPP
- Constitution (read this): [../SPEC/kernel/CONSTITUTION.md](../SPEC/kernel/CONSTITUTION.md)
- The network-participation runbook: [the six steps to citizenship](join-and-share.md)
