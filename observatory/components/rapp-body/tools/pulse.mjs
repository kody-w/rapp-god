#!/usr/bin/env node
// tools/pulse.mjs — the WITNESSED frame-taker (Node >=20, zero npm deps).
//
// Takes one live slice of the RAPP organism and, unless nothing material changed,
// mints a `body.pulse` frame that chains onto the biography. A slice has three organs:
//
//   skeleton — the ecosystem-spec version + sha256 as served from each of its three
//              homes (RAPP, rapp-god, rapp-map; equality across them is itself a vital
//              sign) + the spine registry.json / foundation.json shas.
//   census   — per cataloged repo: default-branch head sha, pushed_at, created_at, layer,
//              a lifecycle status; plus born[] / vanished[] vs the previous frame.
//   vitals   — the latest mesh-sweep verdict + drift counts (sweeps/latest.json, optional),
//              the open drift() issue census, and mirrors_identical.
//
// A source it cannot read becomes an explicit `observation-gap` event — NEVER silently
// thinner data (the false-green lesson: absence must be visible).
//
// DOCTRINE — an observation gap is TRANSPORT, not biography (the 429/403 false-vanish fix):
//   • A repo unreadable this run but present last frame KEEPS its last-known census entry
//     (stale:true), emits an observation-gap, and NEVER yields born/vanish/census-change.
//   • `vanish` requires POSITIVE evidence: HTTP 404 on the repo, confirmed on TWO
//     consecutive runs (present → 404 → 404). 429/403/network are blindness, not absence.
//   • Coherence gate: if ANY spec home is unreadable, or >20% of census repos are
//     transport-unreadable, pulse EXITS 3 ("slice incoherent — refusing to mint") and
//     mints nothing — unless --force-degraded. CI always runs WITH GITHUB_TOKEN.
//   • The no-churn fingerprint EXCLUDES observation-gap events and stale markers entirely.
//
// No-churn rule (hard): if skeleton+census+vitals are materially identical to the
// previous frame (timestamps + gaps + stale markers ignored), DO NOT mint — print
// "no change; no frame".  --heartbeat, --birth, and --events-file override it.
//
//   node tools/pulse.mjs
//   node tools/pulse.mjs --heartbeat          # force a liveness frame
//   node tools/pulse.mjs --birth --lexicon-sha <64hex>
//   node tools/pulse.mjs --events-file events.json
//   node tools/pulse.mjs --force-degraded     # mint even when the slice is incoherent
//   node tools/pulse.mjs --dry-run            # build + gate a candidate; write no state
//
// Exit codes: 0 = minted/dry-run/clean no-change · 1 = internal error
//             3 = slice incoherent · 4 = pre-append frame gate refused.
//
// Anonymous-safe; uses GITHUB_TOKEN when present; honors RAPP_CACHE_DIR (see _gh.mjs).

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { repoMeta, repoHead, rawFile, driftIssues, usingCache } from "./_gh.mjs";
import { SPEC_HOMES, SPINE, unionCensus } from "./_census.mjs";
import {
  buildFrame, writeFrame, writeIndex, writeVitals, readChain, listFrameFiles, readFrameFile,
  materialFingerprint, FRAMES_DIR, REPO_ROOT, KIND_WITNESSED, KIND_RECONSTRUCTED, readBodyId,
} from "./_frame.mjs";
import { printGateResult, validateCandidateFile } from "./frame-gate.mjs";

const HEARTBEAT = process.argv.includes("--heartbeat");
const BIRTH = process.argv.includes("--birth");
const DRY_RUN = process.argv.includes("--dry-run");
const LEXICON_SHA_INDEX = process.argv.indexOf("--lexicon-sha");
const LEXICON_SHA = LEXICON_SHA_INDEX === -1 ? null : process.argv[LEXICON_SHA_INDEX + 1];
const EVENTS_FILE_INDEX = process.argv.indexOf("--events-file");
const HAS_EVENTS_FILE = EVENTS_FILE_INDEX !== -1;
const EVENTS_FILE = HAS_EVENTS_FILE ? process.argv[EVENTS_FILE_INDEX + 1] : null;
const FORCE_DEGRADED = process.argv.includes("--force-degraded");
const INCOHERENT_PCT = 0.20; // >20% of census repos transport-unreadable ⇒ slice incoherent
const OWNER_USER = "kody-w";
const nowIso = () => new Date().toISOString();

