// tools/_census.mjs — the body's cell census, composed from the canonical sources.
//
// Source of truth (per ORDER + ecosystem-spec.mirrors): the census covers every repo the
// ecosystem-spec catalogs (spec.repos, 10 cluster groups) UNION every repo the rapp-spine
// registry lists, deduped. Layer/cluster metadata comes from the spine registry (7 layers)
// plus the spec categories. Nothing here is invented — it is parsed from the grail data.

// The three published homes of the ecosystem-spec (equality across them is itself a vital
// sign — the agent's `verify` action sha256-compares them; divergence IS drift).
export const SPEC_HOMES = {
  rapp: { owner: "kody-w", repo: "RAPP", ref: "main", path: "specs/ecosystem-spec.json", label: "kody-w/RAPP (canonical source)" },
  rapp_god: { owner: "kody-w", repo: "rapp-god", ref: "main", path: "api/v1/ecosystem-spec.json", label: "kody-w/rapp-god" },
  rapp_map: { owner: "kody-w", repo: "rapp-map", ref: "main", path: "ecosystem-spec.json", label: "kody-w/rapp-map (mirror of record for reads)" },
};

export const SPINE = {
  owner: "kody-w",
  repo: "rapp-spine",
  ref: "main",
  registry: "registry.json",
  foundation: "foundation.json",
};

export const DEFAULT_LAYER_ORDER = [
  "kernel", "map", "runtime", "distribution", "identity", "network", "leviathan", "uncataloged",
];

const norm = (n) => String(n).toLowerCase();

// spec.repos entries look like "rapp-god (registry of every part …)" — the repo name is
// the leading token before the first parenthetical.
export function parseRepoName(s) {
  return String(s).split(/\s*\(/)[0].trim();
}

// The order the spine publishes its layers, with `uncataloged` appended for repos the
// registry does not place. Falls back to the default if the spine is unreadable.
export function layerOrderFrom(spineReg) {
  const order = Array.isArray(spineReg?.layers_order) ? [...spineReg.layers_order] : [];
  if (!order.length) return [...DEFAULT_LAYER_ORDER];
  if (!order.includes("uncataloged")) order.push("uncataloged");
  return order;
}

// Build the deduped union census. Returns rows sorted by name (case-insensitive) so the
// output is deterministic across runs (stable frame payloads → stable content-address).
export function unionCensus(specObj, spineReg) {
  const union = new Map(); // norm(name) -> row

  // spec.repos: name -> category (owner assumed kody-w, as the spec catalogs).
  const specRepos = (specObj && specObj.repos) || {};
  for (const [category, arr] of Object.entries(specRepos)) {
    if (!Array.isArray(arr)) continue;
    for (const entry of arr) {
      const name = parseRepoName(entry);
      if (!name) continue;
      union.set(norm(name), {
        owner: "kody-w", name, category, layer: null, in_spec: true, in_spine: false,
      });
    }
  }

  // spine registry: repo "owner/name" -> layer (first layer seen per repo wins).
  const registry = Array.isArray(spineReg?.registry) ? spineReg.registry : [];
  for (const e of registry) {
    if (!e || !e.repo) continue;
    const [owner, name] = String(e.repo).split("/");
    if (!name) continue;
    const key = norm(name);
    if (union.has(key)) {
      const row = union.get(key);
      row.in_spine = true;
      if (!row.layer) row.layer = e.layer || null;
      if (!row.owner) row.owner = owner;
    } else {
      union.set(key, { owner: owner || "kody-w", name, category: null, layer: e.layer || null, in_spec: false, in_spine: true });
    }
  }

  const rows = [...union.values()];
  for (const r of rows) if (!r.layer) r.layer = "uncataloged";
  rows.sort((a, b) => (norm(a.name) < norm(b.name) ? -1 : norm(a.name) > norm(b.name) ? 1 : 0));
  return rows;
}
