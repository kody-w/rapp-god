#!/usr/bin/env node
// tools/reconstruct.mjs — the PRENATAL frames (git archaeology, run ONCE at birth).
//
// The cradle is reachable: git already remembers when every organ was born. This tool
// mines real history — each cataloged repo's created_at (GitHub API) plus the canon
// milestones the grail data itself evidences (Eternity ratification, the spine/foundation
// content-lock, the twin going DOG-online) — and emits `body.pulse.reconstructed` frames
// in CHRONOLOGICAL order, seq 0..N-1, chained by parent_sha. Each frame carries its
// evidence (the API fields / commit shas / URLs it was derived from) and NEVER claims
// witness; its census is explicitly partial (census_basis).
//
// The witnessed genesis (pulse.mjs) links onto the end of this chain at seq N.
//
//   node tools/reconstruct.mjs            # write frames/0.json … frames/(N-1).json + index.json
//   node tools/reconstruct.mjs --dry-run  # print the plan, write nothing
//
// Anonymous-safe; uses GITHUB_TOKEN when present; honors RAPP_CACHE_DIR (see _gh.mjs).

import fs from "node:fs";
import path from "node:path";
import { repoMeta, rawFile, usingCache } from "./_gh.mjs";
import { SPEC_HOMES, SPINE, unionCensus } from "./_census.mjs";
import {
  buildFrame, writeFrame, writeIndex, listFrameFiles, readFrameFile, frameFileName,
  FRAMES_DIR, KIND_RECONSTRUCTED, KIND_WITNESSED, readBodyId,
} from "./_frame.mjs";

const DRY = process.argv.includes("--dry-run");
const RAW = "https://raw.githubusercontent.com";
const dayTs = (d) => `${String(d).slice(0, 10)}T00:00:00Z`;
const daysBetween = (a, b) => Math.abs((new Date(a) - new Date(b)) / 86400000);

// ---- load the census + its birth dates ------------------------------------------------

async function loadSpecAndSpine() {
  let spec = null, specHome = null, spine = null;
  for (const [key, h] of Object.entries(SPEC_HOMES)) {
    const r = await rawFile(h.owner, h.repo, h.ref, h.path);
    if (r.ok) { try { spec = JSON.parse(r.text); specHome = key; break; } catch {} }
  }
  const sr = await rawFile(SPINE.owner, SPINE.repo, SPINE.ref, SPINE.registry);
  if (sr.ok) { try { spine = JSON.parse(sr.text); } catch {} }
  return { spec, specHome, spine };
}

async function gatherBirths(rows) {
  const born = [];
  const unreachable = [];
  for (const r of rows) {
    const m = await repoMeta(r.owner, r.name);
    if (m.ok && m.data.created_at) {
      born.push({ ...r, created_at: m.data.created_at, archived: !!m.data.archived });
    } else {
      unreachable.push({ ...r, reason: m.error || `HTTP ${m.status}` });
    }
  }
  born.sort((a, b) => (a.created_at < b.created_at ? -1 : a.created_at > b.created_at ? 1 : (a.name < b.name ? -1 : 1)));
  return { born, unreachable };
}

// Group births into waves: a new wave starts when the gap since the previous birth
// exceeds GAP days, the month changes, or the current wave reached MAX. Deterministic.
function waves(born, { GAP = 2, MAX = 10 } = {}) {
  const out = [];
  let cur = null;
  for (const b of born) {
    const month = b.created_at.slice(0, 7);
    const gap = cur ? daysBetween(b.created_at, cur.last) : Infinity;
    if (!cur || gap > GAP || month !== cur.month || cur.repos.length >= MAX) {
      cur = { first: b.created_at.slice(0, 10), date: b.created_at.slice(0, 10), last: b.created_at, month, repos: [] };
      out.push(cur);
    }
    cur.repos.push(b);
    cur.last = b.created_at;
    cur.date = b.created_at.slice(0, 10); // wave dated at its LAST birth so census is inclusive
  }
  return out;
}

// ---- canon milestones the grail data evidences ---------------------------------------