function gateTemporaryCandidate(frame) {
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "rapp-body-frame-gate-"));
  const candidatePath = path.join(tempDir, `${frame.seq}.candidate.json`);
  try {
    fs.writeFileSync(candidatePath, JSON.stringify(frame, null, 2) + "\n");
    return validateCandidateFile(candidatePath);
  } finally {
    fs.rmSync(tempDir, { recursive: true, force: true });
  }
}

export function readEventsFile(filePath) {
  if (!filePath || filePath.startsWith("--")) {
    throw new Error("--events-file requires a path");
  }
  let events;
  try {
    events = JSON.parse(fs.readFileSync(path.resolve(filePath), "utf8"));
  } catch (e) {
    throw new Error(`--events-file could not read valid JSON from ${filePath}: ${e.message}`);
  }
  if (!Array.isArray(events)) {
    throw new Error("--events-file must contain a JSON array");
  }
  events.forEach((event, index) => {
    if (!event || typeof event !== "object" || Array.isArray(event)) {
      throw new Error(`--events-file event ${index} must be an object`);
    }
    if (typeof event.type !== "string" || !event.type.trim()) {
      throw new Error(`--events-file event ${index} is missing type`);
    }
    if (typeof event.text !== "string" || !event.text.trim()) {
      throw new Error(`--events-file event ${index} is missing text`);
    }
  });
  return events;
}

// ---- skeleton -------------------------------------------------------------------------

async function gatherSkeleton() {
  const homes = {};
  let specObj = null, specVersion = null;
  const readableShas = [];
  const gaps = [];

  for (const [key, h] of Object.entries(SPEC_HOMES)) {
    const r = await rawFile(h.owner, h.repo, h.ref, h.path);
    homes[key] = {
      repo: `${h.owner}/${h.repo}`, path: h.path, label: h.label,
      present: r.ok, sha256: r.ok ? r.sha256 : null,
    };
    if (r.ok) {
      readableShas.push(r.sha256);
      if (!specObj) { try { specObj = JSON.parse(r.text); specVersion = specObj.version || null; } catch {} }
    } else {
      gaps.push({ type: "observation-gap", source: `spec-home:${key}`, detail: `${homes[key].repo}/${h.path} unreadable (${r.error})` });
    }
  }

  // mirrors_identical only means something with >=2 readable homes.
  let mirrors_identical = null;
  const readableCount = Object.values(homes).filter((h) => h.present).length;
  if (readableCount >= 2) mirrors_identical = new Set(readableShas).size === 1;

  // spine registry + foundation content shas
  const sr = await rawFile(SPINE.owner, SPINE.repo, SPINE.ref, SPINE.registry);
  const sf = await rawFile(SPINE.owner, SPINE.repo, SPINE.ref, SPINE.foundation);
  let spineObj = null;
  if (sr.ok) { try { spineObj = JSON.parse(sr.text); } catch {} }
  else gaps.push({ type: "observation-gap", source: "spine:registry", detail: `unreadable (${sr.error})` });
  if (!sf.ok) gaps.push({ type: "observation-gap", source: "spine:foundation", detail: `unreadable (${sf.error})` });

  const skeleton = {
    spec_version: specVersion,
    homes,
    mirrors_identical,
    spine: { registry_sha256: sr.ok ? sr.sha256 : null, foundation_sha256: sf.ok ? sf.sha256 : null },
  };
  return { skeleton, specObj, spineObj, gaps };
}

