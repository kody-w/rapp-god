# First RAPP race — blind judging pack

PROBLEM RACED: "Where should the standing guard stand? Name the ecosystem's single
greatest present drift risk and the ONE guard (check, ritual, or watchdog) that would
catch it earliest. Be concrete: what it watches, when it fires."

Seven lanes answered. Each lane is one historical state of the same organism (you do
not know which). SCORED CLASS lanes (A, C, E, G) are ranked against each other.
EXHIBITION CLASS lanes (B, D, F) embody partial/reconstructed bodies — score them on
their own merits, never against the scored class. Frame references are redacted as
[frame-ref] to keep judging blind to era.

---
## Lane A — SCORED
RISK: I am reconciling yesterday's picture while my organs keep moving. My last full-mesh sweep found 13 drift findings, 3 high; reconciliation is still in-flight — and in the ~24 hours since, two organs advanced their default branches unswept, and my open drift count rose 1 → 2 with severity unspecified. The greatest present risk is drift born between sweeps: changes landing in moving organs during an active reconciliation, invisible until the next scheduled full sweep — including regressions of the very fixes in flight.
GUARD: A push-triggered micro-sweep. Watches: any organ's default branch advancing since the last frame. Fires: the moment a frame records a branch advance, it immediately runs a scoped sweep on only those organs against the canonical spec, and stamps the resulting frame DRIFT-CLEAN or DRIFT-FOUND for that organ — never letting an advanced branch enter the biography unaudited. Secondary rule: any drift issue filed without a severity label fires the same check within one frame.
WHY EARLIEST: The pulse already observes branch advances same-day; the scheduled sweep sees them up to a full interval later. Binding the sweep to the advance-event closes a ~24-hour blind window to minutes — and during reconciliation-in-flight, that window is exactly where the high findings could silently regress.
EVIDENCE: [frame-ref] (DRIFT-FOUND, 13 findings/3 high, reconciliation in-flight); [frame-ref] (pulse fires even when idle — the trigger channel exists); [frame-ref] (two organs advanced post-sweep; open drift 1→2, severity unspecified).

---
## Lane B — EXHIBITION
RISK: I am one repo old and I have no spec. My frame records spec_version: null, and every vital — sync, drift_issues, mirrors_identical, last_sweep — is null, not zero. Null means unmeasured, not healthy. The greatest present drift risk is silent fragmentation at first replication: the moment a second repo, mirror, or copied definition of me appears, there will be two claimants to "what RAPP is" and no canonical artifact to arbitrate. Drift born before a source of truth exists is invisible forever after — both copies will look original.
GUARD: A canon-first watchdog. Watches: (1) the count of repos/surfaces carrying my name or definitions, and (2) whether a versioned canonical spec exists and is referenced by each surface. Fires: immediately, at repo-count > 1 OR at any commit that duplicates a definition outside the birth repo, while spec_version is still null. Its demand: no second surface may exist until a spec_version is stamped and the new surface declares which version it mirrors. It also converts null vitals to measured zeros by running the first sweep now.
WHY EARLIEST: Every other guard — mirror diffing, sweep cadence, drift ledgers — presupposes a canon to diff against. This guard fires before divergence is possible, at the replication event itself. A diff-based watchdog catches drift after it exists; this one catches the condition that makes drift undetectable.
EVIDENCE: [frame-ref] (birth): repos: 1, spec_version: null, all vitals null, last_sweep null. Nothing later exists for me.

---
## Lane C — SCORED
RISK: My immune system just learned to forgive — and forgiveness rots silently. Movement I closed RECONCILED partly by waiving 4 findings "with canon citations" and re-baselining 1 detector. In the same frame, the canon itself moved: the ecosystem spec version bumped, and the Lexicon was sealed. A waiver is only true relative to the canon text it cites; the moment canon shifts, a waiver can keep suppressing a finding that is now real drift. My vitals then read the most dangerous number possible: open drift issues 0, verdict RECONCILED — a green that may be manufactured by stale exemptions, not health. With 15 organs advancing branches in one inter-sweep week and a brand-new organ appearing between pulses, the window for a masked finding to metastasize is wide.
GUARD: A waiver-freshness watchdog in the map layer, wired to the waiver ledger and golden drift cases. Each waiver stores the sha256 of the exact canon passage it cites. It fires the moment any canon surface (ecosystem spec, Constitution, Lexicon) changes: it re-hashes every cited passage, and any mismatch auto-reopens the waived finding as a drift issue before the next weekly sweep runs.
WHY EARLIEST: Canon-change-triggered, not sweep-triggered. The weekly sweep would trust the ledger and report RECONCILED for up to seven more days; this guard invalidates a stale waiver at the commit that stales it — the earliest observable moment.
EVIDENCE: [frame-ref] (4 waived + detector re-baselined; spec version bump; lexicon sealed; 15 organs advanced; new organ born; issues 2→0), [frame-ref] (detection + memory plan), [frame-ref] (drift accrues between pulses, 1→2).

