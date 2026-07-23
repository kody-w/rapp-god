import test from 'node:test';
import assert from 'node:assert/strict';

import { geohashDecode, geohashEncode, haversineMeters, offsetLocation, privacyCell } from '../../src/lib/geo.js';
import { createRng, hashString, weightedPick } from '../../src/lib/rng.js';

test('seeded random sequences are stable and distinct', () => {
  const first = createRng('same-field');
  const second = createRng('same-field');
  const other = createRng('other-field');
  const a = Array.from({ length: 12 }, first);
  const b = Array.from({ length: 12 }, second);
  const c = Array.from({ length: 12 }, other);
  assert.deepEqual(a, b);
  assert.notDeepEqual(a, c);
  assert.ok(a.every((value) => value >= 0 && value < 1));
  assert.equal(hashString('same-field'), hashString('same-field'));
});

test('weighted picks respect exact boundaries', () => {
  const choices = [['a', 2], ['b', 3], ['c', 5]];
  assert.equal(weightedPick(choices, () => 0), 'a');
  assert.equal(weightedPick(choices, () => 0.21), 'b');
  assert.equal(weightedPick(choices, () => 0.99), 'c');
  assert.throws(() => weightedPick([['none', 0]], () => 0));
});

test('geohashes round-trip globally within their decoded cell', () => {
  const fixtures = [
    { lat: 40.7128, lng: -74.006 },
    { lat: -33.8688, lng: 151.2093 },
    { lat: 35.6762, lng: 139.6503 },
    { lat: 0, lng: 0 }
  ];
  for (const point of fixtures) {
    const hash = geohashEncode(point.lat, point.lng, 7);
    const decoded = geohashDecode(hash);
    assert.ok(point.lat >= decoded.bounds.south && point.lat <= decoded.bounds.north);
    assert.ok(point.lng >= decoded.bounds.west && point.lng <= decoded.bounds.east);
  }
});

test('privacy cells use a cell center rather than the raw point', () => {
  const raw = { lat: 33.7490123, lng: -84.3879824 };
  const cell = privacyCell(raw, 5);
  assert.notEqual(cell.lat, raw.lat);
  assert.notEqual(cell.lng, raw.lng);
  assert.equal(cell.hash, geohashEncode(raw.lat, raw.lng, 5));
});

test('meter offsets and haversine distance agree', () => {
  const start = { lat: 40.7128, lng: -74.006 };
  const moved = offsetLocation(start, 30, 40);
  assert.ok(Math.abs(haversineMeters(start, moved) - 50) < 0.15);
});
