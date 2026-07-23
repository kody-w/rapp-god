import { clamp } from '../lib/geo.js';
import { secureRandom } from '../lib/rng.js';

export const CATCH_TIERS = {
  common: { base: 0.78, flee: 0.05 },
  uncommon: { base: 0.62, flee: 0.08 },
  rare: { base: 0.43, flee: 0.12 },
  legendary: { base: 0.25, flee: 0.18 },
  mythic: { base: 0.13, flee: 0.24 }
};

export function ringScale(elapsedMs, periodMs = 1_500) {
  const phase = ((elapsedMs % periodMs) + periodMs) % periodMs / periodMs;
  return 0.34 + 0.66 * (0.5 + 0.5 * Math.cos(phase * Math.PI * 2));
}

export function throwQuality(elapsedMs, hit = true) {
  if (!hit) return { label: 'wide', multiplier: 0, hit: false };
  const scale = ringScale(elapsedMs);
  if (scale <= 0.43) return { label: 'perfect', multiplier: 1.65, hit: true };
  if (scale <= 0.58) return { label: 'great', multiplier: 1.35, hit: true };
  if (scale <= 0.76) return { label: 'nice', multiplier: 1.15, hit: true };
  return { label: 'steady', multiplier: 1, hit: true };
}

export function catchProbability({ rarity, orbMultiplier = 1, treatMultiplier = 1, throwMultiplier = 1 }) {
  const tier = CATCH_TIERS[rarity] || CATCH_TIERS.common;
  return clamp(tier.base * orbMultiplier * treatMultiplier * throwMultiplier, 0.04, 0.96);
}

export function rollCatch(options, rng = secureRandom) {
  const probability = catchProbability(options);
  const holdChance = probability ** (1 / 3);
  let wobbles = 0;
  for (let check = 0; check < 3; check += 1) {
    if (rng() >= holdChance) break;
    wobbles += 1;
  }
  const caught = wobbles === 3;
  const fleeChance = clamp((CATCH_TIERS[options.rarity] || CATCH_TIERS.common).flee * (options.fleeMultiplier ?? 1), 0, 0.65);
  const fled = !caught && rng() < fleeChance;
  return { probability, holdChance, wobbles, caught, fled, fleeChance };
}
