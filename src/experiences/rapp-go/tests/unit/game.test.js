import test from 'node:test';
import assert from 'node:assert/strict';

import { catchProbability, ringScale, rollCatch, throwQuality } from '../../src/game/catch.js';
import {
  BAG_CAP,
  DEFAULT_INVENTORY,
  activateLure,
  grantItems,
  inventoryCount,
  placeStatus,
  spendItem,
  spinPlace
} from '../../src/game/economy.js';
import { generateSpawns } from '../../src/game/spawns.js';

const location = { lat: 40.7128, lng: -74.006, accuracy: 5 };
const weather = { temperature: 19, code: 2, wind: 7, isDay: true };

test('catch probabilities honor rarity and modifiers', () => {
  const plain = catchProbability({ rarity: 'rare' });
  const helped = catchProbability({ rarity: 'rare', orbMultiplier: 1.8, treatMultiplier: 1.3, throwMultiplier: 1.35 });
  assert.ok(helped > plain);
  assert.ok(helped <= 0.96);
  assert.equal(rollCatch({ rarity: 'mythic' }, () => 0).caught, true);
  assert.equal(rollCatch({ rarity: 'common' }, () => 0.999).caught, false);
});

test('the timing ring has useful quality bands', () => {
  assert.ok(ringScale(0) > ringScale(750));
  assert.equal(throwQuality(750).label, 'perfect');
  assert.equal(throwQuality(0).label, 'steady');
  assert.equal(throwQuality(750, false).hit, false);
});

test('inventory grants clamp to the bag and spends cannot go negative', () => {
  const full = grantItems({}, [{ id: 'orb.glass', count: BAG_CAP + 20 }]);
  assert.equal(inventoryCount(full.inventory), BAG_CAP);
  assert.equal(full.full, true);
  const spent = spendItem({ 'orb.glass': 2 }, 'orb.glass', 2);
  assert.equal(spent.ok, true);
  assert.deepEqual(spent.inventory, {});
  assert.equal(spendItem({}, 'orb.glass', 1).ok, false);
});

test('places enforce range, cooldown, deterministic rewards, and lures', () => {
  const place = { id: 'test-fountain', lat: location.lat, lng: location.lng, kind: 'water' };
  const before = placeStatus(place, location, {}, 1_000);
  assert.equal(before.inRange, true);
  assert.equal(before.ready, true);

  const first = spinPlace({ place, location, inventory: DEFAULT_INVENTORY, spinState: {}, now: 1_000 });
  const repeatedFromFreshState = spinPlace({ place, location, inventory: DEFAULT_INVENTORY, spinState: {}, now: 1_000 });
  assert.equal(first.ok, true);
  assert.deepEqual(first.drops.map(({ id, count }) => ({ id, count })), repeatedFromFreshState.drops.map(({ id, count }) => ({ id, count })));

  const cooldown = spinPlace({ place, location, inventory: first.inventory, spinState: first.spinState, now: 1_001 });
  assert.equal(cooldown.ok, false);
  assert.equal(cooldown.reason, 'cooldown');

  const lure = activateLure({ place, inventory: { lure: 1 }, lureState: {}, now: 2_000 });
  assert.equal(lure.ok, true);
  assert.equal(lure.inventory.lure, undefined);
  assert.ok(lure.lureState[place.id] > 2_000);
});

test('spawn fields are deterministic, bounded, and weather-derived', async () => {
  const options = { location, weather, now: 1_767_700_800_000, count: 7 };
  const first = await generateSpawns(options);
  const second = await generateSpawns(structuredClone(options));
  assert.deepEqual(first, second);
  assert.equal(first.length, 7);
  assert.ok(first[0].distanceM < 25);
  assert.ok(first.every((spawn) => spawn.distanceM < 200));
  assert.ok(first.every((spawn) => spawn.creature.genome.weather.kind === 'cloud'));
});