// ---- census ---------------------------------------------------------------------------
//
// DOCTRINE: an observation gap is TRANSPORT, not biography. A repo unreadable this run
// but present last frame KEEPS its last-known census entry (stale:true), emits an
// observation-gap, and NEVER produces a vanish/born/census-change. A `vanish` requires
// POSITIVE evidence: an HTTP 404 on the repo itself, confirmed on TWO consecutive runs
// (present → 404 `absent_unconfirmed` → 404 `vanished`). 429/403/network are never
// evidence of absence — only of our own blindness.
//
// Per-repo lifecycle status, carried in the census entry so the next run can reason:
//   present            HTTP 200 — live, fresh head_sha
//   stale              transport-unreadable this run — carrying last-known forward
//   absent_unconfirmed one HTTP 404 seen (positive but unconfirmed) — carrying forward
//   absent             steady 404 (e.g. a catalog name that never resolved) — no event
//   vanished           two consecutive 404s — dropped from census, emits `vanish`
//   unreadable         never-before-seen repo, unreadable on first sight

function prevStatusOf(entry) {
  if (!entry) return "none";
  if (entry.status) return entry.status;
  return entry.reachable ? "present" : "absent"; // legacy frames (pre-doctrine) had only `reachable`
}

// PURE decision table (unit-testable) — the heart of the doctrine. Given the previous
// frame's lifecycle status and THIS run's observation code, decide what happens. A
// transport failure never yields born/vanish/present; a vanish needs two consecutive 404s.
//   code: 200 | 404 | "transport"
export function classifyObservation(prevStatus, code) {
  const presentish = prevStatus === "present" || prevStatus === "stale";
  if (code === 200) {
    return { status: "present", present: true, born: !presentish && prevStatus !== "absent_unconfirmed", vanish: false, carry: false, gap: false };
  }
  if (code === 404) {
    if (presentish) return { status: "absent_unconfirmed", present: false, born: false, vanish: false, carry: true, gap: false };
    if (prevStatus === "absent_unconfirmed") return { status: "vanished", present: false, born: false, vanish: true, carry: false, gap: false };
    return { status: "absent", present: false, born: false, vanish: false, carry: false, gap: false };
  }
  // transport (429/403/network/timeout/cache-miss) — blindness, never evidence
  if (presentish || prevStatus === "absent_unconfirmed") {
    return { status: prevStatus === "absent_unconfirmed" ? "absent_unconfirmed" : "stale", present: false, born: false, vanish: false, carry: true, gap: true };
  }
  if (prevStatus === "absent") return { status: "absent", present: false, born: false, vanish: false, carry: false, gap: true };
  return { status: "unreadable", present: false, born: false, vanish: false, carry: false, gap: true };
}

async function gatherCensus(rows, prevByName) {
  const repos = [];
  const gaps = [];
  const born = [];
  const vanished = [];
  const headsAdvanced = [];
  let transportUnreadable = 0; // repos we could not read due to transport (feeds the coherence gate)

  for (const r of rows) {
    const prev = prevByName.get(r.name) || null;
    const prevStatus = prevStatusOf(prev);
    const base = { name: r.name, owner: r.owner, layer: r.layer, category: r.category };

    const meta = await repoMeta(r.owner, r.name);
    const code = meta.ok ? 200 : (meta.status === 404 ? 404 : "transport");
    const act = classifyObservation(prevStatus, code);

    if (act.gap && code === "transport") {
      transportUnreadable++;
      gaps.push({ type: "observation-gap", source: `repo:${r.owner}/${r.name}`, detail: `metadata unreadable (${meta.error})`, transport: true });
    }
    if (act.born) born.push(r.name);
    if (act.vanish) { vanished.push(r.name); continue; } // dropped from census (positively gone)

    if (act.status === "present") {
      // Live repo — read the head; a transport failure on the head alone carries last-known.
      const head = await repoHead(r.owner, r.name);
      let head_sha = head.ok ? head.sha : (prev?.head_sha ?? null);
      let head_stale = false;
      if (!head.ok) {
        if (head.status !== 404) {
          transportUnreadable++;
          head_stale = true;
          gaps.push({ type: "observation-gap", source: `repo:${r.owner}/${r.name}`, detail: `head commit unreadable (${head.error})`, transport: true });
        } else {
          head_sha = null;
        }
      }
      const entry = {
        ...base, status: "present", reachable: true, head_sha,
        pushed_at: meta.data.pushed_at || prev?.pushed_at || null,
        created_at: meta.data.created_at || prev?.created_at || null,
        archived: !!meta.data.archived,
      };
      if (head_stale) entry.head_stale = true;
      repos.push(entry);
      if (prev && prev.head_sha && head.ok && head.sha && prev.head_sha !== head.sha) headsAdvanced.push(r.name);
      continue;
    }

    // Non-present outcomes: carry last-known forward (stale/unconfirmed) or record steady absence.
    if (act.carry) {
      repos.push({ ...base, status: act.status, reachable: false, stale: true,
        head_sha: prev?.head_sha ?? null, pushed_at: prev?.pushed_at ?? null, created_at: prev?.created_at ?? null });
    } else {
      const entry = { ...base, status: act.status, reachable: false, head_sha: null };
      if (act.gap) entry.stale = true;
      repos.push(entry);
    }
  }

  repos.sort((a, b) => (a.name.toLowerCase() < b.name.toLowerCase() ? -1 : 1));
  const presentCount = repos.filter((r) => r.status === "present").length;
  return { repos, born, vanished, gaps, headsAdvanced, presentCount, transportUnreadable };
}

