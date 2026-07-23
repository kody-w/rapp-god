import { ARCHETYPES, SPECIES_CATALOG, speciesByNumber, speciesForArchetype } from '../data/species.js';
import { geohashEncode } from './geo.js';
import { createRng, weightedPick } from './rng.js';

export const CREATURE_SCHEMA = 'rapp-go-creature/2.0';

const SPECIES = SPECIES_CATALOG.map((species) => species.name);
const PREFIXES = ['Quiet', 'Silver', 'Moss', 'Velvet', 'Little', 'Dawn', 'Rain', 'Hollow', 'Soft', 'Ember'];
const NOUNS = ['Murmur', 'Kite', 'Fern', 'Pebble', 'Current', 'Lantern', 'Comet', 'Thistle', 'Ripple', 'Echo'];
const SIGNATURE_TRAITS = [
  'back sail', 'chest gem', 'split tail', 'shoulder plates', 'crown buds',
  'long whiskers', 'ankle tufts', 'side crest', 'shell ridges', 'mask freckles',
  'elbow fins', 'brow horns', 'leaf mane', 'glass spines', 'ring markings',
  'ribbon ears', 'moss collar', 'luminous throat', 'stone knees', 'fan crest'
];
const FINISHES = ['velvet', 'matte', 'pearl', 'stone', 'glass', 'bark', 'satin', 'speckled'];
const MARKINGS = ['none', 'freckles', 'saddle', 'mask', 'rings', 'dapple', 'stripe', 'constellation'];
const GAITS = ['careful', 'bounding', 'rolling', 'prancing', 'scuttling', 'stalking', 'lilting', 'springing'];

const PALETTES = {
  clear: [['#f7c76a', '#ff8a5b', '#fff1bd'], ['#8ad8e8', '#4f8fd8', '#e8fbff']],
  cloud: [['#9ab0c7', '#64748b', '#e8eef3'], ['#b5a9c9', '#746b8c', '#f4efff']],
  rain: [['#62b6cb', '#277da1', '#cdeff4'], ['#7cc8b8', '#3b7f78', '#dff7ef']],
  storm: [['#7b6ee8', '#413b79', '#f2c94c'], ['#9b7ede', '#38304f', '#f7d774']],
  snow: [['#c9eff7', '#78b8d0', '#ffffff'], ['#dfe4ff', '#8792c7', '#ffffff']],
  fog: [['#b8c4bd', '#74847c', '#eef3ef'], ['#c8c5bc', '#817e77', '#f5f2e8']],
  night: [['#6071c7', '#242b5c', '#d8d7ff'], ['#815ac0', '#30234f', '#f1dcff']]
};

export function weatherKind(code, isDay = true) {
  if (!isDay && Number(code) <= 3) return 'night';
  if ([95, 96, 99].includes(Number(code))) return 'storm';
  if (Number(code) >= 71 && Number(code) <= 86) return 'snow';
  if ((Number(code) >= 51 && Number(code) <= 67) || (Number(code) >= 80 && Number(code) <= 82)) return 'rain';
  if ([45, 48].includes(Number(code))) return 'fog';
  if (Number(code) >= 1 && Number(code) <= 3) return 'cloud';
  return 'clear';
}

export function weatherLabel(weather) {
  const kind = weatherKind(weather.code, weather.isDay);
  const labels = {
    clear: 'clear sky', cloud: 'soft clouds', rain: 'rain', storm: 'storm light',
    snow: 'snow', fog: 'fog', night: 'night sky'
  };
  return labels[kind];
}