---
## Lane D — EXHIBITION
RISK: I ratified my own identity law yesterday — identity hashes derived from owner/slug coordinates — and I am flying blind on whether my 41 repos actually conform to it. My vitals at this frame are all null. Worse, the law itself is brittle by construction: the hash derives from mutable coordinates. One repo rename or ownership transfer and an identity silently detaches from its body — the identity says one thing, the coordinates say another, and every mirror that cached the old hash diverges. Identity drift is the drift that makes all other drift undetectable, because it corrupts the very keys any sweep would join on.
GUARD: An identity ledger watchdog. It holds a signed ledger of (owner, slug, identity-hash) for all repos and (a) recomputes the hash on every repo rename/transfer/creation event and on a daily sweep, firing on any mismatch between computed hash and ledgered identity; (b) fires unconditionally when last-sweep age exceeds 24h — which means it fires the moment it is installed, because last_sweep is null right now.
WHY EARLIEST: The constitution is one day old — nothing downstream has hardened around bad identities yet. Catching a mismatch at the rename event, before any mirror or registry propagates the stale hash, is the earliest possible moment; a periodic mirror-diff would only catch it after divergence already spread.
EVIDENCE: [frame-ref] (identity law ratified); frame vitals (all four null, 41 repos); [frame-refs] (bare births — no sweep ever recorded in my biography).

---
## Lane E — SCORED
RISK: My most frequent writer is about to become my least supervised one. The daily pulse cron appends frames to an append-only spine — and within days, the frontier judgment that shaped this week's frames departs. My conformance suite guards sweeps ("future sweeps validate against it before being trusted"), not writes. A weaker mind's pulse frame with a stale lexicon pin, a missing census pin, or a silently-skipped observation gap becomes permanent chain history the moment it lands. The doorman compounds this: he is born of a frame and will speak whatever the chain says. Drift won't arrive as a dramatic break — it arrives as tomorrow's routine frame, slightly wrong.
GUARD: A pre-append frame gate on the pulse itself. Before any frame is committed: (1) verify-chain against the prior head, (2) the lexicon pin must equal the sealed value or cite a lawful amendment, (3) census/heads present, gaps recorded as events, (4) the candidate frame run through the golden conformance suite's drift classes. Any failure: refuse the append, file a drift issue, ping the weekly heartbeat. It fires daily, at write time.
WHY EARLIEST: Append-only means a bad frame can be superseded but never erased — write time is the only moment prevention exists; heartbeat and scheduled sweeps are post-hoc by days. And the gate is mechanical, so it does not degrade when the frontier mind leaves.
EVIDENCE: Daily pulse wired; frontier access ends within days; suite currently validates sweeps, not frames; lexicon sealed; open drift issues: 0 — the risk is entirely forward.

---
## Lane F — EXHIBITION
RISK: I am 51 repos wide and my vitals are blind — sync: null, drift_issues: null, mirrors_identical: null, last_sweep: null. No sweep has ever confirmed my body agrees with itself. Meanwhile I just did two things that make silent drift lethal: I content-pinned my foundation pillars and adopted a SHA-chained frame pulse at ecosystem scale. Pinned hashes plus live repos plus zero monitoring means any repo can quietly diverge from the registry — or a frame can be emitted off-chain — and nothing in me would notice until the chain is already forked history.
GUARD: A pulse-time chain-and-pin verifier standing on the frame emitter. Watches: every outgoing frame. Fires: at emit, before broadcast, it (1) verifies the new frame's SHA links to the previous frame's hash — refuse to broadcast on mismatch; (2) recomputes the content hashes of the pinned foundation pillars against live HEADs and stamps the result into the frame's vitals, so vitals are never null again; (3) fires an alarm if a pulse interval passes with no frame at all (a silent heart is drift too).
WHY EARLIEST: The pulse is my only recurring public heartbeat — the one moment all repos are summarized into a signed statement. A guard at emit catches a broken link or stale pin at frame N, one interval old, instead of a later ad-hoc sweep discovering forked history.
EVIDENCE: [frame-ref] (pinned foundation registry), [frame-ref] (SHA-chained pulse adopted), frame vitals (all null), [frame-ref] (identity law the chain protects).

---
## Lane G — SCORED
RISK: My detection-to-memory handoff is already tearing. My own vitals disagree with themselves: the last sweep returned DRIFT-FOUND with 13 findings, 3 HIGH, 13 issues filed — yet my drift-issue ledger shows only 1 open issue, severity "unspecified", with zero HIGHs. Somewhere between the mesh sweep and the issue tracker, 12 findings vanished or closed unverified and severity metadata was stripped. The immunity plan says detection + memory close the loop; right now the loop is open, and a HIGH finding can be "reconciled" without anything proving the fix landed. Worse, my witnessed frame already records three observation-gaps — the pulse itself misses events, so I cannot assume the frames will catch this by accident.
GUARD: A ledger-vs-sweep reconciliation check, run at every frame emission (each pulse), not each sweep. It diffs the latest sweep's findings — by finding ID and severity — against open-or-verified-closed drift issues. It fires when: (a) any finding lacks a traceable issue, (b) severity counts disagree (HIGHs in sweep, none in ledger), (c) an issue closed with no re-detection pass over its surface, or (d) an issue carries "unspecified" severity.
WHY EARLIEST: It fires today — two of its conditions are true at this frame. It is a cheap state-diff at pulse cadence, so it beats the next full-mesh sweep by a day and, being state-based, it survives the observation-gaps that blind event-based watching.
EVIDENCE: [frame-ref] (DRIFT-FOUND 13/3-high vs 1 open unspecified; observation-gaps ×3; immunity plan), [frame-ref] (pulse organ adopted).
