# Bill Whalen's Agent Team

A planted RAPP neighborhood — **the neighborhood IS the workflow**. Anyone with `brainstem.py` running locally can join, pull every agent this team ships, and run the whole workflow on their own machine. No cloud, no Azure, no auth — just local first.

> **Hero use case:** portable workflow shareability. Your team's working agents become a single-URL drop-in for any other RAPP brainstem.

---

## How to join (3 steps)

### 1. Get a brainstem running locally

```bash
curl -fsSL https://kody-w.github.io/RAPP/installer/install.sh | bash
```

That's the whole install. It mints your rappid (your operator identity), starts a brainstem on `localhost:7071`, and opens chat in your browser.

(Already have a brainstem from before? Skip this step — you're already set.)

### 2. Tell your brainstem to join this neighborhood

In chat, type:

```
join kody-w/billwhalen-agent-team
```

The brainstem will:
- Verify this gate is a real RAPP neighborhood
- Mint your rappid if it doesn't exist yet (idempotent — does nothing if it does)
- Hot-load every agent in this neighborhood's [`rar/index.json`](./rar/index.json) into your local `agents/` directory (sha256-verified, additive only — never clobbers your existing agents)
- Record the subscription at `~/.brainstem/neighborhoods.json`

### 3. Run the workflow

Every agent this neighborhood ships is now a tool your local brainstem can call. Ask in chat:

```
what agents do I have from billwhalen-agent-team?
```

Then run any of them. They run on your machine, against your local data, with no roundtrip to anyone else's tenant.

---

## Contributing an agent to the neighborhood

Got a single-file `*_agent.py` that helps Bill's team? Three options, simplest first:

1. **Open an Issue** with the agent code in the body. A maintainer reviews and adds it to `rar/index.json`.
2. **Drop it in `submissions/`** via PR. CI validates the agent contract; merge ratifies and updates `rar/index.json`.
3. **Plant your own gate** alongside this one (`plant_seed_agent` from kody-w/RAPP) and federate. Your gate becomes a sibling neighborhood in the trust web.

---

## What this neighborhood is for

Bill Whalen and his team build with [`agent-team-starter-kit`](https://github.com/billwhalenmsft/agent-team-starter-kit) — 14 specialized AI personas, GitHub Issues as work queue, Azure Functions + OpenAI. This RAPP neighborhood is where those agents become **portable** — single `.py` files that drop into any teammate's local brainstem with no setup. The Copilot Studio harness path (T3) is the deployment target; the local brainstem (T1) is the iteration loop.

---

## Identity

- **Rappid:** `rappid:@kody-w/billwhalen-agent-team:83942d3a707bb8b39cdaff36aa6c258d6e2abd7aaf58b74d725b6c5dacbc0227`
- **Kind:** `neighborhood`
- **Planted at:** 2026-05-10T20:36:49Z
- **Parent:** [kody-w/RAPP](https://github.com/kody-w/RAPP)
- **License:** CC0-1.0 for submissions where applicable; spec text MIT (per parent)

---

## Files in this gate

| File | What it is |
|------|------------|
| [`rappid.json`](./rappid.json) | This gate's permanent identity |
| [`neighborhood.json`](./neighborhood.json) | Schema-versioned gate metadata |
| [`rar/index.json`](./rar/index.json) | The shareable workflow — agents, organs, cards |
| [`members.json`](./members.json) | Operators who've joined |
| [`soul.md`](./soul.md) | Voice / disposition for any AI inhabiting this gate |
| [`holo.md`](./holo.md), [`holo.svg`](./holo.svg), [`holo-qr.svg`](./holo-qr.svg) | Holocard (identity proof + summon QR) |
| [`card.json`](./card.json) | Tradeable card-shape per `rappcards/1.1.2` |
| [`facets.json`](./facets.json) | Capability declarations |
| [`specs/`](./specs/) | Bundled contracts so this gate is self-sufficient |
| [`submissions/`](./submissions/), [`votes/`](./votes/) | PR-mediated growth surfaces |
