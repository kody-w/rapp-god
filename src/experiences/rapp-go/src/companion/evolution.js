import { stableStringify, sha256Hex } from '../lib/creature.js';
import { createRng, randomId } from '../lib/rng.js';

const clone = (value) => structuredClone(value);

async function frameSha(creature, previousSha) {
  return sha256Hex(`${stableStringify(creature)}${previousSha || ''}`);
}

export async function makeCompanionFrame(creature, previousSha, kind, note, extra = {}, now = Date.now()) {
  return {
    sha: await frameSha(creature, previousSha),
    prev: previousSha || '',
    at: now,
    kind,
    note,
    creature: clone(creature),
    ...extra
  };
}

export async function createCompanionProfile(starter, memory, { now = Date.now(), companionId = null } = {}) {
  const id = companionId || randomId('companion');
  const birth = await makeCompanionFrame(
    starter,
    '',
    'birth',
    `born from ${memory.label || 'a chosen memory'}`,
    { memorySources: memory.sources || [] },
    now
  );
  return {
    schema: 'rapp-go-companion/1.0',
    companionId: id,
    createdAt: now,
    memory: clone(memory),
    frames: [birth]
  };
}

export function currentCompanion(profile) {
  return profile?.frames?.at(-1)?.creature || null;
}

function pickDifferent(base, donor, rng) {
  if (base === donor) return donor;
  return rng() < 0.38 ? base : donor;
}

function blendNumber(base, donor, rng) {
  if (!Number.isFinite(base)) return donor;
  if (!Number.isFinite(donor)) return base;
  const choice = rng();
  if (choice < 0.28) return donor;
  if (choice < 0.55) return base * 0.35 + donor * 0.65;
  return (base + donor) / 2;
}

function spliceForm(base, donor, rng) {
  const result = { ...base };
  for (const key of new Set([...Object.keys(base), ...Object.keys(donor)])) {
    if (['species', 'lobes', 'eyes', 'appendages'].includes(key)) result[key] = pickDifferent(base[key], donor[key], rng);
    else if (typeof donor[key] === 'number') result[key] = blendNumber(base[key], donor[key], rng);
    else if (donor[key] !== undefined && rng() > 0.45) result[key] = donor[key];
  }
  result.species = donor.species || result.species;
  return result;
}

function spliceSurface(base, donor, rng) {
  const result = { ...base };
  const basePalette = base.palette || [];
  const donorPalette = donor.palette || [];
  const length = Math.max(basePalette.length, donorPalette.length, 3);
  result.palette = Array.from({ length }, (_, index) => {
    if (index === 0 && donorPalette.length) return donorPalette[index % donorPalette.length];
    return rng() < 0.45
      ? basePalette[index % Math.max(1, basePalette.length)] || donorPalette[index % donorPalette.length]
      : donorPalette[index % Math.max(1, donorPalette.length)] || basePalette[index % basePalette.length];
  });
  result.pattern = donor.pattern || base.pattern;
  result.glow = blendNumber(base.glow, donor.glow, rng);
  return result;
}

function spliceMotion(base, donor, rng) {
  const result = { ...base };
  for (const key of new Set([...Object.keys(base), ...Object.keys(donor)])) {
    result[key] = typeof donor[key] === 'number' ? blendNumber(base[key], donor[key], rng) : (base[key] ?? donor[key]);
  }
  return result;
}

export async function spliceCreature(primary, donor, traits = ['surface'], seed = '') {
  const selected = traits.length ? traits : ['surface'];
  const rng = createRng(seed || `${primary.id}×${donor.id}`);
  const genome = clone(primary.genome);
  if (selected.includes('form')) genome.form = spliceForm(primary.genome.form, donor.genome.form, rng);
  if (selected.includes('surface')) genome.surface = spliceSurface(primary.genome.surface, donor.genome.surface, rng);
  if (selected.includes('motion')) genome.motion = spliceMotion(primary.genome.motion, donor.genome.motion, rng);
  genome.inheritance = {
    generation: Number(primary.genome.inheritance?.generation || 0) + 1,
    donor: donor.id,
    traits: selected
  };
  const id = (await sha256Hex(stableStringify(genome))).slice(0, 16);
  return {
    ...clone(primary),
    id,
    species: genome.form.species || primary.species,
    speciesNumber: genome.form.speciesNumber || primary.speciesNumber,
    distinctiveTrait: genome.form.signatureTrait || primary.distinctiveTrait,
    genome,
    origin: 'companion'
  };
}

export async function evolveCompanion(profile, donor, traits, now = Date.now()) {
  const primary = currentCompanion(profile);
  if (!primary) throw new Error('A primary companion is required before splicing');
  const head = profile.frames.at(-1);
  const seed = `${primary.id}×${donor.id}×${head.sha}`;
  const evolved = await spliceCreature(primary, donor, traits, seed);
  const frame = await makeCompanionFrame(
    evolved,
    head.sha,
    'splice',
    `absorbed ${traits.join(' + ')} from ${donor.name}`,
    { donorId: donor.id, traits: [...traits] },
    now
  );
  return { ...clone(profile), frames: [...profile.frames, frame] };
}

export async function revertCompanion(profile, targetSha, now = Date.now()) {
  const target = profile.frames.find((frame) => frame.sha === targetSha);
  if (!target) throw new Error('That companion frame does not exist');
  const head = profile.frames.at(-1);
  const frame = await makeCompanionFrame(
    target.creature,
    head.sha,
    'revert',
    `returned to the form at ${target.sha.slice(0, 8)}`,
    { targetSha },
    now
  );
  return { ...clone(profile), frames: [...profile.frames, frame] };
}

export async function validateCompanionHistory(profile) {
  for (const frame of profile?.frames || []) {
    if (await frameSha(frame.creature, frame.prev) !== frame.sha) return false;
  }
  return true;
}
