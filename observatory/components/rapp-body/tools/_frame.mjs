// tools/_frame.mjs — body-frame primitives (zero npm deps, Node crypto only).
//
// A body frame is the atomic slice the RAPP organism broadcasts. It conforms to
// rapp-frame/2.0 EXACTLY as kody-w/twin/frames/*.json publishes it:
//
//   { spec, kind, seq, ts, twin_id, kernel_version, payload, sha256, parent_sha, sig }
//
// The frame is CONTENT-ADDRESSED: sha256 over the canonical form of its PAYLOAD.
// A twin engineer will recognize `canonicalize()` below — it is byte-for-byte the
// deterministic sorted-key JSON from twin/tools/_frame.mjs. Reproducing twin's real
// frames 0.json / 1.json proved the rule:  sha256 === sha256(canonicalize(payload)).
// parent_sha chains those payload-hashes into the worldline (rapp-eternity/1.0 at
// body scale: the chain IS the identity, a frame is just where you cut it).
//
// Signatures are OPTIONAL (sig:null) — chain integrity comes from the sha256 links,
// same as twin's genesis frame. Keypair signing can be layered later without a fork.

import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const SPEC = "rapp-frame/2.0";
export const KIND_WITNESSED = "body.pulse";
export const KIND_RECONSTRUCTED = "body.pulse.reconstructed";
export const KERNEL_VERSION = "0.6.0"; // grail kernel of record (rapp-agent/1.0, v0.6.0)

// REPO_ROOT is this repo's root (tools/ lives directly under it). RAPP_BODY_ROOT
// overrides it so a ceremony can run against a throwaway body in a temp dir without
// touching the live frames.
export const REPO_ROOT = process.env.RAPP_BODY_ROOT
  ? path.resolve(process.env.RAPP_BODY_ROOT)
  : path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
export const FRAMES_DIR = path.join(REPO_ROOT, "frames");
export const RAPPID_PATH = path.join(REPO_ROOT, "rappid.json");

// Deterministic JSON: recursively sort object keys, compact. This is `canonical(frame)`
// from rapp-frame/2.0 — the same bytes on every machine, so the sha is stable. It is
// the exact function twin/tools/_frame.mjs uses; keep it identical for interop.
export function canonicalize(v) {
  if (v === null || typeof v !== "object") return JSON.stringify(v);
  if (Array.isArray(v)) return "[" + v.map(canonicalize).join(",") + "]";
  const keys = Object.keys(v).sort();
  return "{" + keys.map((k) => JSON.stringify(k) + ":" + canonicalize(v[k])).join(",") + "}";
}

export function sha256Hex(buf) {
  return crypto.createHash("sha256").update(buf).digest("hex");
}

// The content-address of a frame = sha256 over the canonical form of its payload.
// (Verified against kody-w/twin/frames/0.json and 1.json.)
export function digestPayload(payload) {
  return crypto.createHash("sha256").update(canonicalize(payload), "utf8").digest("hex");
}

export function sha8(sha) {
  return String(sha).slice(0, 8);
}

// Eternity identity (CONSTITUTION Art. XXXIV.1, locked 2026-06-03): the 64-hex tail is
// sha256 of '<owner>/<slug>'. `rappid:@<owner>/<slug>:<64hex>`.
export function eternityHex(owner, slug) {
  return crypto.createHash("sha256").update(`${owner}/${slug}`).digest("hex");
}
export function eternityRappid(owner, slug) {
  return `rappid:@${owner}/${slug}:${eternityHex(owner, slug)}`;
}

// The body's own rappid (twin_id field). Prefer rappid.json; fall back to the derivation.
export function readBodyId() {
  try {
    const r = JSON.parse(fs.readFileSync(RAPPID_PATH, "utf8"));
    if (r && typeof r.rappid === "string") return r.rappid;
  } catch {}
  return eternityRappid("kody-w", "rapp-body");
}

// Assemble a full rapp-frame/2.0 frame object with the payload content-address filled in.
// Field insertion order mirrors twin's published frames exactly, so the file reads the same.
export function buildFrame({ kind, seq, ts, payload, parent_sha, twin_id, kernel_version }) {
  const sha256 = digestPayload(payload);
  return {
    spec: SPEC,
    kind,
    seq,
    ts,
    twin_id: twin_id ?? readBodyId(),
    kernel_version: kernel_version ?? KERNEL_VERSION,
    payload,
    sha256,
    parent_sha: parent_sha ?? null,
    sig: null,
  };
}

