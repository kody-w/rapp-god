import { createCreature } from '../lib/creature.js';
import { geohashEncode, haversineMeters, offsetLocation } from '../lib/geo.js';
import { createRng } from '../lib/rng.js';

export const SPAWN_BUCKET_MS = 30 * 60 * 1000;

export function spawnBucket(now = Date.now()) {
  return Math.floor(now / SPAWN_BUCKET_MS);
}

export async function generateSpawns({ location, weather, now = Date.now(), count = 7, luredPlaces = [] }) {
  const bucket = spawnBucket(now);
  const cell = geohashEncode(location.lat, location.lng, 6);
  const rng = createRng(`${cell}:${bucket}:field-v2`);
  const anchors = [{ east: 14, north: 12 }];
  for (let index = 1; index < count; index += 1) {
    const angle = rng() * Math.PI * 2;
    const radius = 38 + rng() * 145;
    anchors.push({ east: Math.cos(angle) * radius, north: Math.sin(angle) * radius });
  }
  for (const place of luredPlaces) {
    if (anchors.length >= count + 2) break;
    const angle = rng() * Math.PI * 2;
    const point = offsetLocation(place, Math.cos(angle) * 18, Math.sin(angle) * 18);
    anchors.push({ fixed: point });
  }

  const spawns = await Promise.all(anchors.map(async (anchor, index) => {
    const point = anchor.fixed || offsetLocation(location, anchor.east, anchor.north);
    const creature = await createCreature({
      seed: `${cell}:${bucket}:spawn:${index}`,
      location: point,
      weather,
      bucket,
      variant: index,
      origin: 'wild'
    });
    return {
      id: `spawn-${bucket}-${creature.id}-${index}`,
      lat: point.lat,
      lng: point.lng,
      anchor: point,
      distanceM: haversineMeters(location, point),
      creature,
      seed: `${cell}:${bucket}:${index}`
    };
  }));
  return spawns.sort((a, b) => a.distanceM - b.distanceM);
}

export function wanderingPosition(spawn, now = Date.now()) {
  const rng = createRng(spawn.seed);
  const period = 25_000 + rng() * 20_000;
  const phase = (now % period) / period * Math.PI * 2;
  const radius = 3 + rng() * 8;
  return offsetLocation(spawn.anchor, Math.cos(phase) * radius, Math.sin(phase * 0.82) * radius);
}
