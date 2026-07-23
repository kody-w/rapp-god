# PLAN — Crawl the RAPP ecosystem, build a two-tier second brain

**Audience: the model doing the build (Opus).** This is an executable plan, not
prose. Follow the phases in order. Phase 0 is the safety contract — do it first
and never violate it.

Scale at handoff: ~479 repositories under the account (~338 public, ~141
private). The crawl must discover the **unknown** ones too, not just the known
`rapp-*` set.

**You are not alone.** Multiple models build this in parallel. Before writing
anything, read [`CONCURRENCY.md`](CONCURRENCY.md) — partition by file, claim your
scope, rebase before push, never hand-edit generated aggregates. The phases below
assume that protocol.

---

## Phase 0 — The safety contract (read twice, never break)

**The boundary is repository visibility, checked live per repo.**

1. **A repo's `visibility` is ground truth.** `public` → eligible for the public
   brain. `private` → private brain ONLY. Re-check visibility at crawl time; do
   not trust any cached list.
2. **Never copy private content into a public artifact.** Public notes may
   summarize and link *public* repos only. A public note may say "there is a
   private companion" **only if that fact is already public**; otherwise it must
   not even reveal a private repo's existence.
3. **Never transcribe a secret, key, token, credential, customer name, employee
   name, email, address, or financial figure** into *either* brain. The private
   brain stores a **redacted pointer** ("Azure key present in `<repo>/.env` —
   rotate"), never the value.
4. **Guard the seam.** Wire a content gate (secret + denylist + private-name
   scan) as a pre-commit/pre-push hook on THIS public repo, so a private fact
   physically cannot be pushed. Reuse the estate's existing content-gate tool
   (see the private ops handoff) rather than writing a new one.
5. **When unsure, it's private.** Default any ambiguous fact to the private tier.

Ship Phase 0's guard before writing a single public note.

---

## Phase 1 — Crawl & classify (discover known + unknown)

```bash
# Full inventory (both visibilities), dated:
gh repo list <owner> --limit 500 --json \
  name,visibility,description,updatedAt,pushedAt,isArchived,isFork,primaryLanguage,repositoryTopics \
  > inventory.json
```

Then classify every repo into an ecosystem **cluster** (platform engine, release
train / rings, agent-swarm, marketplace, company/IP, tooling/infra, experiments,
archived). Emit `classification.json`:

```json
{ "repo": "...", "visibility": "public|private", "cluster": "...",
  "sensitivity": "public|internal|secret", "role": "one line", "unknown": false }
```

- **Unknown-unknowns**: any repo that matches no known cluster → `unknown:true`,
  routed to a triage list. Surfacing these is a primary goal.
- For each **public** repo: fetch README + key manifests (`roadmap.json`,
  `ring.json`, `VERSION`, spec/manifest files) via `gh api .../contents` — public.
- For each **private** repo: metadata + a safe one-line summary only. Do NOT
  pull raw file bodies into anything that could reach the public tier.
- Run the estate secret-scan across ALL repos; record hits as redacted pointers
  in the private tier and (if public) as urgent remediation items.

---

## Phase 2 — Synthesize the two brains

Reuse the proven structure (established elsewhere in this estate):
**MOC / question-index Home over a PARA-lite spine, atomic claim-titled notes,
one bolded BLUF line per note, consistent frontmatter.** Do not reinvent it.

**Public brain (this repo, `public/`):**
- `Home.md` — a question-index ("What is RAPP?", "What's public?", "Where do I
  start?") linking cluster MOCs.
- Cluster MOCs (platform, rings, marketplace, tooling) linking per-repo atomic
  notes — **public repos only**.
- `glossary.md`, `llms.txt` (machine entry), and a visual (reuse the
  `rapp-roadmap` board pattern — single-file page over CORS-open static JSON).

**Private brain (a private repo you designate, or an existing private hub):**
- The full graph: public + private clusters, IP posture, security findings
  (redacted), cross-links. This is where private detail lives — never here.
- May link to public notes; public notes never embed private content.

**Cross-tier rule:** links go private→public freely; public→private never
reveals private content (a public note may reference a public repo, full stop).

---

## Phase 3 — Keep it live (static API + Pages)

Reuse the `rapp-static-api/1.0` pattern (as on the public roadmap board):
- One hand-authored `manifest.json` → `build.py` generates
  `registry.json` + `api/v1/{status,map}.json` + content-addressed frames.
- A single-file Pages page fetches the JSON CORS-open and renders the public map
  (map view + search + the roadmap board's multi-lens views).
- CI rebuilds on push + on a schedule. **Public brain gets Pages; the private
  brain never gets Pages** (private repo, no public surface).

---

## Phase 4 — Guardrails against rot & leak (recurring)

- **Leak audit (scheduled):** re-run the secret-scan, plus a check "does any
  public note reference a private repo or private content?" — fail loudly.
- **Freshness:** stale-note sweep (bump `updated`; review >6-month-old notes).
- **Orphans:** every note reachable from a Home/MOC; sweep broken links.
- **Completeness critic:** "which repo/cluster is still undocumented, which
  unknown-unknown is untriaged?" → the next crawl's work-list. Log what was
  skipped; never silently cap coverage.

---

## Definition of done

- [ ] Phase-0 content gate live on this repo (private facts can't be pushed).
- [ ] `inventory.json` + `classification.json` covering all ~479 repos, with an
      `unknown` triage list.
- [ ] Public brain in `public/` + a live Pages map; `llms.txt` present.
- [ ] Private brain in the private tier (full picture, redacted secrets).
- [ ] A leak audit that passes, and is scheduled to keep passing.

**"Done" means the live public page serves the map and the leak audit is green —
exercised, with the run/URL cited. A false "done" that leaks is the cardinal
sin here.**