export function frameFileName(seq) {
  return `${seq}.json`;
}

// List published frame files (<seq>.json), sorted by numeric seq ascending.
export function listFrameFiles(dir = FRAMES_DIR) {
  if (!fs.existsSync(dir)) return [];
  return fs
    .readdirSync(dir)
    .filter((f) => /^\d+\.json$/.test(f))
    .sort((a, b) => parseInt(a, 10) - parseInt(b, 10));
}

export function readFrameFile(fp) {
  return JSON.parse(fs.readFileSync(fp, "utf8"));
}

// Read the whole chain (in seq order) as parsed frame objects.
export function readChain(dir = FRAMES_DIR) {
  return listFrameFiles(dir).map((f) => readFrameFile(path.join(dir, f)));
}

export function writeFrame(frame, dir = FRAMES_DIR) {
  fs.mkdirSync(dir, { recursive: true });
  const fp = path.join(dir, frameFileName(frame.seq));
  fs.writeFileSync(fp, JSON.stringify(frame, null, 2) + "\n");
  return fp;
}

// frames/index.json — the manifest: ONE fetch loads the whole timeline map.
export function writeIndex(frames, dir = FRAMES_DIR) {
  const head = frames[frames.length - 1] || null;
  const index = {
    spec: "rapp-frame-index/1.0",
    twin_id: readBodyId(),
    generated: new Date().toISOString(),
    count: frames.length,
    head: head ? { seq: head.seq, sha256: head.sha256, ts: head.ts, kind: head.kind } : null,
    frames: frames.map((f) => ({
      seq: f.seq,
      path: `frames/${frameFileName(f.seq)}`,
      ts: f.ts,
      kind: f.kind,
      sha256: f.sha256,
      parent_sha: f.parent_sha,
    })),
  };
  fs.writeFileSync(path.join(dir, "index.json"), JSON.stringify(index, null, 2) + "\n");
  return index;
}

// vitals.json — the static-API surface: latest-frame pointer + current health rollup.
export function writeVitals(frame, health, root = REPO_ROOT) {
  const vitals = {
    spec: "rapp-body-vitals/1.0",
    twin_id: readBodyId(),
    updated: new Date().toISOString(),
    head: frame
      ? { seq: frame.seq, sha256: frame.sha256, ts: frame.ts, kind: frame.kind }
      : null,
    health: health || {},
  };
  fs.writeFileSync(path.join(root, "vitals.json"), JSON.stringify(vitals, null, 2) + "\n");
  return vitals;
}

// The "material" fingerprint used by the no-churn rule: skeleton + census(structure) +
// vitals, with all volatile timestamps and derived fields stripped, so an identical
// body produces an identical fingerprint regardless of when it was observed.
//
// DOCTRINE (observation gaps are transport, not biography): the fingerprint MUST ignore
// every transient observation artifact — `reachable`, `stale`, `status`, `head_stale` —
// and the events array entirely. A repo that is merely unreadable this run carries its
// last-known `head_sha` forward, so its material is byte-identical to the previous frame
// and produces NO churn. Only a real biographical change (a moved head_sha, a bumped spec
// version, a confirmed vanish that drops a repo from the census) moves the fingerprint.
export function materialFingerprint(payload) {
  const p = payload || {};
  const sk = p.skeleton || {};
  const material = {
    skeleton: {
      spec_version: sk.spec_version ?? null,
      mirrors_identical: sk.mirrors_identical ?? null,
      homes: sk.homes
        ? Object.fromEntries(Object.entries(sk.homes).map(([k, v]) => [k, v && v.sha256 || null]))
        : null,
      spine: sk.spine || null,
    },
    // per-repo material = identity + layer + head_sha ONLY. NO reachable/stale/status:
    // those are observation state, not biography. head_sha is the effective (carried-
    // forward when stale) value, so a rate-limited run fingerprints identically.
    census: (p.census?.repos || [])
      .map((r) => ({
        name: r.name,
        layer: r.layer ?? null,
        category: r.category ?? null,
        head_sha: r.head_sha ?? null,
      }))
      .sort((a, b) => (a.name < b.name ? -1 : a.name > b.name ? 1 : 0)),
    vitals: {
      sync: p.vitals?.sync ?? null,
      drift_issues: p.vitals?.drift_issues
        ? { open: p.vitals.drift_issues.open ?? null, high: p.vitals.drift_issues.high ?? null }
        : null,
      mirrors_identical: p.vitals?.mirrors_identical ?? null,
    },
  };
  return sha256Hex(canonicalize(material));
}