// ---- vitals ---------------------------------------------------------------------------

function readSweep() {
  const p = path.join(REPO_ROOT, "sweeps", "latest.json");
  if (!fs.existsSync(p)) return null;
  try { return JSON.parse(fs.readFileSync(p, "utf8")); } catch { return null; }
}

function severityOf(title) {
  const t = String(title).toLowerCase();
  if (/\b(critical|crit)\b/.test(t)) return "high";
  if (/\bhigh\b/.test(t) || /^\s*\[?h(igh)?\]?[:\-]/.test(t)) return "high";
  if (/\b(med(ium)?)\b/.test(t)) return "medium";
  if (/\blow\b/.test(t)) return "low";
  return "unspecified";
}

async function gatherVitals(censusNames, skeleton) {
  const sweep = readSweep();
  const sync = sweep
    ? {
        source: "sweeps/latest.json",
        swept_at: sweep.swept_at || null,
        verdict: sweep.verdict || null,
        findings: sweep.findings ?? null,
        high: sweep.by_severity?.high ?? null,
        issues_filed: sweep.issues_filed ?? null,
        reconciliation: sweep.reconciliation || null,
        plan: sweep.plan || null,
      }
    : null;

  const gaps = [];
  let drift_issues = null;
  const ds = await driftIssues(OWNER_USER);
  if (ds.ok) {
    const inCensus = new Set(censusNames.map((n) => n.toLowerCase()));
    const mine = ds.items.filter((i) => {
      const repo = (i.repository_url || "").split("/").pop() || "";
      return inCensus.has(repo.toLowerCase());
    });
    const by = { high: 0, medium: 0, low: 0, unspecified: 0 };
    let oldest = null;
    for (const i of mine) {
      by[severityOf(i.title)]++;
      if (!oldest || i.created_at < oldest) oldest = i.created_at;
    }
    drift_issues = { open: mine.length, by_severity: by, oldest_opened: oldest };
  } else {
    gaps.push({ type: "observation-gap", source: "drift-issues", detail: `open drift() issue search unreadable (${ds.error})` });
  }

  return { vitals: { sync, drift_issues, mirrors_identical: skeleton.mirrors_identical, last_sweep: sweep ? { swept_at: sweep.swept_at, verdict: sweep.verdict } : null }, sweep, gaps };
}

// ---- events (derived: births, vanishings, spec-version change, drift delta, genesis) ---

