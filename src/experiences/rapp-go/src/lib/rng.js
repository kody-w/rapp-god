const UINT32_MAX_PLUS_ONE = 0x1_0000_0000;

export function hashString(value) {
  const text = String(value);
  let hash = 2166136261;
  for (let index = 0; index < text.length; index += 1) {
    hash ^= text.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  hash += hash << 13;
  hash ^= hash >>> 7;
  hash += hash << 3;
  hash ^= hash >>> 17;
  hash += hash << 5;
  return hash >>> 0;
}

export function createRng(seed) {
  let state = hashString(seed);
  return () => {
    state = (state + 0x6d2b79f5) >>> 0;
    let value = state;
    value = Math.imul(value ^ (value >>> 15), value | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
    return ((value ^ (value >>> 14)) >>> 0) / UINT32_MAX_PLUS_ONE;
  };
}

export function weightedPick(entries, rng = Math.random) {
  const choices = entries.filter(([, weight]) => Number.isFinite(weight) && weight > 0);
  if (!choices.length) throw new Error('weightedPick requires at least one positive weight');
  const total = choices.reduce((sum, [, weight]) => sum + weight, 0);
  let cursor = rng() * total;
  for (const [value, weight] of choices) {
    cursor -= weight;
    if (cursor < 0) return value;
  }
  return choices.at(-1)[0];
}

export function secureRandom() {
  if (globalThis.crypto?.getRandomValues) {
    const value = new Uint32Array(1);
    globalThis.crypto.getRandomValues(value);
    return value[0] / UINT32_MAX_PLUS_ONE;
  }
  return Math.random();
}

export function randomId(prefix = 'id') {
  if (globalThis.crypto?.randomUUID) return `${prefix}-${globalThis.crypto.randomUUID()}`;
  return `${prefix}-${Date.now().toString(36)}-${Math.floor(secureRandom() * UINT32_MAX_PLUS_ONE).toString(36)}`;
}
