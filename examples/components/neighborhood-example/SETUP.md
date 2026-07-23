# Setup

`EggHatcher` is one agent that handles every setup scenario. Drag the `.py` into your brainstem's `agents/` directory, send one chat — done.

## Three modes

### Mode 1: Sneakernet (`from_egg`)

You received `egg_hatcher_agent.py` + a `<name>.egg` via USB / AirDrop / scp / postal mail. No internet required.

```
EggHatcher from_egg=/path/to/neighborhood-example.egg
```

The agent unpacks, sha256-verifies, installs all workflow agents, mints your rappid, mints your per-handle workspace + local data dir, records the subscription. ONE chat, complete setup.

### Mode 2: Online (`from_repo`)

You have GitHub access + are a collaborator on this neighborhood's repo.

```
EggHatcher from_repo=kody-w/neighborhood-example
```

Same end state as Mode 1, but pulls from GitHub via `gh` instead of from a local egg.

### Mode 3: Pack to share (`pack_egg`)

You want to ship YOUR current workspace to a peer.

```
EggHatcher pack_egg=true
```

Produces `~/brainstem-eggs/neighborhood-example-<timestamp>.egg`. Pair it with a copy of `egg_hatcher_agent.py` and send both to anyone — they can hatch it on their machine with no internet.

---

## Prerequisite: a brainstem running locally

If you don't have one yet:

- **With internet:** `curl -fsSL https://kody-w.github.io/RAPP/installer/install.sh | bash`
- **Fully airgapped:** you need a copy of `kody-w/RAPP` on disk too. Sneakernet it from a colleague, then `cd /path/to/RAPP/rapp_brainstem && ./start.sh`.

The brainstem creates `~/.brainstem/` on first run.

---

## After setup

Workflow agents loaded. Try in chat:

- `Twin intro` — orientation in the neighborhood's voice
- `EngagementFactory slug=hello-world customer_name="Test Co" ask="..."` — start an engagement
- `DashboardRender` — render the dashboard HTML
- `ProjectPinger team_status` — cross-team portfolio view
- `EggHatcher status` — confirm what's set up

---

## Round-tripping changes back to the repo

When you have internet + want to share back:

```bash
cd ~/brainstem-workspace/neighborhood-example/
git add ses/<your-handle>/projects.json
git commit -m "..."
git push     # requires gh auth + collaborator rights
```

Customer data at `~/.brainstem/neighborhoods/neighborhood-example/<handle>/customers/` never enters this commit — that path is `.gitignore`d.

---

## Updating the workflow

Owner ships a new agent → re-runs the neighborhood factory → new `.egg` → sneakernet → recipient runs `EggHatcher from_egg=... force=true`. Your `~/.brainstem/neighborhoods/neighborhood-example/` is untouched.

---

## See also

- `SKILL.md` — feed to your LLM to drive setup
- `CONSTITUTION.md` — 8 articles
- `specs/AGENT_CONTRACT.md` — what makes a valid agent
- `specs/RAR_INDEX.md` — manifest format + sha256 verification
- `specs/NEIGHBORHOOD_PROTOCOL.md` — join lifecycle, boundary, sneakernet rule
