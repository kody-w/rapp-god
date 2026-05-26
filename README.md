# 👁️ rapp-god

**A god's-eye view of the [RAPP](https://github.com/kody-w/RAPP) ecosystem** — a public map of every repo,
and a live **drift detector**. It owns no spec and fixes no drift; its one job is to make drift
**impossible to miss**.

**Live dashboard:** <https://kody-w.github.io/rapp-god/>

> Mental model: the ecosystem is many repos, but some truths are supposed to be *one* truth — the
> neighborhood spec, the `BasicAgent` base class, the constitution. The moment a copy of one of those
> forks, the whole thing quietly rots. rapp-god watches every place a truth is duplicated and shows
> you, at a glance, whether they still agree.

## Two lenses

**Lens A — canonical integrity.** For each canonical source (the spec, the sealed codec, the kite
mark, the doorman, the SDK, the string tools), rapp-god keeps a `snapshot/` and compares it live to
the canonical repo. *Has a canonical file moved since we last trusted it?*

**Lens B — cross-repo drift.** Some files must stay **byte-identical across two repos**. rapp-god
fetches both live and compares. `must match` = a real divergence to fix. `watch` = the same name
lives in two homes and a human decides whether that's intended.

The dashboard runs both **in your browser** — fetch the live files, SHA-256 both sides, compare — so
the page is the proof, computed fresh every time you open it.

## What it caught on day one

rapp-god's first survey found the ecosystem already drifting — silently, invisibly, until now:

| Pair | Verdict |
|------|---------|
| `NEIGHBORHOOD_PROTOCOL.md` — RAPP vs canonical spec repo | ⚠️ **drift** (`9b15ced` ≠ `787d585`) |
| `basic_agent.py` — RAPP brainstem vs RAR `@rapp` | ⚠️ **drift** (`701488b` ≠ `641fd31`) |
| `CONSTITUTION.md` — RAPP vs RAR | ⚠️ differ (two homes — your call) |
| `CONSTITUTION.md` — RAPP root vs its bundled brainstem | ⚠️ differ (internal dup) |

That table is the entire argument for this repo. None of it was visible before.

## Run it yourself

```bash
bash check.sh   # both lenses, against the live repos; exits non-zero on must-match drift (the CI signal)
bash sync.sh    # re-pull every canonical into snapshot/ and refresh the manifest hashes (fixes Lens A)
```

`check.sh` is what CI (`.github/workflows/god-drift.yml`) runs on every push and on a schedule, so
drift is caught even when no one is looking. **A red badge means the ecosystem has unreconciled
drift — that's the canary working, not a broken build.** Make it green by reconciling the source
(or, if a divergence is intentional, downgrade that pair from `must match` to `watch` in
`manifest.json`).

`sync.sh` only refreshes Lens A (this repo's own snapshots). Lens B drift is fixed at the source —
rapp-god is an index, not an editor.

## The map

`manifest.json` carries the full ecosystem map (every repo + role), rendered on the dashboard. RAPP —
the platform and the prior "god" repo — is exposed down to its sub-components (the brainstem, the
swarm, the installer, the pages, the specs) so the god's eye sees inside it too.

## How it's wired

- **`manifest.json`** — `tracked` (Lens A: canonical → snapshot, with sizes + hashes), `pairs`
  (Lens B: the cross-repo copies that must agree), and `map` (the whole ecosystem).
- **`snapshot/`** — the mirrored canonical files, readable globally via raw.githubusercontent.com.
- **`index.html`** — the zero-dependency dashboard (GitHub Pages).
- **`check.sh` / `sync.sh`** — the same checks on the command line, and the re-sync.
- **`.github/workflows/god-drift.yml`** — the scheduled signal.

Part of the RAPP ecosystem — see the [map repo](https://github.com/kody-w/rapp-map). MIT © Kody Wildfeuer.
