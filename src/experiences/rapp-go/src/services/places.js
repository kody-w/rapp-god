import { haversineMeters, offsetLocation, privacyCell } from '../lib/geo.js';

const OVERPASS_ENDPOINTS = [
  'https://overpass-api.de/api/interpreter',
  'https://overpass.kumi.systems/api/interpreter'
];
const PLACE_CACHE_MS = 12 * 60 * 60 * 1000;

export function classifyPlace(tags = {}) {
  if (['drinking_water', 'fountain'].includes(tags.amenity) || ['spring', 'water'].includes(tags.natural)) return 'water';
  if (tags.leisure === 'park' || ['tree', 'wood', 'garden'].includes(tags.natural)) return 'nature';
  if (tags.historic || tags.memorial || ['artwork', 'viewpoint', 'attraction'].includes(tags.tourism)) return 'landmark';
  if (['library', 'community_centre', 'townhall'].includes(tags.amenity) || tags.tourism === 'information') return 'civic';
  return 'rest';
}

function fallbackName(kind, index) {
  const names = {
    water: ['a neighborhood fountain', 'a quiet spring'],
    nature: ['a pocket of green', 'an old tree'],
    landmark: ['a local landmark', 'a small monument'],
    civic: ['a gathering place', 'a public corner'],
    rest: ['a place to pause', 'a street-side seat']
  };
  const choices = names[kind] || names.rest;
  return choices[index % choices.length];
}

export function demoPlaces(location) {
  const fixtures = [
    { id: 'demo-fountain', name: 'Cedar Street Fountain', kind: 'water', east: 18, north: 8 },
    { id: 'demo-garden', name: 'Pocket Rain Garden', kind: 'nature', east: -42, north: 25 },
    { id: 'demo-mural', name: 'Moonrise Mural', kind: 'landmark', east: 56, north: -18 },
    { id: 'demo-library', name: 'Little Free Library', kind: 'civic', east: -85, north: -52 },
    { id: 'demo-bench', name: 'Riverside Bench', kind: 'rest', east: 112, north: 46 }
  ];
  return fixtures.map((fixture) => ({
    ...offsetLocation(location, fixture.east, fixture.north),
    id: fixture.id,
    name: fixture.name,
    kind: fixture.kind,
    tags: {},
    distanceM: Math.hypot(fixture.east, fixture.north),
    source: 'demo'
  }));
}

function queryFor(cell) {
  const { south, west, north, east } = cell.bounds;
  const box = [south, west, north, east].map((value) => value.toFixed(6)).join(',');
  return `[out:json][timeout:12];(
    nwr["amenity"~"fountain|drinking_water|bench|library|community_centre|townhall"](${box});
    nwr["leisure"="park"](${box});
    nwr["natural"~"tree|spring|wood"](${box});
    nwr["tourism"~"artwork|viewpoint|attraction|information"](${box});
    nwr["historic"](${box});
    nwr["memorial"](${box});
  );out center tags;`;
}

function normalizeElements(elements, location) {
  const seen = new Set();
  const places = [];
  for (const [index, element] of (elements || []).entries()) {
    const id = `${element.type}/${element.id}`;
    if (seen.has(id)) continue;
    seen.add(id);
    const lat = Number(element.lat ?? element.center?.lat);
    const lng = Number(element.lon ?? element.center?.lon);
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) continue;
    const kind = classifyPlace(element.tags);
    const distanceM = haversineMeters(location, { lat, lng });
    if (distanceM > 1_200) continue;
    places.push({
      id,
      lat,
      lng,
      name: element.tags?.name || fallbackName(kind, index),
      kind,
      tags: element.tags || {},
      distanceM,
      source: 'openstreetmap'
    });
  }
  return places.sort((a, b) => a.distanceM - b.distanceM).slice(0, 36);
}

function fallbackPlaces(location) {
  return demoPlaces(location).map((place, index) => ({
    ...place,
    id: `fallback-${index}`,
    name: ['a nearby fountain', 'a patch of green', 'a familiar corner', 'a public shelf', 'a place to rest'][index],
    source: 'fallback'
  }));
}

async function overpassFetch(endpoint, query, fetchImpl, timeoutMs) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const body = new URLSearchParams({ data: query });
    const response = await fetchImpl(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8' },
      body,
      signal: controller.signal
    });
    if (!response.ok) throw new Error(`Overpass returned ${response.status}`);
    return await response.json();
  } finally {
    clearTimeout(timer);
  }
}

export async function getPlaces(location, {
  demo = false,
  now = Date.now(),
  fetchImpl = globalThis.fetch,
  store = null,
  timeoutMs = 10_000
} = {}) {
  if (demo) return demoPlaces(location);
  const cell = privacyCell(location, 6);
  const cacheKey = `places.${cell.hash}`;
  const cached = store?.get(cacheKey);
  if (cached?.savedAt && now - cached.savedAt < PLACE_CACHE_MS && Array.isArray(cached.places)) {
    return cached.places.map((place) => ({ ...place, distanceM: haversineMeters(location, place), source: 'cache' }));
  }
  if (typeof fetchImpl !== 'function') return fallbackPlaces(location);

  const query = queryFor(cell);
  for (const endpoint of OVERPASS_ENDPOINTS) {
    try {
      const payload = await overpassFetch(endpoint, query, fetchImpl, timeoutMs);
      const places = normalizeElements(payload.elements, location);
      if (places.length) {
        store?.set(cacheKey, { savedAt: now, places });
        return places;
      }
    } catch {}
  }
  return fallbackPlaces(location);
}

export { OVERPASS_ENDPOINTS };
