#!/usr/bin/env node
// tools/verify-chain.mjs — walk the whole biography and prove it is intact.
//
// A twin engineer reading this will recognize the shape of twin/tools/verify-chain.mjs:
// it replays every frame in seq order and checks integrity + chain linkage. The body's
// frames are content-addressed on their PAYLOAD (sha256 === sha256(canonicalize(payload)),
// the exact rule proven against kody-w/twin/frames/*.json), and linked by parent_sha into
// a single worldline. This validator checks, for the full chain:
//
//   • envelope    — spec rapp-frame/2.0, a known kind, one stable twin_id, required fields
//   • seq         — contiguous 0..N-1, no gaps or duplicates
//   • integrity   — recomputed sha256(payload) matches frame.sha256 (tamper-evident)
//   • linkage     — parent_sha[0]==null; parent_sha[n]==sha256[n-1]
//   • time        — ts monotonic non-decreasing
//   • provenance  — reconstructed frames form the prefix and each carries evidence;
//                   no witnessed frame is preceded by nothing-but sits before a reconstructed one;
//                   witnessed frames declare mode "witnessed"
//   • no gap-fact — a repo may NEVER appear in a born/vanish change while the same frame
//                   carries an observation-gap for it (gaps are transport, not biography)
//   • index.json  — the manifest matches the frames on disk (one fetch == the whole map)
//
// Exit 0 iff every check passes; exit 1 with precise reasons otherwise. pulse.yml runs
// this BEFORE and AFTER minting.
//
//   node tools/verify-chain.mjs

import fs from "node:fs";
import path from "node:path";
import {
  digestPayload, listFrameFiles, readFrameFile, frameFileName,
  FRAMES_DIR, SPEC, KIND_WITNESSED, KIND_RECONSTRUCTED, readBodyId, sha8,
} from "./_frame.mjs";

const KNOWN_KINDS = new Set([KIND_WITNESSED, KIND_RECONSTRUCTED]);
const bodyId = readBodyId();

const files = listFrameFiles();
const problems = [];
const history = [];

if (files.length === 0) {
  console.error("FAIL: no frames found in frames/.");
  process.exit(1);
}

let prev = null;
let firstWitnessedSeq = null;

files.forEach((file, i) => {
  const errs = [];
  let frame;
  try {
    frame = readFrameFile(path.join(FRAMES_DIR, file));
  } catch (e) {
    problems.push({ file, msg: `unreadable/invalid JSON: ${e.message}` });
    history.push({ seq: i, file, kind: "?", ok: false, errs: [`invalid JSON: ${e.message}`], sha8: "--------" });
    return;
  }

  // envelope
  if (frame.spec !== SPEC) errs.push(`envelope: spec is ${JSON.stringify(frame.spec)}, expected ${SPEC}`);
  if (!KNOWN_KINDS.has(frame.kind)) errs.push(`envelope: unknown kind ${JSON.stringify(frame.kind)}`);
  if (frame.twin_id !== bodyId) errs.push(`envelope: twin_id ${frame.twin_id} != body id ${bodyId}`);
  for (const k of ["seq", "ts", "payload", "sha256", "kernel_version"]) {
    if (frame[k] === undefined) errs.push(`envelope: missing field ${k}`);
  }
  if (!("parent_sha" in frame)) errs.push("envelope: missing field parent_sha");

  // filename matches seq
  if (file !== frameFileName(frame.seq)) errs.push(`layout: file ${file} does not match seq ${frame.seq} (${frameFileName(frame.seq)})`);

  // seq contiguity
  if (frame.seq !== i) errs.push(`seq: expected ${i}, got ${frame.seq}`);

  // integrity — recompute the payload content-address
  const recomputed = digestPayload(frame.payload);
  if (recomputed !== frame.sha256) errs.push(`integrity: recomputed sha256 ${sha8(recomputed)} != frame.sha256 ${sha8(frame.sha256)} (tampered payload)`);

  // linkage
  const expectedParent = prev ? prev.sha256 : null;
  if ((frame.parent_sha ?? null) !== expectedParent) {
    errs.push(`linkage: parent_sha ${frame.parent_sha ? sha8(frame.parent_sha) : "null"} != expected ${expectedParent ? sha8(expectedParent) : "null"}`);
  }

  // time monotonicity
  if (prev && frame.ts < prev.ts) errs.push(`time: ts ${frame.ts} < previous ${prev.ts} (non-monotonic)`);

  // provenance
  const mode = frame.payload?.provenance?.mode;
  if (frame.kind === KIND_RECONSTRUCTED) {
    if (mode !== "reconstructed") errs.push(`provenance: reconstructed frame declares mode ${JSON.stringify(mode)}`);
    const ev = frame.payload?.provenance?.evidence;
    if (!Array.isArray(ev) || ev.length === 0) errs.push("provenance: reconstructed frame carries no evidence[]");
  } else if (frame.kind === KIND_WITNESSED) {
    if (mode !== "witnessed") errs.push(`provenance: witnessed frame declares mode ${JSON.stringify(mode)}`);
    if (firstWitnessedSeq === null) firstWitnessedSeq = frame.seq;
  }

  // DEFENSE IN DEPTH (observation gaps are not biography): a repo must NEVER appear in a
  // born/vanish event — or in census.born/census.vanished — while that SAME frame carries
  // an observation-gap for it. Born/vanish require positive evidence; a gap is blindness.
  // This is what would have caught the 429/403 false-vanish frames at verify time.
  const events = Array.isArray(frame.payload?.events) ? frame.payload.events : [];
  const gappedRepos = new Set();
  for (const e of events) {
    if (e && e.type === "observation-gap" && typeof e.source === "string") {
      const m = e.source.match(/^repo:[^/]+\/(.+)$/);
      if (m) gappedRepos.add(m[1]);
    }
  }
  const changedRepos = new Set();
  for (const e of events) {
    if (e && (e.type === "birth" || e.type === "vanish") && Array.isArray(e.repos)) {
      for (const n of e.repos) changedRepos.add(n);
    }
  }
  for (const n of (frame.payload?.census?.born || [])) changedRepos.add(n);
  for (const n of (frame.payload?.census?.vanished || [])) changedRepos.add(n);
  for (const n of changedRepos) {
    if (gappedRepos.has(n)) {
      errs.push(`gap-derived biography: repo "${n}" appears in a born/vanish change AND has a same-frame observation-gap — a gap is transport, not evidence of birth/death`);
    }
  }

  history.push({ seq: frame.seq, file, kind: frame.kind, ok: errs.length === 0, errs, sha8: sha8(frame.sha256) });
  for (const m of errs) problems.push({ file, msg: m });
  prev = frame;
});

