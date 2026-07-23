# rapp_kernel

**Kernel & install** — the frozen DNA archive (kernel snapshots + version catalog).

- Canonical: https://github.com/kody-w/RAPP (kernel lives at `rapp_kernel/` in the species root)
- Schema: `rapp-kernel/1.1`
- Default branch: `main`

## What it is

`rapp_kernel` is the **frozen DNA** of the digital organism — the kernel snapshots. The kernel is `brainstem.py` + `basic_agent.py`: universal, drop-in replaceable, and **never edited by AI assistants** (CONSTITUTION Art. XXXIII). It is archived as immutable snapshots (`latest/` + `v/<version>/`) with a `manifest.json` (`rapp-kernel/1.1`) cataloging every version, signed with ed25519.

When something feels like it needs a kernel change, the answer is always: write a new agent or organ instead. The kernel never moves (ANTIPATTERNS §2).

## What it provides

- Frozen kernel snapshots — the DNA archive.
- `manifest.json` — the signed version catalog.
- The drop-in-replaceable guarantee: any brainstem can swap its kernel for another snapshot.

See [`OVERVIEW.md`](../OVERVIEW.md) §1 and the Constitution.