export function stableStringify(value) {
  if (Array.isArray(value)) return `[${value.map(stableStringify).join(',')}]`;
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${stableStringify(value[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

export async function sha256Hex(value) {
  const bytes = typeof value === 'string' ? new TextEncoder().encode(value) : value;
  if (!globalThis.crypto?.subtle) throw new Error('Web Crypto is required');
  const digest = await globalThis.crypto.subtle.digest('SHA-256', bytes);
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, '0')).join('');
}

function archetypeWeights(kind, moment) {
  const base = Object.fromEntries(ARCHETYPES.map((archetype) => [archetype, 1]));
  const boosts = {
    clear: { quadruped: 2, ray: 3, botanical: 1 }, cloud: { ray: 4, moth: 2, crawler: 2 },
    rain: { serpent: 3, aquatic: 4, botanical: 2 }, storm: { crystal: 5, tripod: 2, crawler: 2 },
    snow: { crystal: 3, shell: 3, quadruped: 1 }, fog: { orbital: 4, mushroom: 3, ray: 2 },
    night: { moth: 3, mushroom: 2, crawler: 3 }
  }[kind] || {};
  for (const [archetype, weight] of Object.entries(boosts)) base[archetype] += weight;
  const sources = new Set(moment?.sources || []);
  if (sources.has('sound')) { base.moth += 3; base.serpent += 2; base.tripod += 1; }
  if (sources.has('picture')) { base.botanical += 2; base.crystal += 2; base.quadruped += 1; }
  if (sources.has('thought')) { base.crawler += 3; base.biped += 2; base.mushroom += 1; }
  if (moment?.mood === 'bright') { base.ray += 2; base.moth += 1; }
  if (moment?.mood === 'still') { base.botanical += 2; base.shell += 2; }
  if (moment?.mood === 'stormy') { base.crystal += 3; base.tripod += 2; }
  if (moment?.mood === 'tender') { base.quadruped += 3; base.mushroom += 1; }
  return Object.entries(base);
}

function rarityFromRoll(roll, kind, moment) {
  const weatherBoost = kind === 'storm' ? 0.14 : kind === 'snow' || kind === 'fog' ? 0.06 : 0;
  const signalBoost = Math.max(0, (moment?.sources?.length || 2) - 2) * 0.018;
  const score = Math.min(0.999, roll + weatherBoost + signalBoost);
  if (score >= 0.975) return 'mythic';
  if (score >= 0.9) return 'legendary';
  if (score >= 0.72) return 'rare';
  if (score >= 0.42) return 'uncommon';
  return 'common';
}

function ambientMoment(weather, location, bucket) {
  return {
    schema: 'rapp-go-moment/1.0',
    sources: ['time', 'place', 'weather'],
    day: Math.floor(Number(bucket) * 30 * 60 * 1000 / 86_400_000) * 86_400_000,
    hourBand: Math.floor(new Date(Number(bucket) * 30 * 60 * 1000).getHours() / 4),
    mood: 'open',
    place: { cell: geohashEncode(location.lat, location.lng, 6) },
    picture: null,
    sound: null,
    thought: null,
    weather: {
      temperatureBand: Math.round(Number(weather.temperature) / 3),
      code: Number(weather.code),
      windBand: Math.round(Number(weather.wind) / 3),
      isDay: Boolean(weather.isDay)
    }
  };
}

export async function createMomentCreature({ seed, location, weather, moment, bucket, variant = 0, axis = 'whole', origin = 'wild', speciesNumber = null }) {
  const kind = weatherKind(weather.code, weather.isDay);
  const signal = moment || ambientMoment(weather, location, bucket);
  const rng = createRng(`${seed}:${variant}:${kind}:${axis}:${stableStringify(signal)}`);
  const momentArchetype = weightedPick(archetypeWeights(kind, signal), rng);
  const speciesChoices = speciesForArchetype(momentArchetype);
  const blueprint = speciesByNumber(speciesNumber) || speciesChoices[Math.floor(rng() * speciesChoices.length)];
  const archetype = blueprint.archetype;
  const species = blueprint.name;
  const secondaryArchetype = blueprint.secondaryArchetype;
  const paletteOptions = PALETTES[kind] || PALETTES.clear;
  const weatherPalette = paletteOptions[Math.floor(rng() * paletteOptions.length)];
  const picturePalette = signal.picture?.palette?.filter((color) => /^#[0-9a-f]{6}$/iu.test(color));
  const palette = picturePalette?.length
    ? [picturePalette[0], picturePalette[1] || weatherPalette[1], picturePalette[2] || weatherPalette[2]]
    : weatherPalette;
  const soundEnergy = Number(signal.sound?.energy ?? 0.4);
  const soundTexture = Number(signal.sound?.texture ?? 0.35);
  const thoughtCadence = Number(signal.thought?.cadence ?? 0.1);
  const pictureLuma = Number(signal.picture?.luma ?? 0.5);
  const pictureContrast = Number(signal.picture?.contrast ?? 0.35);
  const individual = {
    signatureTrait: SIGNATURE_TRAITS[Math.floor(rng() * SIGNATURE_TRAITS.length)],
    finish: FINISHES[Math.floor(rng() * FINISHES.length)],
    marking: signal.picture ? (pictureContrast > 0.48 ? 'constellation' : 'dapple') : MARKINGS[Math.floor(rng() * MARKINGS.length)],
    gait: signal.sound ? (soundEnergy > 0.7 ? 'bounding' : soundTexture > 0.55 ? 'scuttling' : 'lilting') : GAITS[Math.floor(rng() * GAITS.length)],
    stature: Math.round((0.82 + rng() * 0.4) * 1_000) / 1_000,
    headScale: Math.round((0.76 + rng() * 0.48) * 1_000) / 1_000,
    eyeScale: Math.round((0.78 + rng() * 0.5) * 1_000) / 1_000,
    limbLength: Math.round((0.72 + rng() * 0.62) * 1_000) / 1_000,
    tailCurl: Math.round((rng() * 2 - 1) * 1_000) / 1_000,
    asymmetry: Math.round((rng() * 2 - 1) * 1_000) / 1_000,
    markingDensity: Math.round((0.15 + rng() * 0.8) * 1_000) / 1_000,
    accentIndex: Math.floor(rng() * 3)
  };
  const genome = {
    version: 2,
    seed: String(seed),
    moment: signal,
    individual,
    weather: {
      kind,
      code: Number(weather.code),
      temperature: Math.round(Number(weather.temperature) * 10) / 10,
      wind: Math.round(Number(weather.wind) * 10) / 10,
      isDay: Boolean(weather.isDay)
    },
    form: {
      species,
      speciesNumber: blueprint.number,
      speciesKey: blueprint.key,
      archetype,
      secondaryArchetype,
      bodyProfile: blueprint.bodyProfile,
      headStyle: blueprint.headStyle,
      earStyle: blueprint.earStyle,
      crestStyle: blueprint.crestStyle,
      tailStyle: blueprint.tailStyle,
      wingStyle: blueprint.wingStyle,
      animation: blueprint.animation,
      temperament: blueprint.temperament,
      lobes: 2 + Math.floor(rng() * 4 + (axis === 'thought' ? thoughtCadence * 4 : 0)),
      eyes: Math.max(1, Math.min(4, blueprint.eyes + (axis === 'thought' && thoughtCadence > 0.2 ? 1 : 0))),
      appendages: Math.min(8, Math.floor(rng() * 6 + (axis === 'sound' ? soundTexture * 3 : 0))),
      legPairs: blueprint.legPairs,
      segments: blueprint.segments,
      roundness: Math.round((0.48 + blueprint.sizeBias * 0.18 + rng() * 0.15 + pictureLuma * 0.1) * 1000) / 1000,
      tilt: Math.round((rng() * 2 - 1) * 1000) / 1000,
      headRatio: Math.round((0.55 + rng() * 0.65) * individual.headScale * 1000) / 1000,
      eyeScale: individual.eyeScale,
      limbScale: Math.round((blueprint.limbBias * individual.limbLength) * 1000) / 1000,
      tailLength: Math.round((0.45 + rng() * 1.1) * 1000) / 1000,
      signatureTrait: individual.signatureTrait,
      asymmetry: individual.asymmetry
    },
    surface: {
      palette,
      finish: individual.finish,
      marking: individual.marking,
      markingDensity: individual.markingDensity,
      glow: Math.round(Math.min(0.95, 0.12 + rng() * 0.45 + pictureLuma * 0.3) * 1000) / 1000,
      pattern: signal.picture
        ? (pictureContrast > 0.48 ? 'constellation' : pictureContrast > 0.25 ? 'spots' : 'rings')
        : weightedPick([['plain', 4], ['spots', 3], ['rings', 2], ['constellation', 1]], rng)
    },
    motion: {
      bob: Math.round((0.58 + rng() * 0.7 + soundEnergy * 0.72) * 1000) / 1000,
      sway: Math.round((0.35 + rng() * 0.65 + soundTexture * 0.85) * 1000) / 1000,
      pulse: Math.round((1.15 + rng() * 1.2 + soundEnergy * 1.4 + thoughtCadence * 0.5) * blueprint.tempoBias * 1000) / 1000,
      gait: individual.gait
    }
  };
  const id = (await sha256Hex(stableStringify(genome))).slice(0, 16);
  const nameRng = createRng(id);
  const name = `${PREFIXES[Math.floor(nameRng() * PREFIXES.length)]} ${NOUNS[Math.floor(nameRng() * NOUNS.length)]}`;
  return {
    schema: CREATURE_SCHEMA,
    id,
    name,
    rarity: rarityFromRoll(nameRng(), kind, signal),
    species,
    speciesNumber: blueprint.number,
    distinctiveTrait: individual.signatureTrait,
    origin,
    birth: {
      cell: geohashEncode(location.lat, location.lng, 6),
      bucket: Number(bucket),
      sources: [...signal.sources],
      day: signal.day
    },
    genome
  };
}

export async function createCreature(options) {
  return createMomentCreature(options);
}

export async function verifyCreature(creature) {
  if (!creature || creature.schema !== CREATURE_SCHEMA || !creature.genome || typeof creature.id !== 'string') return false;
  const expected = (await sha256Hex(stableStringify(creature.genome))).slice(0, 16);
  return expected === creature.id;
}

export function publicCreature(creature) {
  return {
    schema: creature.schema,
    id: creature.id,
    name: creature.name,
    rarity: creature.rarity,
    species: creature.species,
    speciesNumber: creature.speciesNumber,
    distinctiveTrait: creature.distinctiveTrait,
    origin: creature.origin,
    birth: creature.birth,
    genome: creature.genome
  };
}

function bytesToBase64(bytes) {
  if (typeof btoa === 'function') {
    let binary = '';
    for (let index = 0; index < bytes.length; index += 1) binary += String.fromCharCode(bytes[index]);
    return btoa(binary);
  }
  return Buffer.from(bytes).toString('base64');
}

function base64ToBytes(value) {
  if (typeof atob === 'function') {
    const binary = atob(value);
    return Uint8Array.from(binary, (character) => character.charCodeAt(0));
  }
  return Uint8Array.from(Buffer.from(value, 'base64'));
}

export function encodeCreatureToken(creature) {
  const json = JSON.stringify(publicCreature(creature));
  return bytesToBase64(new TextEncoder().encode(json)).replaceAll('+', '-').replaceAll('/', '_').replace(/=+$/u, '');
}

export async function decodeCreatureToken(token) {
  try {
    const base64 = String(token).replaceAll('-', '+').replaceAll('_', '/');
    const padded = base64 + '='.repeat((4 - base64.length % 4) % 4);
    const creature = JSON.parse(new TextDecoder().decode(base64ToBytes(padded)));
    if (!await verifyCreature(creature)) throw new Error('Creature signature does not match its genome');
    return creature;
  } catch (error) {
    throw new Error(`This creature link could not be verified: ${error.message}`);
  }
}

export async function toLanternCartridge(creature) {
  const form = creature.genome.form || {};
  const surface = creature.genome.surface || {};
  const motion = creature.genome.motion || {};
  const clamp = (value, minimum, maximum) => Math.min(maximum, Math.max(minimum, value));
  const shape = {
    mote: 'ring', drifter: 'blob', sprig: 'star', wisp: 'segment',
    skimmer: 'star', coil: 'segment', bloom: 'star', shard: 'star'
  }[creature.species] || 'blob';
  const pattern = {
    plain: 'solid', solid: 'solid', spots: 'spot', spot: 'spot', rings: 'stripe',
    stripe: 'stripe', constellation: 'glow', glow: 'glow'
  }[surface.pattern] || 'solid';
  const genome = {
    layers: [
      {
        role: 'form',
        shape,
        limbs: clamp(Math.round(form.appendages || 0), 0, 12),
        segments: clamp(Math.round((form.lobes || 3) + 3), 3, 14),
        symmetry: form.eyes === 1 ? 'radial' : 'bilateral',
        body_r: clamp(0.24 + Number(form.roundness || 0.7) * 0.16, 0.24, 0.44),
        limb_len: clamp(0.24 + Number(form.appendages || 0) * 0.025, 0.24, 0.55),
        spikes: creature.species === 'shard' ? clamp((form.appendages || 3) + 2, 2, 10) : Math.max(0, (form.lobes || 3) - 3)
      },
      {
        role: 'surface',
        palette: surface.palette || ['#7cc8a4', '#4f83c2', '#f5ead0'],
        pattern,
        glow: clamp(Number(surface.glow || 0), 0, 1),
        opacity: 0.92
      },
      {
        role: 'motion',
        breathe: clamp(Number(motion.bob || 1) * 0.18, 0.08, 0.5),
        drift: clamp(Number(motion.sway || 1) * 0.22, 0.08, 0.65),
        pulse: clamp(Number(motion.pulse || 2) * 0.18, 0.12, 0.9),
        reach: clamp(Number(form.appendages || 0) * 0.055, 0.08, 0.55)
      }
    ],
    compose: { windows: [[0, 1, 2]], loop: true }
  };
  const id = (await sha256Hex(stableStringify(genome))).slice(0, 12);
  const bornAt = Number(creature.birth?.day || creature.birth?.bucket * 30 * 60 * 1000 || Date.now());
  return {
    schema: 'hologram-cartridge/1.0',
    id,
    title: creature.name,
    author: '@you',
    born: {
      coord: `${creature.birth?.cell || '0,0'}·${bornAt}`,
      from: `a captured moment · ${(creature.genome.moment?.sources || []).join(' + ') || 'unknown source'}`
    },
    parents: creature.genome.inheritance?.donor ? [creature.genome.inheritance.donor] : [],
    genome,
    sig: ''
  };
}

export { SPECIES };