function deriveEvents({ isGenesis, prevFrame, skeleton, census, vitals, sweep, allGaps }) {
  const events = [];

  if (isGenesis) {
    events.push({ type: "genesis", text: "The witnessed biography opens: the body begins pulsing live. Every earlier frame is reconstructed from git history; from here the pulse observes the organism directly." });
    events.push({ type: "biography-born", text: "kody-w/rapp-body born — the organism's own public, sha256-chained biography (rapp-frame/2.0), the same organ a twin carries, now at ecosystem scale." });
    events.push({ type: "immune-system", text: "PLAN-drift-immunity in flight: the mesh sweep DETECTS drift, these frames REMEMBER it. Detection + memory close the loop." });
  }

  // Sweep event: on genesis, or whenever the sweep is newer than the last frame recorded.
  if (sweep) {
    const prevSweptAt = prevFrame?.payload?.vitals?.sync?.swept_at || null;
    if (isGenesis || (sweep.swept_at && sweep.swept_at !== prevSweptAt)) {
      events.push({
        type: "sweep",
        verdict: sweep.verdict || null,
        findings: sweep.findings ?? null,
        high: sweep.by_severity?.high ?? null,
        issues_filed: sweep.issues_filed ?? null,
        text: `Full-mesh ecosystem sweep: ${sweep.verdict} — ${sweep.findings} findings, ${sweep.by_severity?.high ?? "?"} high. ${sweep.issues_filed} drift() issue(s) filed; reconciliation ${sweep.reconciliation}.`,
      });
    }
  }

  // Spec version change vs previous frame.
  const prevVer = prevFrame?.payload?.skeleton?.spec_version ?? null;
  if (skeleton.spec_version && prevVer && skeleton.spec_version !== prevVer) {
    events.push({ type: "spec-version-change", from: prevVer, to: skeleton.spec_version, text: `ecosystem-spec version ${prevVer} → ${skeleton.spec_version}.` });
  }

  // Mirror divergence is a first-class drift signal.
  if (skeleton.mirrors_identical === false) {
    events.push({ type: "mirror-divergence", text: "ecosystem-spec homes DIVERGE — the three published copies no longer sha256-match. This is drift the day it happens." });
  }

  // Births / vanishings of organs vs the previous frame. Both come ONLY from positive
  // evidence (200 for born, two-consecutive-404 for vanish) — never from a gap.
  if (census.born.length) events.push({ type: "birth", repos: census.born, text: `${census.born.length} organ(s) appeared since the last frame: ${census.born.join(", ")}.` });
  if (census.vanished.length) events.push({ type: "vanish", repos: census.vanished, text: `${census.vanished.length} organ(s) confirmed gone (two consecutive HTTP 404s): ${census.vanished.join(", ")}.` });

  // Heads advanced: organs whose live default-branch head_sha moved since the last frame
  // (gap-free positive activity — this is what a healing/movement frame witnesses).
  if (census.headsAdvanced && census.headsAdvanced.length) {
    const list = census.headsAdvanced;
    const shown = list.slice(0, 12).join(", ") + (list.length > 12 ? `, +${list.length - 12} more` : "");
    events.push({ type: "heads-advanced", repos: list, text: `${list.length} organ(s) advanced their default branch since the last frame: ${shown}.` });
  }

  // Drift-issue delta vs previous frame.
  const prevOpen = prevFrame?.payload?.vitals?.drift_issues?.open ?? null;
  const nowOpen = vitals.drift_issues?.open ?? null;
  if (prevOpen !== null && nowOpen !== null && nowOpen !== prevOpen) {
    events.push({ type: "drift-delta", from: prevOpen, to: nowOpen, text: `open drift() issues ${prevOpen} → ${nowOpen}.` });
  }

  // Every unreadable source is surfaced explicitly.
  for (const g of allGaps) events.push(g);

  return events;
}

// ---- main -----------------------------------------------------------------------------

