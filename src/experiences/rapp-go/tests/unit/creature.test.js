import test from 'node:test';
import assert from 'node:assert/strict';

import {
  createCreature,
  decodeCreatureToken,
  encodeCreatureToken,
  stableStringify,
  sha256Hex,
  toLanternCartridge,
  verifyCreature,
  weatherKind
} from '../../src/lib/creature.js';

const fixture = {
  seed: 'fixture-cell:42',
  location: { lat: 40.7128, lng: -74.006 },
  weather: { temperature: 12.5, code: 61, wind: 18, isDay: false },
  bucket: 42,
  variant: 2
};

test('weather codes map to the expected creature climates', () => {
  assert.equal(weatherKind(0, true), 'clear');
  assert.equal(weatherKind(0, false), 'night');
  assert.equal(weatherKind(45, true), 'fog');
  assert.equal(weatherKind(61, true), 'rain');
  assert.equal(weatherKind(75, true), 'snow');
  assert.equal(weatherKind(95, true), 'storm');
});

test('the same sky creates the same content-addressed creature', async () => {
  const first = await createCreature(fixture);
  const second = await createCreature(structuredClone(fixture));
  assert.deepEqual(first, second);
  assert.equal(first.id.length, 16);
  assert.equal(await verifyCreature(first), true);
});

test('a different spawn variant changes the genome and id', async () => {
  const first = await createCreature(fixture);
  const other = await createCreature({ ...fixture, variant: 3 });
  assert.notEqual(first.id, other.id);
  assert.notDeepEqual(first.genome, other.genome);
});

test('shared creature tokens round-trip and reject disguises', async () => {
  const creature = await createCreature(fixture);
  const token = encodeCreatureToken(creature);
  const decoded = await decodeCreatureToken(token);
  assert.deepEqual(decoded, creature);

  const disguised = { ...creature, id: `${creature.id[0] === '0' ? '1' : '0'}${creature.id.slice(1)}` };
  await assert.rejects(() => decodeCreatureToken(encodeCreatureToken(disguised)), /could not be verified/u);
});

test('moment creatures export as content-addressed rapp-lantern cartridges', async () => {
  const creature = await createCreature(fixture);
  const cartridge = await toLanternCartridge(creature);
  assert.equal(cartridge.schema, 'hologram-cartridge/1.0');
  assert.deepEqual(cartridge.genome.layers.map((layer) => layer.role), ['form', 'surface', 'motion']);
  assert.equal(cartridge.id, (await sha256Hex(stableStringify(cartridge.genome))).slice(0, 12));
  assert.match(cartridge.born.from, /captured moment/u);
});
