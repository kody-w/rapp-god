# 🗺️ The RAPP Roadmap

**Use everyone else's hardware to run the network → operators run brainstems, subscribe to neighborhoods, and those estates mesh into a self-building metropolis — while the single-file kernel never changes.**

> **Re-grounded 2026-06-28** against a full corpus scan — all 85 rapp repos + a 630-card per-file neuron mesh ([kody-w/rapp-map](https://github.com/kody-w/rapp-map)). The prior version drifted toward *"a planetary swarm enhancing Agent 365"* as the destination; this one re-anchors on [MASTER_PLAN](https://github.com/kody-w/RAPP/blob/main/MASTER_PLAN.md)'s actual north star.

> Full roadmap: **[ROADMAP.md](ROADMAP.md)** · machine-readable: [`roadmap.json`](roadmap.json) · route a situation: [rapp-spine](https://github.com/kody-w/rapp-spine) · the estate: [rapp-map](https://github.com/kody-w/rapp-map)

## The north star (MASTER_PLAN §5)

> *"Use everyone else's hardware to run the network."*

GitHub already paid for the CDN (`raw`), the auth (`gh auth`), the durable async mailbox (Issues), the consent gate (PRs), and the edge (Pages). RAPP doesn't build a network — it uses the one already running. Operators run brainstems on their own machines and subscribe to many **neighborhoods**; the union of an operator's subscriptions is their **estate**; estates mesh through shared neighborhoods into the **metropolis**, which *"builds itself once it has enough nodes."* **Agent 365 is an optional Tier-3 commercial lane — not the destination.**

## The medium

Capability as a portable, signed, content-addressed object — the **cartridge** (`agent.py`) and the **egg** — that rides one wire (`POST /chat`, or a signed append-only event), needs no API keys or engine changes to run, and **degrades gracefully offline** (the *Charizard-in-the-woods* hero floor). Composed across scales via the `rapp-egg/2.0` **`scale`** field (agent/twin/brainstem/neighborhood/swarm/factory/industry/estate), these objects build the metropolis bottom-up.

## What re-grounding corrected (the honest part)

- **Agent 365 was mis-cast as the north star** — it appears in the entire kernel canon exactly once, as a GTM line. → demoted to an optional T3 lane.
- **`rapp-frame/1.0` collided** with the kernel's Dream-Catcher memory-frame (ECOSYSTEM §147). → **✅ resolved**: bumped to `rapp-frame/2.0`, unifying both as one `kind`-discriminated family (`memory.*`/`swarm.*`).
- **`/api/agent` violates CONSTITUTION Art XXV** "Chat Is The Only Wire." → route fleet messaging as signed twin-chat events over `/chat` (which `rapp-resident` already does — 67 verified events live).
- **PKI is rejected** by MASTER_PLAN §3 — *except* rappid eternity's **optional** keypair sovereignty (identity stays `sha256` / PKI-free; the keypair is opt-in and **never required**). The PKI cleanup targets only *mandatory*-keypair spots.
- **Build ON the existing network estate** (`rapp-neighborhood-protocol/1.0`, `rapp-commons`, `rapp-resident`, the egg `scale` field) — not a parallel "second wire."
- **The "kernel split-brain" was a false alarm** — rapp-installer is the kernel (the grail); RAPP is a clean *distro* pinning kernel `v0.6.0` byte-identical (Ubuntu-LTS-style). → adopt the **Linux kernel/distro model** explicitly; spawn distros freely ([rapp-spine FOUNDATION §2a](https://github.com/kody-w/rapp-spine/blob/main/FOUNDATION.md)).

## The arc (grounded)

| Phase | Horizon | Theme |
|---|---|---|
| **0 · The kernel/distro model** (Linux philosophy) | now | ✅ no split-brain — RAPP is a clean distro pinning kernel `v0.6.0` · freeze CI = `distro == grail@tag` · standardize tags · ✅ `rapp-frame` → 2.0 |
| **1 · Close the RCE — the canonical way** | 0–3mo | signed twin-chat events over `/chat` · retire `/api/agent` (Art XXV) · merge with `responsible-ai/ROADMAP.md` P0 |
| **2 · The hero floor** | 3–6mo | offline-LLM fallback (Charizard) · git-durable signed log (commons survives its single host) · Memory & Recall + Dream-Catcher |
| **3 · The real planetary work — mesh composition** | 6–12mo | author the neighborhood→estate→metropolis tier on `rapp-estate/1.1` + the egg `scale` field · reframe frame/hydra onto canon · **optional** signing |
| **4 · Re-canonize + optional commercial overlay** | 12mo+ | register the new pillars into the drift triangle · CI (hero tests + ANTIPATTERNS grep) · Agent 365 as an optional T3 lane · quarantine economic/SaaS drift |

## The guarantee that makes it safe

The **kernel never changes.** Every capability — the swarm, the auth, the mesh tier — ships as an **agent / cartridge / spine-profile on the existing wire**, never an engine edit. A passing CI invariant proves it.

## The honest blocker, named first

Today the fleet wire (`POST /api/agent/<name>`) is **unauthenticated** *and* off-canon (Art XXV). **Phase 1 closes it the canonical way** — signed twin-chat events over `/chat`, server-verified per `rapp-resident` — not by hardening a route that shouldn't exist. No enterprise pilot ships before that gate.

## Grounded in the full estate

This roadmap is anchored to the verified estate map + per-file neuron mesh in **[kody-w/rapp-map](https://github.com/kody-w/rapp-map)** (`estate-map.json` + `neurons.json`) — load that first. The adversarial **[BACKLOG.md](BACKLOG.md)** (165 wrenches) remains the long-term hardening bank.
