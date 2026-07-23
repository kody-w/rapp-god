import { haversineMeters } from '../lib/geo.js';
import { createRng, weightedPick } from '../lib/rng.js';

export const BAG_CAP = 120;
export const SPIN_RADIUS_M = 70;
export const SPIN_COOLDOWN_MS = 5 * 60 * 1000;
export const LURE_DURATION_MS = 20 * 60 * 1000;

export const ITEMS = {
  'orb.glass': { id: 'orb.glass', name: 'glass orb', glyph: '◇', catchMultiplier: 1, description: 'A clear vessel for common skies.' },
  'orb.dew': { id: 'orb.dew', name: 'dew orb', glyph: '◌', catchMultiplier: 1.35, description: 'Cool glass with a steadier hold.' },
  'orb.prism': { id: 'orb.prism', name: 'prism orb', glyph: '◈', catchMultiplier: 1.8, description: 'A rare vessel that bends weather-light.' },
  'treat.mint': { id: 'treat.mint', name: 'mint offering', glyph: '❧', catchMultiplier: 1.3, fleeMultiplier: 0.65, description: 'Calms a creature for one throw.' },
  lure: { id: 'lure', name: 'weather lure', glyph: '✦', description: 'Quickens a place for twenty minutes.' }
};

export const DEFAULT_INVENTORY = Object.freeze({
  'orb.glass': 12,
  'orb.dew': 3,
  'orb.prism': 1,
  'treat.mint': 2,
  lure: 1
});

const DROP_TABLES = {
  water: [['orb.dew', 6], ['orb.glass', 4], ['treat.mint', 2], ['lure', 0.5]],
  nature: [['orb.glass', 5], ['treat.mint', 4], ['orb.dew', 2], ['lure', 0.7]],
  landmark: [['orb.glass', 4], ['orb.dew', 3], ['orb.prism', 1.4], ['lure', 0.5]],
  civic: [['orb.glass', 6], ['orb.dew', 2], ['treat.mint', 1], ['orb.prism', 0.5]],
  rest: [['orb.glass', 7], ['treat.mint', 2], ['orb.dew', 1]]
};

export function normalizeInventory(value = {}) {
  const inventory = {};
  for (const id of Object.keys(ITEMS)) {
    const count = Math.max(0, Math.floor(Number(value[id]) || 0));
    if (count) inventory[id] = count;
  }
  return inventory;
}

export function inventoryCount(inventory) {
  return Object.values(normalizeInventory(inventory)).reduce((sum, count) => sum + count, 0);
}

export function spendItem(inventory, id, count = 1) {
  const next = normalizeInventory(inventory);
  const wanted = Math.max(1, Math.floor(count));
  if (!ITEMS[id] || (next[id] || 0) < wanted) return { ok: false, inventory: next };
  next[id] -= wanted;
  if (next[id] === 0) delete next[id];
  return { ok: true, inventory: next };
}

export function grantItems(inventory, drops) {
  const next = normalizeInventory(inventory);
  let room = Math.max(0, BAG_CAP - inventoryCount(next));
  const granted = [];
  for (const drop of drops) {
    const requested = Math.max(0, Math.floor(drop.count));
    const count = Math.min(room, requested);
    if (count > 0 && ITEMS[drop.id]) {
      next[drop.id] = (next[drop.id] || 0) + count;
      granted.push({ id: drop.id, count, item: ITEMS[drop.id] });
      room -= count;
    }
  }
  return { inventory: next, granted, full: room === 0 };
}

export function placeStatus(place, location, spinState = {}, now = Date.now()) {
  const distanceM = haversineMeters(place, location);
  const record = spinState[place.id] || { count: 0, lastAt: 0 };
  const readyInMs = record.lastAt
    ? Math.max(0, Number(record.lastAt) + SPIN_COOLDOWN_MS - now)
    : 0;
  return {
    distanceM,
    inRange: distanceM <= SPIN_RADIUS_M + Math.min(25, Math.max(0, Number(location.accuracy) || 0)),
    ready: readyInMs === 0,
    readyInMs,
    spinCount: Number(record.count) || 0
  };
}

export function spinPlace({ place, location, inventory, spinState = {}, now = Date.now() }) {
  const status = placeStatus(place, location, spinState, now);
  if (!status.inRange) return { ok: false, reason: 'out-of-range', status, inventory: normalizeInventory(inventory), spinState };
  if (!status.ready) return { ok: false, reason: 'cooldown', status, inventory: normalizeInventory(inventory), spinState };

  const rng = createRng(`${place.id}:${status.spinCount + 1}`);
  const table = DROP_TABLES[place.kind] || DROP_TABLES.rest;
  const draws = 2 + Math.floor(rng() * 2);
  const merged = new Map();
  for (let index = 0; index < draws; index += 1) {
    const id = weightedPick(table, rng);
    const amount = id.startsWith('orb.') && rng() > 0.56 ? 2 : 1;
    merged.set(id, (merged.get(id) || 0) + amount);
  }
  const drops = [...merged].map(([id, count]) => ({ id, count }));
  const granted = grantItems(inventory, drops);
  const nextSpinState = {
    ...spinState,
    [place.id]: { count: status.spinCount + 1, lastAt: now }
  };
  return { ok: true, drops: granted.granted, inventory: granted.inventory, full: granted.full, spinState: nextSpinState };
}

export function activateLure({ place, inventory, lureState = {}, now = Date.now() }) {
  const spent = spendItem(inventory, 'lure', 1);
  if (!place || !spent.ok) return { ok: false, inventory: spent.inventory, lureState };
  return {
    ok: true,
    inventory: spent.inventory,
    lureState: { ...lureState, [place.id]: now + LURE_DURATION_MS }
  };
}

export function isLured(placeId, lureState = {}, now = Date.now()) {
  return Number(lureState[placeId] || 0) > now;
}
