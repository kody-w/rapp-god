# MUSCLE ORDER BIRTH — `kody-w/rapp-body`: the organism's biography, its pulse, and the player

## Intent
Build the RAPP body's own frames repo: the full ecosystem as ONE being whose existence is recorded
as a chained, signed, public sequence of frames — cradle to grave — plus **player.html**, a
flip-book that plays the frames so you literally watch the body be born, grow, and transform.
Design authority: `PROPOSAL-rapp-body-frames.md` on branch `feat/atlas-generic-template` of the
LOCAL repo `~/Documents/GitHub/rapp-spine-atlas` — READ IT FIRST (including "The snake through
time" section). Work in the current directory (`~/Documents/GitHub/rapp-body`) = future repo root.
NO git actions — the cortex publishes.

## Conformance (recon before building — compose, never invent)
1. **Frame envelope:** `rapp-frame/2.0` exactly as `kody-w/twin/frames/*.json` uses it:
   `{spec, kind, seq, ts, twin_id, kernel_version, payload, sha256, parent_sha, sig?}`.
   Read `kody-w/twin/tools/verify-chain.mjs` (raw fetch) and REPLICATE its canonicalization +
   chain rules exactly — our `tools/verify-chain.mjs` must interoperate conceptually (a twin
   engineer should read ours and recognize theirs). Body frames use `kind: "body.pulse"` (witnessed)
   and `kind: "body.pulse.reconstructed"` (archaeology).
2. **Identity:** mint the body's `rappid.json` per rapp-eternity/1.0 Eternity form
   (`rappid:@kody-w/rapp-body:<64hex>`, sha256 content-address — conform to `kody-w/twin/rappid.json`
   shape; keypair/sig OPTIONAL and omitted for now — chain integrity comes from sha256 links).
3. **Census source of truth:** the canonical repos list inside the ecosystem spec. Fetch
   `https://raw.githubusercontent.com/kody-w/rapp-map/main/ecosystem-spec.json` (mirror of record
   for reads) — census covers every repo it catalogs, PLUS `kody-w/rapp-spine` registry entries'
   repos, deduped. Layer/cluster metadata comes from the spine registry + spec categories.

## Deliverables

### 1. `tools/pulse.mjs` — the witnessed frame-taker (Node ≥20, ZERO deps)
- Gathers a slice: **skeleton** (ecosystem-spec version + sha256 as served from each of its three
  homes: kody-w/RAPP (locate in-repo path), rapp-god `api/v1/ecosystem-spec.json`, rapp-map
  `ecosystem-spec.json`; plus rapp-spine `registry.json`/`foundation.json` shas), **census**
  (per cataloged repo: name, default-branch head sha, pushed_at, created_at, spine layer if known;
  plus `born[]`/`vanished[]` vs previous frame), **vitals** (open issues labeled `drift` across the
  cataloged repos by severity-prefix in title; `mirrors_identical` bool; last-sweep info if a
  `sweeps/latest.json` exists in this repo — optional input, absent OK), **events[]** (derived:
  births, vanishings, spec version changes, drift deltas vs previous frame).
- Every frame gets `ts` (slice time = now for witnessed) and `payload.taken_ts`; witnessed frames
  set `payload.provenance = {mode: "witnessed"}`.
- **No-churn rule (hard):** if skeleton+census+vitals are materially identical to the previous
  frame (ignore timestamps), DO NOT mint a frame — print "no change; no frame". A `--heartbeat`
  flag overrides (weekly liveness frame, `events: [{type:"heartbeat"}]`).
- Appends to `frames/` as `<seq>.json` (twin convention), updates `frames/index.json`
  (manifest: seq, path, ts, kind, sha256 — ONE fetch loads the whole map) and `vitals.json`
  (latest seq + sha + health rollup; the static-API surface).
- Anonymous-safe (works without token; uses GITHUB_TOKEN when present). A source it cannot read
  becomes an explicit `events: [{type:"observation-gap", ...}]` — NEVER silently thinner data
  (today's false-green lesson).

### 2. `tools/reconstruct.mjs` — the prenatal frames (git archaeology, run ONCE now)
- Mines real history: `created_at` of every cataloged repo (GitHub API), spec/kernel milestones
  discoverable from rapp-map + rapp-god git history (commits touching ecosystem-spec.json:
  version-lock moments), known canon dates present in the spec/spine text (e.g. Eternity
  ratification 2026-06-03, kernel v0.6.0 grail, twin DOG-online 2026-07-06 from twin frame 1).
- Emits `kind: "body.pulse.reconstructed"` frames in CHRONOLOGICAL order, seq starting at 0 —
  one frame per meaningful cluster (repo-birth waves by week/month, each canon milestone its own
  frame). Target: enough frames that the player tells the story (expect roughly 15–40, judgment
  yours). Each carries `payload.provenance = {mode:"reconstructed", evidence:[<API fields/commit
  shas/URLs used>]}` — reconstructed frames NEVER claim witness, and their census may be partial
  (record `census_basis`).
- The chain runs reconstructed 0..N-1 → witnessed genesis = seq N, linked by parent_sha
  throughout.

### 3. The GENESIS witnessed frame (seq N, minted by pulse.mjs after reconstruction)
Today's slice, with `events` telling the day: full-mesh sweep verdict DRIFT-FOUND (13 findings,
3 high), 13 `drift()` issues filed, reconciliation in flight, the immune-system plan
(PLAN-drift-immunity) and this biography born the same day. Keep event text factual, no customer
names, public-safe.

### 4. `tools/verify-chain.mjs` — validator
Walks frames/ + index.json: seq contiguity, parent_sha links, sha256 recompute, ts monotonicity,
provenance rules (no witnessed frame before genesis; every reconstructed frame has evidence).
Exit 0 clean / 1 broken with precise reasons. `pulse.yml` runs it before AND after minting.

### 5. `player.html` — the flip book (the crown; self-contained, no CDN, no deps)
- **Load:** fetch `frames/index.json` then frames (relative paths → works on Pages AND file://
  with a served-directory fallback hint). Handle 15–5000 frames gracefully (lazy-load bodies,
  index drives the timeline).
- **Render each slice as a BODY, not a table:** repos = organ cells (SVG or canvas, hand-rolled),
  clustered by spine layer (map/runtime/distribution/identity/network/leviathan/uncataloged),
  cell size ~ recent activity (pushed_at recency), cluster hue per layer (restrained palette,
  readable in light AND dark via prefers-color-scheme), drift = red inflammation glow scaled by
  open-drift counts, spec version rendered as age rings around a nucleus (the skeleton), born
  organs pulse green on their birth frame, vanished organs fade out. A vitals strip (frame ts,
  seq, witnessed/reconstructed badge, drift counts, spec version) anchors the header.
- **Flip-book controls:** play/pause (space), scrub slider, speed (0.5×–8×), step ◀ ▶ (arrow keys),
  diff mode (highlight what changed vs previous slice), event markers on the timeline
  (births/canon/drift-storms; click = jump). Reconstructed segment visually distinct from the
  witnessed segment on the timeline (e.g. sepia vs full color — the film "develops" at genesis).
- Accessibility: keyboard operable, aria labels on controls, text alternatives for counts.
- Same discipline as atlas.html: zero external requests, < ~2MB, no console errors.

### 6. `.github/workflows/pulse.yml`
Daily cron (one pulse) + `workflow_dispatch` + weekly `--heartbeat` (separate cron). Steps:
verify-chain → pulse → verify-chain → commit frame+index+vitals only if a frame was minted
(the no-churn rule makes this real). `permissions: contents: write`.

### 7. `README.md` — structure/quickstart/format reference ONLY (plain, factual). The soul/voice
docs are cortex-written afterward — do NOT write soul.md.

## Do NOT
- git init/commit/push; no repo creation; no PRs.
- No npm deps anywhere. No CDN in player.html.
- No customer names, no private data in any frame (public-by-construction — the body's DOG rule).
- Do not modify anything outside this directory.

## Done-when (verify yourself, then report)
1. `node tools/reconstruct.mjs` → prenatal frames written; `node tools/pulse.mjs` → genesis frame
   minted; second `pulse.mjs` run → "no change; no frame" (no-churn proven); `--heartbeat` → mints.
2. `node tools/verify-chain.mjs` → clean over the full chain.
3. Playwright-drive `player.html` over the real chain (serve the dir): timeline renders all frames,
   play advances slices, scrub works, diff mode highlights a birth, zero console errors; screenshot
   at 3 points (early reconstructed / mid / genesis) to `shots/`.
4. Report: frame count (reconstructed/witnessed), chain head sha, the genesis frame's events list,
   player drive results, every judgment call.