// Global provenance rule: the reconstructed segment must be a contiguous PREFIX — no
// reconstructed frame may appear after the witnessed biography has begun.
if (firstWitnessedSeq !== null) {
  for (const h of history) {
    if (h.kind === KIND_RECONSTRUCTED && h.seq > firstWitnessedSeq) {
      const msg = `provenance: reconstructed frame at seq ${h.seq} appears AFTER genesis (first witnessed seq ${firstWitnessedSeq}) — reconstructed frames must form the prefix`;
      problems.push({ file: h.file, msg });
      h.ok = false;
      h.errs.push(msg);
    }
  }
}

// index.json consistency
const indexPath = path.join(FRAMES_DIR, "index.json");
if (!fs.existsSync(indexPath)) {
  problems.push({ file: "frames/index.json", msg: "missing manifest" });
} else {
  try {
    const idx = JSON.parse(fs.readFileSync(indexPath, "utf8"));
    if (idx.count !== files.length) problems.push({ file: "index.json", msg: `count ${idx.count} != ${files.length} frames on disk` });
    const bySeq = new Map(history.map((h) => [h.seq, h]));
    for (const e of idx.frames || []) {
      const h = bySeq.get(e.seq);
      if (!h) { problems.push({ file: "index.json", msg: `lists seq ${e.seq} which is not on disk` }); continue; }
      const frame = readFrameFile(path.join(FRAMES_DIR, frameFileName(e.seq)));
      if (e.sha256 !== frame.sha256) problems.push({ file: "index.json", msg: `seq ${e.seq}: manifest sha256 ${sha8(e.sha256)} != frame ${sha8(frame.sha256)}` });
      if (e.kind !== frame.kind) problems.push({ file: "index.json", msg: `seq ${e.seq}: manifest kind ${e.kind} != frame ${frame.kind}` });
      if (e.path !== `frames/${frameFileName(e.seq)}`) problems.push({ file: "index.json", msg: `seq ${e.seq}: manifest path ${e.path} wrong` });
    }
    const head = history[history.length - 1];
    if (idx.head && head && idx.head.sha256 !== head.sha8 && idx.head.sha256.slice(0, 8) !== head.sha8) {
      // head.sha8 is truncated; compare full via frame
      const headFrame = readFrameFile(path.join(FRAMES_DIR, frameFileName(head.seq)));
      if (idx.head.sha256 !== headFrame.sha256) problems.push({ file: "index.json", msg: `head sha256 ${sha8(idx.head.sha256)} != chain head ${sha8(headFrame.sha256)}` });
    }
  } catch (e) {
    problems.push({ file: "index.json", msg: `unreadable: ${e.message}` });
  }
}

// ---- report ---------------------------------------------------------------------------

const reconstructed = history.filter((h) => h.kind === KIND_RECONSTRUCTED).length;
const witnessed = history.filter((h) => h.kind === KIND_WITNESSED).length;

console.log(`body biography — ${files.length} frame(s)  [${reconstructed} reconstructed, ${witnessed} witnessed]`);
console.log(`twin_id: ${bodyId}`);
console.log("");
for (const h of history) {
  const mark = h.ok ? "ok " : "XX ";
  console.log(`  ${mark}[${String(h.seq).padStart(2)}] ${String(h.kind).padEnd(24)} body@${h.sha8}`);
  if (!h.ok) for (const e of h.errs) console.log(`        ! ${e}`);
}
console.log("");

if (problems.length === 0) {
  const head = history[history.length - 1];
  console.log(`VERDICT: OK — all ${files.length} frame(s) verify; biography intact. head: seq ${head.seq} body@${head.sha8}`);
  process.exit(0);
} else {
  console.error(`VERDICT: FAIL — ${problems.length} problem(s):`);
  for (const p of problems) console.error(`  ${p.file}: ${p.msg}`);
  process.exit(1);
}
