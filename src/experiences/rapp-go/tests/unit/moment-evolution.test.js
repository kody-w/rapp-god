import test from 'node:test';
import assert from 'node:assert/strict';

import {
  createCompanionProfile,
  currentCompanion,
  evolveCompanion,
  revertCompanion,
  validateCompanionHistory
} from '../../src/companion/evolution.js';
import { ARCHETYPES, SPECIES_CATALOG } from '../../src/data/species.js';
import { createMomentCreature } from '../../src/lib/creature.js';
import { createMoment, momentSourceLabel, thoughtTraits } from '../../src/lib/moment.js';

const location = { lat: 40.7128, lng: -74.006 };
const weather = { temperature: 19, code: 2, wind: 7, isDay: true };
const bucket = 981_000;

function memory(overrides = {}) {
  return createMoment({
    label: 'the station goodbye',
    thought: 'I wanted this minute to last longer',
    date: 1_767_700_800_000,
    mood: 'tender',
    picture: { palette: ['#aa5544', '#334477', '#eecb99'], luma: 0.56, contrast: 0.44 },
    sound: { energy: 0.72, texture: 0.31, durationBand: 3, kind: 'audio' },
    weather,
    location,
    placeLabel: 'the southbound platform',
    ...overrides
  });
}

test('the starting field guide contains exactly 151 unique original grounded species', () => {
  assert.equal(SPECIES_CATALOG.length, 151);
  assert.equal(new Set(SPECIES_CATALOG.map((species) => species.number)).size, 151);
  assert.equal(new Set(SPECIES_CATALOG.map((species) => species.name)).size, 151);
  assert.deepEqual([...new Set(SPECIES_CATALOG.map((species) => species.archetype))].sort(), [...ARCHETYPES].sort());
  assert.equal(ARCHETYPES.includes('orbital'), false);
  assert.ok(SPECIES_CATALOG.every((species) => species.animation && species.secondaryArchetype && species.temperament));
});

test('two individuals of one species keep the blueprint but receive different hallmark traits', async () => {
  const captured = memory();
  const first = await createMomentCreature({ seed: 'individual-a', location, weather, moment: captured.publicSignal, bucket, speciesNumber: 42 });
  const second = await createMomentCreature({ seed: 'individual-b', location, weather, moment: captured.publicSignal, bucket, speciesNumber: 42 });
  assert.equal(first.speciesNumber, 42);
  assert.equal(second.speciesNumber, 42);
  assert.equal(first.species, second.species);
  assert.notEqual(first.id, second.id);
  assert.notDeepEqual(first.genome.individual, second.genome.individual);
  assert.ok(first.distinctiveTrait);
  assert.ok(second.distinctiveTrait);
});

test('thoughts become deterministic traits while raw words stay private', () => {
  const first = thoughtTraits('a thought that stays with me');
  const second = thoughtTraits('a thought that stays with me');
  assert.deepEqual(first, second);
  assert.equal(first.hash.length, 8);

  const captured = memory();
  assert.match(captured.privateMemory.thought, /minute to last/u);
  assert.doesNotMatch(JSON.stringify(captured.publicSignal), /minute to last/u);
  assert.deepEqual(captured.publicSignal.sources, ['time', 'place', 'weather', 'picture', 'sound', 'thought']);
  assert.match(momentSourceLabel(captured.publicSignal), /picture/u);
  assert.match(momentSourceLabel(captured.publicSignal), /sound/u);
});

test('picture, sound, thought, weather, place, and time all enter the moment genome', async () => {
  const captured = memory();
  const creature = await createMomentCreature({
    seed: 'multimodal-memory',
    location,
    weather,
    moment: captured.publicSignal,
    bucket,
    variant: 0,
    axis: 'whole',
    origin: 'captured-moment'
  });
  assert.deepEqual(creature.genome.moment.sources, ['time', 'place', 'weather', 'picture', 'sound', 'thought']);
  assert.deepEqual(creature.genome.surface.palette, captured.publicSignal.picture.palette);
  assert.ok(creature.genome.motion.bob > 0.7);
  assert.doesNotMatch(JSON.stringify(creature), /station goodbye|minute to last/u);
});

test('splicing changes selected traits while preserving companion identity and history', async () => {
  const foundingMemory = memory();
  const donorMemory = memory({
    label: 'rain on the roof',
    thought: 'the whole room became percussion',
    picture: { palette: ['#225588', '#44aacc', '#dceeff'], luma: 0.38, contrast: 0.69 },
    sound: { energy: 0.94, texture: 0.82, durationBand: 5, kind: 'audio' },
    mood: 'stormy'
  });
  const starter = await createMomentCreature({ seed: 'starter', location, weather, moment: foundingMemory.publicSignal, bucket, axis: 'thought', origin: 'starter' });
  const donor = await createMomentCreature({ seed: 'donor', location, weather: { ...weather, code: 95 }, moment: donorMemory.publicSignal, bucket, axis: 'sound', origin: 'captured-moment' });
  const profile = await createCompanionProfile(starter, { ...foundingMemory.privateMemory, sources: foundingMemory.publicSignal.sources }, { now: 1_000, companionId: 'companion-fixed' });
  const evolved = await evolveCompanion(profile, donor, ['surface', 'motion'], 2_000);
  const current = currentCompanion(evolved);

  assert.equal(evolved.companionId, 'companion-fixed');
  assert.equal(evolved.frames.length, 2);
  assert.equal(evolved.frames[0].creature.id, starter.id);
  assert.notEqual(current.id, starter.id);
  assert.deepEqual(current.genome.form, starter.genome.form);
  assert.equal(current.genome.surface.palette[0], donor.genome.surface.palette[0]);
  assert.equal(current.genome.inheritance.donor, donor.id);
  assert.deepEqual(current.genome.inheritance.traits, ['surface', 'motion']);
  assert.equal(await validateCompanionHistory(evolved), true);

  const reverted = await revertCompanion(evolved, evolved.frames[0].sha, 3_000);
  assert.equal(reverted.frames.length, 3);
  assert.equal(currentCompanion(reverted).id, starter.id);
  assert.equal(reverted.companionId, 'companion-fixed');
  assert.equal(await validateCompanionHistory(reverted), true);

  reverted.frames[1].creature.name = 'tampered';
  assert.equal(await validateCompanionHistory(reverted), false);
});
