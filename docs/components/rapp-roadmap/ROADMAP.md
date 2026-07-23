# The RAPP Roadmap

> ⚠️ **RE-GROUNDED 2026-06-28.** This long-form was written before a full corpus scan (85 repos + a 630-card neuron mesh, [kody-w/rapp-map](https://github.com/kody-w/rapp-map)) caught recency bias. The **current grounded source of truth is [README.md](README.md) + [`roadmap.json`](roadmap.json)**, which re-anchor on MASTER_PLAN's real north star (*"use everyone else's hardware → the self-building metropolis"*), demote Agent 365 to an optional T3 lane, fix the `rapp-frame/1.0` collision, route the fleet over `/chat` (Art XXV), and keep PKI out except rappid eternity's optional keypair. Sections below that frame Agent 365 as the destination or `/api/agent` as the wire are superseded.

> **North star** — *Use everyone else's hardware to run the network* (MASTER_PLAN §5): operators run brainstems on their own machines, subscribe to many neighborhoods (the union = their estate), and estates mesh into a self-building metropolis — while the sacred single-file kernel never changes. Agent 365 is an optional Tier-3 commercial on-ramp, not the destination.

## The new medium

The new medium is capability itself made into a portable, signed, content-addressed object — the cartridge and the egg — that rides ONE wire (POST /chat, or a signed append-only event), needs no API keys, no procurement, and no engine changes to run. What HTML did for documents, the cartridge/egg does for agent capability: an AI workflow born on a laptop in under a minute becomes a forkable, deterministically-verified artifact the Foundry can push fleet-wide in seconds, an egg can carry to another operator with one command, and that promotes intact up the tiers into Copilot Studio. Composed, these objects form a Leviathan — a fleet of agent-beings driven as ONE mind: 0.2s heterogeneous fan-out, no shared-token throttle, alive even when a node's own LLM is dead. The medium is "fleet-of-beings-as-one-mind": the unit is capability-as-an-object, the organism is the swarm, and the whole thing is an enhancement layer Agent 365 governs — never a fork of Microsoft's stack.

## The pitch to Agent 365 — *enhance, never replace*

**The gap.** Agent 365 wins the control plane — Entra Agent ID for identity, Purview for governance, Defender for security, plus registry and observability — but a control plane can only govern a population it does not itself create, and it launches against two cold-start gaps. The DEMAND gap: enterprises hold millions of GitHub Copilot seats that don't yet build agents, so there are too few trained makers. The SUPPLY gap: a new agent platform launches with an empty registry and shadow-agent sprawl. Microsoft has the trust root but not the line that fills it.

**The enhancement.** RAPP is the bottom-up ON-RAMP that fills both gaps without competing for either job. A free, no-API-key, one-line install turns each idle Copilot seat into a trained agent builder in under a minute (closing the demand gap), and the Foundry + a signed RAR registry + portable eggs manufacture and distribute vetted capability (closing the supply gap). Every integration is a cartridge, profile, or connector — Copilot Studio's builder role and RAPP's sacred kernel both stay untouched. The fit is exact: T3 (Copilot Studio + Teams) IS the Agent 365 plane; doc2cs is the one-click promotion path with Entra Agent ID auto-enrollment; the flight recorder is a Purview-shaped audit substrate; the authenticated fleet wire is a Defender-enforced, Entra-governed control. Every move pushes the team's own KPIs — agent population, time-to-first-agent, governance coverage %, security posture, seat attach, maker activation — instead of competing for them.

**Planetary swarm.** The one capability the plane cannot build for itself: the Leviathan — one mind driving many GOVERNED no-LLM bodies with 0.2s heterogeneous fan-out, no shared-token throttle, alive even when a node's own LLM is dead — and the Foundry, which patches every agent in the fleet in seconds, provably, with rollback. This is not 50,000 isolated copilots; it is one coordinated organism of governed agents, and as it federates it becomes a fleet of beings driven as one mind across orgs. That is the new MEDIUM — capability-as-an-object composed into fleet-of-beings-as-one-mind — measured inside Agent 365, never a fork of it.

**The ask.** Co-own the on-ramp. (1) Recognize the cartridge/egg as a first-class content-addressed capability format in the Agent 365 registry; (2) ship an official connector so promoted RAPP agents auto-receive Entra Agent ID + Purview/Defender; (3) co-author the fleet-wire auth standard on Entra Agent ID so Leviathan fan-out is governed by Microsoft's own identity plane; (4) bless RAPP as the sanctioned sandbox->production on-ramp with telemetry up-flow, co-sold by field/CSAs. In return, Agent 365 inherits a stocked shelf, a trained maker population, and a swarm medium — moving its KPIs from day one.

## The phases — laptop → planetary swarm

### Phase 0 — Lock the kernel, light the funnel, name the on-ramp  · `now`

*Make 'kernel sacred' a testable invariant, make the free first-run measurable, and pin the Agent 365 positioning to numbers — before scaling spend or writing integration code.*

**Objectives**
- Freeze the rapp-agent/1.0 contract as a green CI invariant so all later maturation provably stays out of the kernel.
- Make the existing one-liner install the most reliable, measurable first-run in the category and instrument the North-Star activation funnel.
- Lock the 'enhance Agent 365, never replace' framing as a one-sentence thesis a Microsoft PM can repeat, with every RAPP mechanism mapped to an Agent 365 KPI.
- Neutralize the standing liability: mark the unauthenticated swarm/shell/relay cartridges GATED and default-OFF until Phase 1 lands.

**Milestones**
- Kernel-conformance harness in CI: assert the only wires are POST /chat (tool-loop, MAX_ROUNDS) and agent-injected direct routes; freeze the BasicAgent.metadata + perform(**kwargs)->str ABI; assert no capability requires a new core symbol; assert brainstem.py (T1) and function_app.py (T2) behave identically (parity gate).
- Pinned-version installs (BRAINSTEM_VERSION=X.Y.Z), fresh-machine end-to-end install test gate, immutable brainstem-vX.Y.Z rollback tags surfaced to users.
- Opt-in, privacy-clean activation telemetry in an ACCESSORY repo (never the kernel): time-to-first-agent and time-to-first-fan-out.
- Canonical 5-minute hero demo recorded and embedded on the landing page: Leviathan controller doing 0.2s heterogeneous fan-out across 3 bodies, no API keys.
- Blast-radius classification of swarm cartridges (flock_endpoint = direct exec, remote_control = arbitrary shell, brainstem_relay = lateral) — all three marked default-OFF.
- Adoption-gap one-pager + tier->plane->KPI metric map + explicit non-goals slide (not a competing builder, not a competing plane, not a Copilot replacement).

**Guiding hero use case:** The Leviathan controller demo — one mind, 0.2s heterogeneous fan-out across three no-LLM bodies, no API keys — recorded as the canonical 5-minute hero.

**Exit criteria:** The kernel contract is a passing CI invariant (incl. stem/function_app parity); the one-liner has a measured time-to-first-agent funnel on a fresh machine; the unauth fleet/shell/relay cartridges are default-OFF; the Agent 365 metric map compresses to a single repeatable sentence.

### Phase 1 — Close the RCE, make the fleet sellable  · `0-3mo`

*The gating blocker. The unauthenticated POST /api/agent/<name> wire and the shell/relay agents behind it become authenticated, default-deny, per-agent allowlisted, and audited — entirely as a cartridge + spine profile, zero kernel edits, identical in T1/T2 — and the proven controller + Foundry become a turnkey product a second person can stand up safely.*

**Objectives**
- Eliminate fleet-wide RCE: no path reaches an agent's perform() without passing a signed, allowlisted, recorded gate.
- Turn the Leviathan controller + Foundry from a demo into something a second operator can stand up governably in minutes.
- Define and validate the paid surface (Free / Fleet-Pro / Enterprise) with real design partners before scaling GTM.

**Milestones**
- Signed-flock cartridge: HMAC shared-secret bearer (BRAINSTEM_FLOCK_SECRET) + nonce/timestamp replay window on POST /api/agent/<name> and on BrainstemRelay /chat relays; reject unsigned/expired; token slot designed to accept Entra Agent ID claims later.
- Per-agent allowlist, DEFAULT DENY: RemoteControl and every shell/exec agent OUT of the default — enforced and tested so it is real, not theater; every gated call and denial recorded append-only by the flight recorder (caller-attributed).
- Optional mTLS profile for any cross-host/off-LAN hop; documented that shared-secret is LAN-tier and mTLS/Entra is the enterprise path.
- New spine 'fleet-auth' protocol/profile (a profile on the existing wire, NOT a new endpoint) + published threat model; landed identically in T1 brainstem and T2 function_app; security-review sign-off gates any non-LAN deployment.
- 'Add a body' onboarding wizard (stand up a no-LLM body and join a fleet in minutes) and branch-twin hatchery exposed as a self-serve feature.
- Foundry packaged as the capability-supply engine (author once -> deterministic test, no LLM -> push fleet-wide in seconds); SKU hypothesis articulated and run with 3-5 internal Microsoft design-partner teams.

**Guiding hero use case:** The Foundry — author a vetted agent once, deterministically test it with no LLM, and push it across a now-authenticated fleet in seconds.

**Exit criteria:** RemoteControl is provably out of the default allowlist and every /api/agent call is signed + audited; a second operator stands up a governed 3-body fleet from the wizard; a security reviewer signs off on a non-LAN pilot; at least one design partner validates the Fleet-Pro paid surface; the gate behaves identically in T1 and T2.

### Phase 2 — Distribution + a legible fleet  · `3-9mo`

*Make capability flow without a human in the loop: the egg becomes the unit of distribution, RAR a trustworthy signed registry, the MCP server the default way IDE agents drive the fleet — and make a running fleet legible with a signed event stream and a read-only control plane.*

**Objectives**
- Turn capability into a self-serve, signed, verifiable supply chain (no human approval step to move it).
- Make a fleet observable and its versions rollback-safe.
- Turn every Claude Code / Copilot CLI / Cursor user into a distribution channel via the native MCP on-ramp.

**Milestones**
- Signed portable eggs (being/twin/swarm) as a first-class self-serve install; RAR upgraded to a real registry — provenance, signing, ratings/votes, capability search; install verifies signature before load (no unsigned cartridge enters a node).
- Signed append-only event schema (the 'second wire'): every fleet action emits a signed event; a read-only control-plane cartridge shows live roster, token health, per-node capability inventory, and cross-node version/profile drift via the spine.
- Foundry as a signed content-addressed supply chain over rapp-static-api/1.0 catalogs; hatchery branch-twins become the canary/staging lane; one-command rollback to a known-good capability set.
- MCP on-ramp listed and discoverable in Claude Code / Cursor / GitHub Copilot CLI ecosystems (zero-dep stdio); CopilotCLI delegation (brainstem PLANS, Copilot CLI EXECUTES) packaged as a supported, rate-limit-paced pattern.
- Team workspace + self-serve billing for Fleet-Pro; 'RAPP Author' docs + certification track + a seeded first-party catalog so supply (authors) and demand (installs) bootstrap together.

**Guiding hero use case:** Hand someone a being — install a signed .egg with one command and watch it join their fleet, signature and provenance verified.

**Exit criteria:** An enterprise can install a community agent whose signature and provenance it verifies before load; a fleet operator sees live roster + drift in a dashboard fed by the flight recorder; a new cartridge version proves out on a branch-twin then rolls fleet-wide with one-command rollback; the MCP server is discoverable in at least two IDE ecosystems; Fleet-Pro has self-serve billing and paying teams.

### Phase 3 — Land in the plane (Agent 365 co-sell, identity, federation)  · `9-18mo`

*Make graduation into Agent 365 a one-click governed event, convert bottom-up adoption into enterprise revenue through Microsoft's own motion, and cross the operator boundary safely with cryptographic identity and scoped — never blanket — capability grants.*

**Objectives**
- Make a promoted agent unable to enter the Agent 365 plane ungoverned.
- Ship the admin/audit controls IT signs off on, and the procurement-grade trust kit that survives security review.
- Enable safe same-device swarm-to-swarm via keypair identity + scoped, expiring, revocable capability grants (T2T deferred to the far horizon, per adoption-first stance).

**Milestones**
- doc2cs / connected-solution productized as the enterprise front door: docs + app-reg -> connected-agents solution -> import & publish, one click (live Azure app already proves it); Entra Agent ID auto-enrollment on every T3 deploy.
- Admin console: fleet governance, per-agent allowlists, full flight-recorder audit, secrets/identity, kill-switch; flight-recorder events mapped to a Purview-shaped audit/eDiscovery schema and exportable to M365 compliance.
- Keypair identity per being/Leviathan (rappid:<slug>:<64hex>, read all legacy forms forever, emit only canonical, hash is the join key); signed eggs verifiable on import; scoped, expiring, per-agent capability-grant tokens (NOT a shared flock secret) with revocation + key rotation in a federation handshake profile.
- Security review + SOC posture + Phase-1 auth hardening packaged into a procurement-grade 'trust kit'; Azure Marketplace / Agent 365 connector transact listing so the enterprise SKU is purchasable through existing channels.
- Agent 365 co-sell collateral for MS field/CSAs + 2-3 named reference customers; a lighthouse workflow taken laptop -> governed Agent 365 agent with metric deltas captured as the proof artifact.

**Guiding hero use case:** doc2cs — promote a laptop-born cartridge into a governed Copilot Studio + Teams connected-agents solution with Entra Agent ID auto-enrollment, one click.

**Exit criteria:** A promoted agent cannot enter the plane ungoverned (auto-Entra-enroll proven); flight-recorder audit exports into Purview; an enterprise passes procurement on the trust kit; 2-3 reference customers run governed fleets; the Marketplace listing is transactable; co-sell collateral is in field hands.

### Phase 4 — The planetary swarm, productized (the new medium delivered)  · `18mo+`

*Complete the ladder — a fleet of beings driven as one mind, across orgs, as a portable digital self — establish RAPP as a new MEDIUM sanctioned by and measured inside Agent 365, deliver the formal ask, and prove the kernel never changed.*

**Objectives**
- Govern planetary fleets under Microsoft's own identity plane, only after single-operator governance is proven.
- Productize the Leviathan being as a sellable 'digital self' and seed a capability economy around it.
- Deliver the formal Agent 365 ASK and the final kernel-sacred attestation.

**Milestones**
- Entra-brokered fleet auth replaces the shared secret in enterprise mode (brokered-auth / token-protection path: disableBrokeredAuth=false, device-bound tokens); per-agent RBAC scoped to tenant; cross-tenant Leviathans opened only after single-operator governance is proven.
- The 5-estate Leviathan being (Sanctum / Polity / Works / Press / Commons) productized as a signed, identity-bound, policy-scoped 'digital self' representable as a managed org unit inside the plane.
- Formal ASK delivered: (1) recognize the cartridge/egg as a first-class content-addressed capability format in the Agent 365 registry; (2) official connector auto-granting Entra Agent ID + Purview/Defender on promotion; (3) co-authored fleet-wire auth standard on Entra Agent ID; (4) RAPP blessed as the sanctioned sandbox->production on-ramp with telemetry up-flow.
- Ecosystem partner/economy program (third-party eggs/agents/profiles; confidence + reputation first-class); content-addressed capability marketplace feeding the registry; continuous ecosystem-coherence tooling (spine's 33 protocols pinned + neuron-mesh drift sweeps) productized as the governance that keeps a planetary platform coherent.
- Final kernel-sacred attestation: the rapp-agent/1.0 contract is unchanged from Phase 0 — every capability rode cartridges, profiles, or catalogs.

**Guiding hero use case:** One mind, many beings — an operator drives a cross-org fleet of governed Leviathan beings as a single coordinated organism, every action Entra-identified and Purview-audited.

**Exit criteria:** Agent 365 recognizes the cartridge/egg in its registry and an official connector auto-governs promoted agents; a cross-tenant Leviathan runs under Entra-brokered auth with tenant-scoped RBAC; the kernel-sacred attestation passes; joint GTM is live with measured deltas on Agent 365's own KPIs.

## Hero use cases — the guiding lights

| Use case | Today | Productized |
|---|---|---|
| **One mind, many bodies (the Leviathan controller)** | Drives a heterogeneous fleet of no-LLM brainstem bodies over POST /api/agent/<name> in ~0.2s with no shared-token throttle, alive even when a node's own LLM is dead — but UNAUTHENTICATED, LAN-only, a fleet-wide RCE; a five-minute demo, not a product. | Entra-governed, signed, per-agent-allowlisted fan-out across orgs; one operator drives a planetary fleet of governed beings as a single organism, every action Entra-identified and Purview-audited. |
| **Manufacture capability fleet-wide (the Foundry)** | Author a vetted agent once, deterministically test it with no LLM, push it to the whole fleet in seconds — locally, unsigned, ungoverned. | A signed, content-addressed supply chain with role-gated rollout, deterministic test gates, provable rollback, and audit — 'patch every agent in the fleet in seconds, provably' — feeding the Agent 365 registry's empty shelf. |
| **Every branch is a living twin (the Hatchery)** | Git worktrees turn each branch into a running brainstem twin, so builders prototype and A/B agents as naturally as they branch code. | The canary/staging/rollback lane for the whole fleet: new cartridge versions prove out on a branch-twin before fleet rollout, with one-command roll-back to a known-good capability set. |
| **Drive the fleet from the tools you already use (MCP on-ramp)** | Claude Code, GitHub Copilot CLI, and Cursor command the swarm natively via a zero-dependency stdio server — present but not listed/discoverable. | Listed and discoverable in every major IDE-agent ecosystem; Copilot Studio / Agent 365 orchestrators drive a vetted RAPP fleet natively through the same bridge — distribution rides inside builders' existing tools. |
| **Plan here, execute there (CopilotCLI delegation)** | The brainstem PLANS and Copilot CLI EXECUTES autonomously — a glimpse of agents doing real end-to-end work, but naive parallel planning can still saturate one account's Copilot rate limit. | A supported, rate-limit-paced pattern: the planning mind is serialized/throttle-aware while no-LLM bodies absorb the fan-out, so one mind drives a fleet without bottlenecking on a single token. |
| **Hand someone a being (portable eggs / twins)** | Package a whole agent, swarm, or 5-estate Leviathan being as an .egg and install it elsewhere with one command — but unsigned and unverifiable. | Signed, keypair-bound (rappid:<slug>:<64hex>) eggs verified on import and federatable; capability becomes a shareable, trustworthy object a marketplace distributes and the registry can ingest. |
| **From document to governed Agent 365 agent (doc2cs)** | A live Azure app: upload docs + an app registration and get a Copilot Studio connected-agents solution imported and published into M365 — the working bridge into Agent 365's home turf. | One-click promote-to-Agent-365 with Entra Agent ID auto-enrollment and Purview-shaped audit — a laptop cartridge becomes a governed agent that can never enter the plane ungoverned, with metric deltas captured. |
| **The Flight Recorder (the accountability substrate)** | Append-only, both-sides-of-every-conversation log that already records every /api/agent call (caller-attributed) to an owned directory outside the engine. | A signed fleet-wide event stream mapped to a Purview-shaped audit/eDiscovery schema and exported to M365 compliance — the observability that makes the swarm presentable to Defender and procurement. |

## The kernel stays sacred — guarantees

- The kernel is ONE auditable file (brainstem.py, today ~1,817 lines) and NEVER grows to add a capability — every capability arrives as an agent/cartridge, a signed catalog, or a spine protocol/profile, never an engine edit. Even the swarm wire is a cartridge (flock_endpoint_agent.py injects its route at import time).
- The only LLM wire is POST /chat (the tool-calling loop, bounded by MAX_ROUNDS); the only other wire is a signed append-only event. No new REST endpoints are baked into the engine — /chat is the sacred endpoint and all capability flows through it.
- The agent ABI is frozen and drop-in compatible with any unmodified brainstem: a class extending BasicAgent with metadata (OpenAI function schema) + perform(**kwargs)->str, optional system_context(); flat-globbed *_agent.py, hot-reloaded every request. No capability may require a new core symbol.
- stem/function_app parity is sacred and CI-gated: T1 brainstem.py and T2 function_app.py behave identically, so security and behavior guarantees are never tier-specific.
- ALL packaging — installer UI, dashboards, billing, marketplace, auth, federation, telemetry — lives in accessory repos OUTSIDE ~/.brainstem/src; the grail never bloats and the 'engine, not experience' Constitution holds.
- The local tier uses NO API keys: GitHub Copilot OAuth only — single auth, single provider, one training story; Tier-1 Copilot-only is intentional, not a gap to 'unify away'.
- Every VERSION bump ships an immutable brainstem-vX.Y.Z git tag; tags are rollback points users reach via BRAINSTEM_VERSION=X.Y.Z.
- Identity is append-only: read all legacy rappid forms forever, emit only the canonical rappid:<slug>:<64hex>, the hash is the join key — never rewrite identity in place.
- A kernel-conformance harness asserts these invariants in CI, and a final kernel-sacred attestation proves the rapp-agent/1.0 contract is unchanged from Phase 0 — every productized capability rode cartridges, profiles, or catalogs.

## Productization checklist

- [ ] Authenticated fleet wire: HMAC shared-secret bearer + nonce/timestamp replay window on POST /api/agent/<name> and BrainstemRelay; optional mTLS for off-LAN; token slot designed to later accept Entra Agent ID claims — shipped as a signed cartridge + spine 'fleet-auth' profile, landed identically in T1 and T2.
- [ ] Default-DENY per-agent allowlist with RemoteControl and every shell/exec agent OUT of the default; enforced and tested (not theater); every gated call and denial recorded append-only by the flight recorder.
- [ ] Pinned-version installs (BRAINSTEM_VERSION=X.Y.Z) + fresh-machine end-to-end install test gate + surfaced immutable rollback tags.
- [ ] Opt-in, privacy-clean activation telemetry (accessory repo): time-to-first-agent and time-to-first-fan-out funnel.
- [ ] Canonical 5-minute hero demo recorded and embedded: 0.2s heterogeneous fan-out, no API keys.
- [ ] RAR upgraded to a signed registry: provenance, signing, ratings/votes, capability search; install verifies signature before load.
- [ ] Signed portable eggs: keypair-bound (rappid:<slug>:<64hex>), verifiable on import; one-command install-an-egg as a first-class self-serve flow.
- [ ] Read-only fleet control-plane dashboard reading the flight recorder: live roster, token health, per-node capability inventory, cross-node version/profile drift.
- [ ] Foundry as a signed content-addressed supply chain over rapp-static-api/1.0 catalogs; hatchery branch-twins as the canary/staging lane; one-command rollback to a known-good capability set.
- [ ] doc2cs / connected-solution productized: docs + app-reg -> connected-agents solution -> import & publish, one click; Entra Agent ID auto-enrollment on every T3 deploy.
- [ ] Admin console: per-agent allowlists, full flight-recorder audit, secrets/identity, kill-switch; Purview-shaped audit/eDiscovery export to M365 compliance.
- [ ] SKU boundary defined and validated with 3-5 design partners: Free (single brainstem) / Fleet-Pro (multi-body controller + Foundry + dashboard) / Enterprise (governance/audit/Entra); team workspace + self-serve billing for Fleet-Pro.
- [ ] Procurement-grade 'trust kit': security review + SOC posture + threat model + the auth hardening; Azure Marketplace / Agent 365 connector transact listing.
- [ ] MCP on-ramp listed and discoverable in Claude Code / Cursor / GitHub Copilot CLI; CopilotCLI delegation packaged as a supported, rate-limit-paced pattern.
- [ ] 'RAPP Author' docs + certification track + seeded first-party catalog so marketplace supply and demand bootstrap together.
- [ ] Federation: scoped, expiring, revocable per-agent capability-grant tokens (not a shared secret) + key rotation; Entra-brokered fleet auth (device-bound tokens, disableBrokeredAuth=false) for enterprise mode with tenant-scoped RBAC.
- [ ] Continuous ecosystem-coherence CI: spine's 33 protocols pinned + ecosystem-sync / neuron-mesh drift sweeps productized as governance.
- [ ] GitHub Copilot OAuth ToS clarity / a sanctioned relationship secured as part of the Agent 365 conversation.

## Top risks

- ⚠️ BLOCKER — unauthenticated fleet wire is fleet-wide RCE TODAY. Verified: agents/flock_endpoint_agent.py injects POST /api/agent/<name> into the Werkzeug url_map and calls inst.perform(**body) directly with no auth, while remote_control_agent.py runs arbitrary shell (subprocess.run(command, shell=True)) and BrainstemRelay enables lateral movement right behind it. Until signed + default-deny per-agent allowlist + mTLS ships (Phase 1), there is no enterprise SKU, no passing security review, no monetization. It must be the FIRST productization milestone — and even LAN exposure is a standing liability, so the cartridges stay default-OFF until then.
- ⚠️ Kernel bloat / grail contamination — the strongest pressure will be to put auth, dashboards, billing, federation, or telemetry INTO brainstem.py for convenience. That erodes the single-file auditable differentiator and breaks the Constitution. All packaging MUST stay in accessory repos / cartridges / profiles, enforced by the conformance harness.
- ⚠️ Positioning risk — 'planetary swarm of Leviathans' / 'one mind, many bodies' can read as a competitor to Agent 365 or Copilot Studio and trigger the MS field to treat it as a threat. Messaging must relentlessly lead with on-ramp / enhance / adoption-gap and pin every claim to an Agent 365 KPI, acknowledging Agent 365 up front every time.
- ⚠️ Wedge dependency on GitHub Copilot OAuth + shared rate limit — the entire free, no-API-key funnel rests on Copilot API access and ToS; no-LLM bodies remove the throttle only for pre-known agent+args, while the planning mind still spends one account's tokens (30+ min lockouts observed). Needs ToS clarity, a sanctioned relationship, paced/serial planning, and Entra identity reconciliation at T3.
- ⚠️ Monetization ambiguity — a great free funnel with no crisp paid surface never converts. The Free -> Fleet-Pro -> Enterprise boundary and exactly what you pay for (governed multi-body fleet, Foundry at scale, audit/admin) must be defined in Phase 1 and validated with design partners.
- ⚠️ Channel / chasm risk — bottom-up champions cannot sign enterprise deals. Without admin governance + flight-recorder audit + the MS co-sell motion (Phase 3), adoption plateaus at hobbyist scale and never reaches revenue.
- ⚠️ Marketplace cold-start — RAR + eggs only network-effect if supply (authors publishing) and demand (installs) bootstrap together. Needs a seeded first-party catalog, an Author cert/incentive program, and provenance/signing so enterprises trust community agents.
- ⚠️ stem/function_app parity drift — if hardening lands in T1 but not identically in the T2 Azure function_app, security guarantees become tier-specific. Parity must be a CI gate, not a hope.
- ⚠️ Federation key management — signed eggs + capability grants are only as safe as their revocation and rotation story; a leaked zookeeper/being key without fleet-wide revocation compromises every node that trusts it. Scoped, expiring grants — never a shared blanket secret — are mandatory before crossing the operator boundary.
- ⚠️ Ecosystem-coherence drift at scale — 33 protocols across 6 layers already require active drift sweeps; as the platform federates across orgs, incoherence becomes a product-quality and trust risk. The coherence tooling (spine / ecosystem-sync / neuron-mesh) must itself be productized as governance, not run as ad-hoc maintenance.
- ⚠️ Allowlist theater — if RemoteControl or any shell/exec agent ever sits in the DEFAULT allowlist, the Phase 1 gate is cosmetic. Default-deny with shell agents OUT must be enforced and tested, not assumed.
- ⚠️ Moving target — Agent 365's Entra Agent ID, registry, and Purview/Defender hooks are still evolving; keep the integration spec-driven via rapp-spine so RAPP tracks the plane instead of hard-coding against a snapshot, and resist leading with cross-tenant federation (18mo+) before single-operator governance is proven.

---

*One brainstem on a laptop → a planetary swarm of Leviathans enhancing every Agent 365 workflow. The kernel never changes; the capability rides one wire.*

## The architecture, locked (and proven live)

The brainstem is the **atom**; the kernel is **locked**; every spec has a globally-public **canonical twin** (content-addressed in [`foundation.json`](https://github.com/kody-w/rapp-spine/blob/main/foundation.json)); and the whole medium rides the **hydra** (many heads, unkillable). The pillars:

| pillar | spec | repo | status |
|---|---|---|---|
| **fleet** | `leviathan/1.0` | kody-w/leviathan | live, unified |
| **being** | `rapp-leviathan-egg/1.0` | kody-w/rapp-leviathan-hub | live, unified |
| **planet** | `rapp-frame/1.0` | kody-w/rapp-frame-net | live; POC proven (edge local-judgment + append-only event loop) |
| **survival** | `rapp-hydra/1.0` | kody-w/rapp-frame-net | live; proven on 3 independent CDN heads |
| **router** | `rapp-spine/1.0` | kody-w/rapp-spine | live; locks the foundation + routes situations |

**Proven live, on real infrastructure (not slideware):**

- an edge brainstem made a stale-guidance-safe LOCAL judgment off a frame (reversible mitigation, refused irreversible deletion, flagged the conflict)
- the full event-sourced loop closed over GitHub: telemetry -> append-only event -> frame loop forges echo -> materialized view -> edge re-aims (idempotent, no API we don't own on the read path)
- the hydra served the same content-hash from raw.githubusercontent.com, jsDelivr, and raw.githack

The kernel never changed — every pillar is agents/cartridges/profiles on the wire. An edge is a full brainstem, so **every hero use case works at the edge, unchanged**, even on a spotty link, even offline.


## Household layer (added 2026-06-29)

The brainstem now natively reproduces openclaw as drop-in organs it runs by itself: an iMessage **gateway** + group **presence** organ (read-the-room, persona-driven, proven indistinguishable on the LAN), a **burrow** organ (launchd persistence for the brainstem + all organs), and the **Organ Control Room** (a PWA pulled from a global repo, served locally, with enable/disable + observe/live toggles). Plus: make the **chat UI a PWA** (native on macOS/Windows), and bring the brainstem engine to **Claude-Code-class** (budgeted loop + subagents). Own the orchestration; borrow the muscle. See roadmap.json phase "The household layer".