function canonMilestones(spec, spine) {
  const specMapUrl = `${RAW}/${SPEC_HOMES.rapp_map.owner}/${SPEC_HOMES.rapp_map.repo}/${SPEC_HOMES.rapp_map.ref}/${SPEC_HOMES.rapp_map.path}`;
  const spineUrl = `${RAW}/${SPINE.owner}/${SPINE.repo}/${SPINE.ref}/${SPINE.registry}`;
  const foundationUrl = `${RAW}/${SPINE.owner}/${SPINE.repo}/${SPINE.ref}/${SPINE.foundation}`;
  const list = [];

  // Eternity ratification — the identity_format string states it was locked 2026-06-03.
  const idf = spec?.identity_format || "";
  const m = idf.match(/locked (\d{4}-\d{2}-\d{2})/);
  if (m) {
    list.push({
      date: m[1],
      id: "eternity-ratified",
      text: "rapp-eternity/1.0 ratified: Eternity identity locked (CONSTITUTION Art. XXXIV.1) — a rappid is sha256('<owner>/<slug>'). The body's own identity derives from this rule.",
      evidence: [`ecosystem-spec.identity_format @ ${specMapUrl}`, `"${idf.slice(0, 90)}…"`],
      sets_spec_version: spec?.version || null,
    });
  }
  // The spine + foundation content-lock (kernel v0.6.0 declared grail) — both carry
  // a `generated` date; foundation content-addresses the frozen kernel.
  const spineGen = spine?.generated;
  if (spineGen) {
    list.push({
      date: String(spineGen).slice(0, 10),
      id: "spine-foundation-locked",
      text: "rapp-spine + rapp-foundation generated: the content-addressed registry of the RAPP foundation pillars is locked (kernel rapp-agent/1.0 v0.6.0 pinned as the grail). The skeleton the body checks against comes online.",
      evidence: [`rapp-spine registry.json.generated=${spineGen} @ ${spineUrl}`, `rapp-spine foundation.json @ ${foundationUrl}`],
    });
  }
  // The twin goes DOG-online — the first conformant rapp-frame/2.0 biography in the
  // ecosystem; the exact organ the body now grows. Evidenced by twin frame 1.
  list.push({
    date: "2026-07-06",
    id: "twin-dog-online",
    text: "kody-w/twin broadcasts the first conformant rapp-frame/2.0 pulse (\"DOG online\"): SHA-chained public bones. The body adopts this same organ at ecosystem scale.",
    evidence: [
      "twin frames/1.json sha256=52a59f1f23c039349a8c78024923d295a501e96f9337fb72cb8b36489c94894d",
      `${RAW}/kody-w/twin/main/frames/1.json`,
    ],
  });
  return list;
}

// ---- assemble the reconstructed chain -------------------------------------------------

// When does spec_version become knowable? When both grail homes (rapp-god + rapp-map)
// exist — from then the spec is "published byte-identical to rapp-god and rapp-map".
function specHomesOnlineDate(born) {
  const god = born.find((b) => b.name.toLowerCase() === "rapp-god");
  const map = born.find((b) => b.name.toLowerCase() === "rapp-map");
  if (god && map) return (god.created_at > map.created_at ? god.created_at : map.created_at).slice(0, 10);
  return null;
}

