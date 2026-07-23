<!-- (c) 2026 Kody Wildfeuer · part of the RAPP ecosystem (rapp-god) -->

# Grail Scan — certifying a commit against the full spec corpus with a neuron swarm

> **Spec id:** `rapp-grail-scan/1.0` · **status:** additive, advisory gate · **home:** kody-w/rapp-god
>
> **Authority correction:** this historical advisory procedure is not RAPP/1
> acceptance and cannot bless identity, registry freshness, signatures, or
> owner decisions. Technical authority is the pinned RAPP/1 rev-5 spec.
> Federal governance retains only its public source commit/tree pin because
> the local content is private-boundary withheld. Ratification and owner
> decisions therefore fail closed. All four owner blockers remain open.
>
> A *grail* commit is one that the canonical corpus would bless: it violates no spec, and it leaves no spec stale. Grail Scan is the **bidirectional** procedure that proves it — a fine-grained neuron swarm reads the whole corpus against the commit, **and the commit against the whole corpus**, then a synthesis cortex issues a verdict. It is the swarm formalization of rapp-god's existing job (canonical integrity + cross-repo drift) and the [DRIFT_TRIANGLE].

---

## 0. Why a swarm

The corpus is large (god + RAPP-Bible + every repo's SPEC/GRAIL/CONSTITUTION). A single reviewer holds it shallowly. **One neuron per spec file** holds each slice at full fidelity, in parallel, cheaply — so nothing is skimmed and every finding is reported. The grail verdict is only as trustworthy as its smallest unit of attention; the swarm makes that unit one file.

## 1. The two directions (both are required)

A commit is grail only if **both** hold:

1. **commit → specs (compliance):** the diff violates no MUST/SHALL in any spec it touches. (Does it break an invariant, a schema, a kind taxonomy, the append-only law, a trademark/licence rule?)
2. **specs → commit (freshness / anti-drift):** no spec is left **contradicted or stale** by the commit. (Does a spec now describe the repo wrongly? Does the commit introduce a primitive the corpus has no slot for and must register?)

Direction 1 keeps the commit honest. Direction 2 keeps the **corpus** honest. A commit that adds a genuinely new primitive is *not* a violation — it is a **registration debt**: grail requires the spec be amended in the same change-set, not that the primitive be removed.

## 2. The procedure

```
INPUT  : a commit/PR (the change-set) + the spec corpus (god registry → every tracked SPEC/GRAIL/CONSTITUTION)
PHASE 1 — NEURONS (parallel, one per spec file, as small as you can divide it):
  each neuron READS exactly one spec file + the commit's relevant surface, and returns:
    { file, defines, relevance: high|med|low,
      violations: [ {rule, where, severity} ],          // direction 1
      staleness:  [ {claim, nowFalseBecause} ],          // direction 2
      registrationDebt: [ {newPrimitive, mustRegisterIn} ] }
PHASE 2 — SYNTHESIS CORTEX (one high-effort agent):
  merges all neurons → a VERDICT:
    grail: true|false
    blocking:    [ violations that MUST be fixed before merge ]
    debts:       [ spec amendments / registry entries owed in this change-set ]
    drift:       [ specs the commit makes stale, with the exact edit ]
    full_fidelity: [ every neuron's finding, nothing dropped ]
```

A reference harness is rapp-god's neuron-swarm runner (one `parallel()` agent per file, then a judge) — the same shape used to evaluate the Moment platform against the corpus.

## 3. The grail rule

- **GRAIL = true** ⇔ `blocking == []` **and** every `debt` is satisfied **inside the same change-set** (the spec is amended / the registry entry added alongside the code). A new primitive with its registration is grail; the same primitive without it is **not** (it is uncodified drift).
- **GRAIL = false** ⇒ the report lists the exact blocking violations and owed amendments. Nothing merges to a canonical `main` until grail (advisory by default; a repo MAY make it a required check).

## 4. Conformance & permanence (so the scan itself is honest)

- The scan reads **all legacy forms** of every record/id it encounters and judges against the **canonical** one (mirrors the eternity compatibility contract).
- Verdicts are **append-only artifacts** (commit the grail report next to the change-set); the git history of grail reports is itself the audit trail — the same git-scrape discipline rapp-god already uses.
- The scan **never rewrites** a spec or a commit; it only reports. Amendments are authored by humans/agents and re-scanned.

## 5. Worked example (this very change-set)

Running Grail Scan on the **Moment platform** commit against god + RAPP-Bible produced:

- **blocking:** none (Moment is additive; it breaks no existing MUST).
- **debts (must accompany the change-set):** register **`rapp-moment/1.0`** and **`rapp-eternity/1.0`** in god (`map[]`, `tracked[]`, `parts[]`) and mirror them in RAPP-Bible (`SPEC/moment`, `SPEC/eternity`).
- **drift:** rapp-god README + `repos/rapp-commons.md` still call rapp-commons a *"cross-estate signed event stream / global hangout"* — stale; must become the **Moment** framing.
- **governance:** CONSTITUTION **Article XLVI** (rappid IS the URL, one v2 format) and **XXXIV** (never regenerate rappid; only parent-lineage) must be reconciled — Eternity rappids (`rappid:<slug>:<64hex>`) are a **second, broader namespace**, and **transferable deeds** are a **second, orthogonal chain** (the rappid stays immutable; the *deed* moves). New kinds `moment`/`keeper`/`dimension` are a kind-event Article XLVI.2 says requires amending the article.

That report **is** the grail verdict for the Moment work: not blocking, but owing four registrations and one Article XLVI amendment to be fully grail.

---

*Run it before every canonical merge. The swarm holds the whole book so the commit can be blessed by it — and so the book is corrected by the commit.*
