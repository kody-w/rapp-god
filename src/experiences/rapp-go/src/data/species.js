import { createRng } from '../lib/rng.js';

export const ARCHETYPES = Object.freeze([
  'quadruped', 'biped', 'serpent', 'ray', 'moth', 'botanical',
  'crystal', 'shell', 'aquatic', 'mushroom', 'crawler', 'tripod'
]);

const ROOTS = [
  'Aeri', 'Bruma', 'Cindra', 'Dapple', 'Elow', 'Fenn', 'Glim', 'Hush',
  'Iri', 'Junra', 'Kest', 'Luma', 'Moss', 'Nimbi', 'Orra', 'Peb',
  'Quill', 'Rill', 'Sola', 'Tavi', 'Umber', 'Vela', 'Whim', 'Xylo',
  'Yarrow', 'Zeph', 'Coru', 'Drift', 'Ember', 'Flora', 'Goss'
];
const ENDINGS = ['a', 'ari', 'bell', 'bloom', 'drift', 'fin', 'horn', 'kin', 'light', 'mote', 'nook', 'tail', 'wing'];
const BODY_PROFILES = ['round', 'long', 'pear', 'diamond', 'stacked'];
const HEAD_STYLES = ['round', 'wedge', 'mask', 'bud', 'lantern'];
const EAR_STYLES = ['none', 'round', 'point', 'fin', 'leaf'];
const CREST_STYLES = ['none', 'horns', 'antlers', 'crystal', 'petals', 'cap'];
const TAIL_STYLES = ['none', 'whip', 'fan', 'orb', 'leaf'];
const WING_STYLES = ['none', 'leaf', 'membrane', 'veil'];
const ANIMATIONS = ['bound', 'amble', 'ripple', 'scuttle', 'sway', 'pulse', 'stalk', 'glide', 'coil', 'bloom', 'forage', 'hop'];
const TEMPERAMENTS = ['curious', 'gentle', 'watchful', 'restless', 'patient', 'playful', 'solemn', 'bright'];

function nameFor(index) {
  const root = ROOTS[index % ROOTS.length];
  const endingIndex = (Math.floor(index / ROOTS.length) * 5 + index * 7) % ENDINGS.length;
  return `${root}${ENDINGS[endingIndex]}`;
}

function blueprintFor(index) {
  const number = index + 1;
  const rng = createRng(`rapp-go-original-species-${number}`);
  const archetype = ARCHETYPES[index % ARCHETYPES.length];
  const secondaryOffset = 1 + Math.floor(rng() * (ARCHETYPES.length - 1));
  const secondaryArchetype = ARCHETYPES[(index + secondaryOffset) % ARCHETYPES.length];
  const wingBias = ['ray', 'moth'].includes(archetype) ? 1 + Math.floor(rng() * 3) : Math.floor(rng() * WING_STYLES.length);
  return Object.freeze({
    number,
    key: `rgo-${String(number).padStart(3, '0')}`,
    name: nameFor(index),
    archetype,
    secondaryArchetype,
    bodyProfile: BODY_PROFILES[Math.floor(rng() * BODY_PROFILES.length)],
    headStyle: HEAD_STYLES[Math.floor(rng() * HEAD_STYLES.length)],
    earStyle: EAR_STYLES[Math.floor(rng() * EAR_STYLES.length)],
    crestStyle: CREST_STYLES[Math.floor(rng() * CREST_STYLES.length)],
    tailStyle: TAIL_STYLES[Math.floor(rng() * TAIL_STYLES.length)],
    wingStyle: WING_STYLES[wingBias],
    animation: ANIMATIONS[(index * 5 + Math.floor(rng() * ANIMATIONS.length)) % ANIMATIONS.length],
    temperament: TEMPERAMENTS[(index * 3 + Math.floor(rng() * TEMPERAMENTS.length)) % TEMPERAMENTS.length],
    eyes: 1 + Math.floor(rng() * 4),
    legPairs: archetype === 'moth' ? 3 : archetype === 'quadruped' ? 2 : archetype === 'biped' ? 1 : archetype === 'tripod' ? 3 : Math.floor(rng() * 4),
    segments: archetype === 'serpent' ? 7 + Math.floor(rng() * 7) : 3 + Math.floor(rng() * 7),
    sizeBias: Math.round((0.78 + rng() * 0.5) * 1_000) / 1_000,
    limbBias: Math.round((0.62 + rng() * 0.78) * 1_000) / 1_000,
    tempoBias: Math.round((0.7 + rng() * 0.9) * 1_000) / 1_000
  });
}

export const SPECIES_CATALOG = Object.freeze(Array.from({ length: 151 }, (_, index) => blueprintFor(index)));

export function speciesByNumber(number) {
  return SPECIES_CATALOG[Number(number) - 1] || null;
}

export function speciesForArchetype(archetype) {
  return SPECIES_CATALOG.filter((species) => species.archetype === archetype);
}

export function speciesByKey(key) {
  return SPECIES_CATALOG.find((species) => species.key === key) || null;
}