function build(rows, born, unreachable, spec, spine) {
  const specVersion = spec?.version || "1.0.0";
  const homesDate = specHomesOnlineDate(born);
  const RAPP = born.find((b) => b.name === "RAPP");
  const GOD = born.find((b) => b.name.toLowerCase() === "rapp-god");
  const MAP = born.find((b) => b.name.toLowerCase() === "rapp-map");

  // steps = {date, first, last, births:[repo...], canon:[milestone...]}
  const steps = [];
  for (const w of waves(born)) steps.push({ date: w.date, first: w.first, last: w.date, births: w.repos, canon: [] });
  for (const c of canonMilestones(spec, spine)) {
    // Attach to a wave when the canon date falls within that wave's span (so a birth
    // burst and the canon it coincides with become one frame); else it stands alone.
    const within = steps.find((s) => s.first && s.first <= c.date && c.date <= s.last);
    if (within) within.canon.push(c);
    else steps.push({ date: c.date, first: c.date, last: c.date, births: [], canon: [c] });
  }
  steps.sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0));

  const homesPresent = (date) => ({
    rapp: { present: !!(RAPP && RAPP.created_at.slice(0, 10) <= date) },
    rapp_god: { present: !!(GOD && GOD.created_at.slice(0, 10) <= date) },
    rapp_map: { present: !!(MAP && MAP.created_at.slice(0, 10) <= date) },
  });

  const frames = [];
  const cumulative = new Map(); // name -> repo row (with created_at)
  let seq = 0, parent = null;

  for (const step of steps) {
    const bornNames = [];
    for (const b of step.births) { cumulative.set(b.name, b); bornNames.push(b.name); }
    const specKnown = homesDate && step.date >= homesDate ? specVersion : null;

    const reposArr = [...cumulative.values()]
      .map((r) => ({
        name: r.name, owner: r.owner, layer: r.layer, category: r.category,
        created_at: r.created_at, born_this_frame: bornNames.includes(r.name),
      }))
      .sort((a, b) => (a.name.toLowerCase() < b.name.toLowerCase() ? -1 : 1));

    const events = [];
    if (bornNames.length) events.push({ type: "birth", repos: bornNames });
    for (const c of step.canon) events.push({ type: "canon", id: c.id, text: c.text });

    const evidence = [];
    if (bornNames.length) evidence.push(`created_at (GitHub API) for: ${bornNames.join(", ")}`);
    for (const c of step.canon) for (const e of c.evidence) evidence.push(e);

    const payload = {
      taken_ts: dayTs(step.date),
      provenance: { mode: "reconstructed", evidence },
      skeleton: {
        spec_version: specKnown,
        homes: homesPresent(step.date),
        mirrors_identical: null, // unknown historically (no witness of the three homes)
        spine: { registry_sha256: null, foundation_sha256: null },
      },
      census: {
        basis: `reconstructed: repos with created_at <= ${step.date} (partial; ${unreachable.length} cataloged repo(s) unreachable at reconstruction time and therefore undated)`,
        count: reposArr.length,
        repos: reposArr,
        born: bornNames,
        vanished: [],
      },
      vitals: { sync: null, drift_issues: null, mirrors_identical: null, last_sweep: null },
      events,
    };

    const frame = buildFrame({
      kind: KIND_RECONSTRUCTED, seq, ts: dayTs(step.date), payload, parent_sha: parent,
    });
    frames.push(frame);
    parent = frame.sha256;
    seq++;
  }
  return frames;
}

// ---- main -----------------------------------------------------------------------------

(async () => {
  console.log(`reconstruct — cache: ${JSON.stringify(usingCache())}`);
  // Refuse to clobber a witnessed biography — this is a one-time cradle operation.
  const existing = listFrameFiles();
  const witnessed = existing.filter((f) => readFrameFile(path.join(FRAMES_DIR, f)).kind === KIND_WITNESSED);
  if (witnessed.length) {
    console.error(`REFUSING: ${witnessed.length} witnessed frame(s) already present. reconstruct is the one-time prenatal op; delete frames/ to redo the cradle.`);
    process.exit(1);
  }

  const { spec, specHome, spine } = await loadSpecAndSpine();
  if (!spec) { console.error("FATAL: could not read ecosystem-spec from any home."); process.exit(1); }
  const rows = unionCensus(spec, spine);
  console.log(`census: ${rows.length} repos (spec home: ${specHome}, spine: ${spine ? "ok" : "MISSING"})`);

  const { born, unreachable } = await gatherBirths(rows);
  console.log(`datable births: ${born.length}; unreachable (undated): ${unreachable.map((u) => u.name).join(", ") || "none"}`);

  const frames = build(rows, born, unreachable, spec, spine);
  console.log(`\nplanned ${frames.length} reconstructed frames:`);
  for (const f of frames) {
    const ev = f.payload.events.map((e) => e.type === "birth" ? `+${e.repos.length}` : `canon:${e.id}`).join(" ");
    console.log(`  [${String(f.seq).padStart(2)}] ${f.ts.slice(0, 10)}  census=${String(f.payload.census.count).padStart(2)}  ${ev}`);
  }

  if (DRY) { console.log("\n--dry-run: wrote nothing."); return; }

  // Clear any prior reconstructed-only frames, then write the fresh cradle chain.
  for (const f of existing) fs.rmSync(path.join(FRAMES_DIR, f));
  for (const f of frames) writeFrame(f);
  writeIndex(frames);
  console.log(`\nwrote frames/0.json … frames/${frames.length - 1}.json + frames/index.json`);
  console.log(`chain head (reconstructed): seq ${frames.length - 1}  sha256 ${frames[frames.length - 1].sha256.slice(0, 16)}…`);
  console.log(`twin_id: ${readBodyId()}`);
})();