async function main() {
  const suppliedEvents = HAS_EVENTS_FILE ? readEventsFile(EVENTS_FILE) : [];
  if (BIRTH && !/^[0-9a-f]{64}$/.test(LEXICON_SHA || "")) {
    throw new Error("--birth requires --lexicon-sha followed by exactly 64 lowercase hex characters");
  }

  console.log(`pulse — cache: ${JSON.stringify(usingCache())}${HEARTBEAT ? "  [--heartbeat]" : ""}${BIRTH ? "  [--birth]" : ""}${DRY_RUN ? "  [--dry-run]" : ""}${HAS_EVENTS_FILE ? `  [--events-file ${EVENTS_FILE}]` : ""}`);

  const chain = readChain();
  const prevFrame = chain[chain.length - 1] || null;
  const witnessedCount = chain.filter((f) => f.kind === KIND_WITNESSED).length;
  const isGenesis = witnessedCount === 0;
  // The previous frame's census, indexed by name — the last-known truth we carry forward
  // when this run cannot read a source. Gaps NEVER erase this; only positive evidence does.
  const prevByName = new Map();
  if (prevFrame) for (const r of (prevFrame.payload.census?.repos || [])) prevByName.set(r.name, r);

  // Gather the slice.
  const sk = await gatherSkeleton();

  // COHERENCE GATE (the false-green fix): a slice built on unreadable sources is not a
  // biography — it is our own blindness. If ANY spec home is unreadable, or >20% of the
  // census repos are transport-unreadable, we REFUSE to mint (exit 3) rather than record
  // noise as fact. --force-degraded overrides (records stale/carried-forward data, clearly
  // marked). CI always runs with GITHUB_TOKEN, so it never trips this gate.
  const homesUnreadable = Object.values(sk.skeleton.homes).filter((h) => !h.present).map((h) => h.repo);
  if (!sk.specObj) {
    console.error(`slice incoherent — refusing to mint: could not read ecosystem-spec from ANY home (${homesUnreadable.join(", ") || "all"}). Re-run with a GITHUB_TOKEN.`);
    process.exit(3);
  }
  const rows = unionCensus(sk.specObj, sk.spineObj);
  const cen = await gatherCensus(rows, prevByName);
  const vt = await gatherVitals(cen.repos.map((r) => r.name), sk.skeleton);
  const allGaps = [...sk.gaps, ...cen.gaps, ...vt.gaps];

  const pctUnreadable = rows.length ? cen.transportUnreadable / rows.length : 0;
  const incoherent = homesUnreadable.length > 0 || pctUnreadable > INCOHERENT_PCT;
  if (incoherent && !FORCE_DEGRADED) {
    console.error(`slice incoherent — refusing to mint (spec homes unreadable: ${homesUnreadable.length}/3${homesUnreadable.length ? " [" + homesUnreadable.join(", ") + "]" : ""}; transport-unreadable repos: ${cen.transportUnreadable}/${rows.length} = ${(pctUnreadable * 100).toFixed(0)}%). An observation gap is transport, not biography. Re-run with a GITHUB_TOKEN (CI always does), or pass --force-degraded to mint a clearly-marked stale slice.`);
    process.exit(3);
  }
  if (incoherent && FORCE_DEGRADED) {
    const action = DRY_RUN ? "building a DEGRADED dry-run candidate" : "minting a DEGRADED slice";
    console.warn(`[--force-degraded] ${action}: ${homesUnreadable.length} home(s) unreadable, ${cen.transportUnreadable}/${rows.length} repos transport-unreadable (carried forward as stale).`);
  }

  // The MATERIAL slice (skeleton+census+vitals) drives the no-churn decision. By doctrine
  // the fingerprint IGNORES observation gaps and stale markers entirely (see _frame.mjs),
  // so a rate-limited run over an unchanged body fingerprints identically → no churn.
  const materialPayload = { skeleton: sk.skeleton, census: { repos: cen.repos }, vitals: vt.vitals };
  const fp = materialFingerprint(materialPayload);
  const prevFp = prevFrame ? materialFingerprint(prevFrame.payload) : null;

  console.log(`slice: ${cen.repos.length} repos (${cen.presentCount} present, ${cen.transportUnreadable} transport-unreadable), spec ${sk.skeleton.spec_version}, mirrors_identical=${sk.skeleton.mirrors_identical}, gaps=${allGaps.length}`);
  console.log(`fingerprint: ${fp.slice(0, 16)}  prev: ${prevFp ? prevFp.slice(0, 16) : "—"}  genesis=${isGenesis}`);

  if (!isGenesis && prevFp === fp && !HEARTBEAT && !BIRTH && !HAS_EVENTS_FILE) {
    console.log("no change; no frame");
    return;
  }

  const events = deriveEvents({ isGenesis, prevFrame, skeleton: sk.skeleton, census: cen, vitals: vt.vitals, sweep: vt.sweep, allGaps });
  if (HEARTBEAT) events.unshift({ type: "heartbeat", text: "weekly liveness pulse — the body is alive even when nothing changed." });
  if (BIRTH) {
    events.unshift(
      { type: "birth", text: "The body is born: kody-w/rapp-body publishes today. Cradle-to-now biography — 21 reconstructed frames from git archaeology, witnessed pulses since 2026-07-08 — now public, chained, and verifiable by anyone." },
      { type: "lexicon-sealed", lexicon_sha: LEXICON_SHA, text: "The Lexicon is sealed: LEXICON.md at the species root (Constitution Article LII), sha256 pinned in this frame as lexicon_sha. The body is born speaking a sealed language — Nine Words, one operator, one wire, three shelves, nine rulings." },
      { type: "heal-complete", text: "Movement I closes RECONCILED: the R3 full-mesh re-sweep adjudicated 7 findings — 2 fixed and merged upstream, 4 waived with canon citations, 1 detector re-baselined. Gate: zero unexplained drift." },
      { type: "immune-system-executable", text: "The immune system gained an executable memory: golden drift cases with expected rulings and a waiver ledger now live in the map layer — future sweeps validate themselves against fossilized judgment before their verdicts are trusted." },
    );
  }
  if (HAS_EVENTS_FILE) events.unshift(...suppliedEvents);

  const ts = nowIso();
  const degraded = incoherent && FORCE_DEGRADED;
  const payload = {
    taken_ts: ts,
    ...(BIRTH ? { lexicon_sha: LEXICON_SHA } : {}),
    provenance: degraded
      ? { mode: "witnessed", degraded: true, degraded_reason: { homes_unreadable: homesUnreadable, transport_unreadable: cen.transportUnreadable } }
      : { mode: "witnessed" },
    skeleton: sk.skeleton,
    census: {
      basis: degraded ? "witnessed (degraded — some entries carried forward as stale)" : "witnessed",
      count: cen.repos.length,
      present: cen.presentCount,
      transport_unreadable: cen.transportUnreadable,
      repos: cen.repos,
      born: cen.born,
      vanished: cen.vanished,
    },
    vitals: vt.vitals,
    events,
  };

  const seq = prevFrame ? prevFrame.seq + 1 : 0;
  const frame = buildFrame({ kind: KIND_WITNESSED, seq, ts, payload, parent_sha: prevFrame ? prevFrame.sha256 : null });
  const gateResult = gateTemporaryCandidate(frame);
  printGateResult(gateResult);
  if (!gateResult.allowed) {
    console.error("pulse: candidate refused; no frame, index, or vitals state was written");
    process.exitCode = 4;
    return;
  }
  if (DRY_RUN) {
    console.log(`DRY RUN: candidate seq ${seq} passed the gate (${events.length} event(s)); no frame, index, or vitals state was written`);
    return;
  }

  writeFrame(frame);

  const frames = readChain();
  writeIndex(frames);

  const health = {
    spec_version: sk.skeleton.spec_version,
    mirrors_identical: sk.skeleton.mirrors_identical,
    repos_total: cen.repos.length,
    repos_present: cen.presentCount,
    transport_unreadable: cen.transportUnreadable,
    degraded,
    born_recent: cen.born,
    vanished_recent: cen.vanished,
    heads_advanced_recent: cen.headsAdvanced,
    drift_sweep: vt.vitals.sync ? { verdict: vt.vitals.sync.verdict, findings: vt.vitals.sync.findings, high: vt.vitals.sync.high } : null,
    open_drift_issues: vt.vitals.drift_issues?.open ?? null,
    observation_gaps: allGaps.length,
  };
  writeVitals(frame, health);

  console.log(`\nMINTED ${isGenesis ? "GENESIS " : ""}frame seq ${seq}  sha256 ${frame.sha256.slice(0, 16)}…  (${events.length} events)`);
  console.log("events:");
  for (const e of events) console.log(`  • ${e.type}${e.text ? " — " + e.text : e.detail ? " — " + e.detail : ""}`);
  console.log(`\nframes/index.json + vitals.json updated. chain length: ${frames.length}`);
}

// Only run when executed directly (so importing this module — e.g. to unit-test
// classifyObservation — does NOT trigger a real pulse).
if (import.meta.url === pathToFileURL(process.argv[1] || "").href) {
  main().catch((e) => { console.error(`pulse error: ${e.stack || e.message}`); process.exit(1); });
}
