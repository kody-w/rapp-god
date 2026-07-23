// tools/_gh.mjs — zero-dep GitHub access for the pulse tools (Node fetch, >=20).
//
// Anonymous-safe: works with NO token (60/hr shared), and uses GITHUB_TOKEN / GH_TOKEN
// when present (5000/hr). Every read returns a TYPED result { ok, status, ... } so a
// caller can turn an unreadable source into an explicit `observation-gap` event instead
// of silently recording thinner data (the false-green lesson: absence must be visible).
//
// Optional read-through cache: set RAPP_CACHE_DIR to a directory and 200-responses are
// cached by URL (write-through). This keeps repeated/offline runs polite to the API and
// deterministic — used for local verification. CI leaves it unset and reads live.
// RAPP_CACHE_ONLY=1 additionally forbids the network (a cache miss = unreadable), which
// proves a run touched zero live endpoints.

import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

const API = "https://api.github.com";
const RAW = "https://raw.githubusercontent.com";

const CACHE_DIR = process.env.RAPP_CACHE_DIR || null;
const CACHE_ONLY = process.env.RAPP_CACHE_ONLY === "1";
const USER_AGENT = "rapp-body-pulse (kody-w/rapp-body)";

export function token() {
  return process.env.GITHUB_TOKEN || process.env.GH_TOKEN || null;
}

function headers(extra = {}) {
  const h = { "User-Agent": USER_AGENT, ...extra };
  const t = token();
  if (t) h.Authorization = `Bearer ${t}`;
  return h;
}

// Readable, collision-resistant cache filename for a URL (sanitized URL + short hash
// tail). Pure so a pre-populator can compute identical keys.
export function cacheKey(url) {
  const safe = url.replace(/^https?:\/\//, "").replace(/[^A-Za-z0-9._-]+/g, "_").slice(0, 120);
  const tail = crypto.createHash("sha256").update(url).digest("hex").slice(0, 12);
  return `${safe}.${tail}.txt`;
}

// Cache filenames: 200 bodies live at cacheKey(url); a known 404 is recorded as a small
// sentinel at negKey(url) so a cache-only/offline run reproduces POSITIVE absence (a real
// 404) instead of degrading it to a transport gap. Only 200 and 404 are ever cached —
// transport failures (429/403/network) are never cached, because they are not evidence.
export function negKey(url) {
  return cacheKey(url) + ".miss404";
}

function cacheFileFor(url) {
  if (!CACHE_DIR) return null;
  return path.join(CACHE_DIR, cacheKey(url));
}
function negFileFor(url) {
  if (!CACHE_DIR) return null;
  return path.join(CACHE_DIR, negKey(url));
}

// Returns { kind: "ok", body } | { kind: "404" } | null.
function readCache(url) {
  const fp = cacheFileFor(url);
  if (fp && fs.existsSync(fp)) return { kind: "ok", body: fs.readFileSync(fp, "utf8") };
  const nf = negFileFor(url);
  if (nf && fs.existsSync(nf)) return { kind: "404" };
  return null;
}

function writeCache(url, body) {
  const fp = cacheFileFor(url);
  if (!fp) return;
  fs.mkdirSync(path.dirname(fp), { recursive: true });
  fs.writeFileSync(fp, body);
}
function writeNeg(url) {
  const nf = negFileFor(url);
  if (!nf) return;
  fs.mkdirSync(path.dirname(nf), { recursive: true });
  fs.writeFileSync(nf, "404\n");
}

// Core fetch → typed { ok, status, text, fromCache, error }. Never throws on HTTP/network.
export async function ghFetch(url, { accept } = {}) {
  const cached = readCache(url);
  if (cached) {
    if (cached.kind === "ok") return { ok: true, status: 200, text: cached.body, fromCache: true };
    return { ok: false, status: 404, text: null, fromCache: true, error: "HTTP 404" }; // cached positive absence
  }
  if (CACHE_ONLY) {
    return { ok: false, status: 0, text: null, fromCache: false, error: "cache-miss (RAPP_CACHE_ONLY)" };
  }
  try {
    const res = await fetch(url, { headers: headers(accept ? { Accept: accept } : {}) });
    const text = await res.text();
    if (res.ok) writeCache(url, text);
    else if (res.status === 404) writeNeg(url); // negative-cache positive absence
    return {
      ok: res.ok,
      status: res.status,
      text: res.ok ? text : null,
      fromCache: false,
      error: res.ok ? null : `HTTP ${res.status}`,
      rateLimited: res.status === 403 || res.status === 429,
    };
  } catch (e) {
    return { ok: false, status: 0, text: null, fromCache: false, error: `network: ${e.message}` };
  }
}

// JSON variants ------------------------------------------------------------------------

export async function ghJson(url) {
  const r = await ghFetch(url, { accept: "application/vnd.github+json" });
  if (!r.ok) return { ok: false, status: r.status, data: null, error: r.error, rateLimited: r.rateLimited };
  try {
    return { ok: true, status: r.status, data: JSON.parse(r.text), fromCache: r.fromCache };
  } catch (e) {
    return { ok: false, status: r.status, data: null, error: `bad JSON: ${e.message}` };
  }
}

// GET api.github.com{apiPath}  (apiPath must start with "/")
export function apiUrl(apiPath) {
  return apiPath.startsWith("http") ? apiPath : `${API}${apiPath}`;
}
export async function api(apiPath) {
  return ghJson(apiUrl(apiPath));
}

// GET raw.githubusercontent.com/{owner}/{repo}/{ref}/{filePath}  → { ok, status, text, sha256 }
export function rawUrl(owner, repo, ref, filePath) {
  return `${RAW}/${owner}/${repo}/${ref}/${filePath}`;
}
export async function rawFile(owner, repo, ref, filePath) {
  const r = await ghFetch(rawUrl(owner, repo, ref, filePath));
  if (!r.ok) return { ok: false, status: r.status, text: null, error: r.error };
  return {
    ok: true,
    status: r.status,
    text: r.text,
    sha256: crypto.createHash("sha256").update(r.text).digest("hex"),
    fromCache: r.fromCache,
  };
}

// Repo metadata: created_at, pushed_at, default_branch, open_issues_count, archived, ...
export async function repoMeta(owner, name) {
  return api(`/repos/${owner}/${name}`);
}

// Latest commit on the default branch (one call) → { sha, date }.
export async function repoHead(owner, name) {
  const r = await api(`/repos/${owner}/${name}/commits?per_page=1`);
  if (!r.ok) return { ok: false, status: r.status, error: r.error, rateLimited: r.rateLimited };
  const top = Array.isArray(r.data) ? r.data[0] : null;
  if (!top) return { ok: false, status: r.status, error: "no commits" };
  return {
    ok: true,
    sha: top.sha,
    date: top.commit?.committer?.date || top.commit?.author?.date || null,
    fromCache: r.fromCache,
  };
}

// One user-wide search for OPEN issues labelled `drift` (1 call instead of one per repo).
// Callers filter to the census and bucket by severity prefix in the title. Best-effort:
// the search API is rate-limited even when authenticated, so an error is a real gap.
export async function driftIssues(user) {
  const q = encodeURIComponent(`user:${user} is:issue is:open label:drift`);
  const r = await api(`/search/issues?q=${q}&per_page=100`);
  if (!r.ok) return { ok: false, status: r.status, error: r.error, rateLimited: r.rateLimited };
  return { ok: true, total: r.data.total_count ?? 0, items: r.data.items || [], fromCache: r.fromCache };
}

export function usingCache() {
  return { dir: CACHE_DIR, only: CACHE_ONLY, authed: !!token() };
}
