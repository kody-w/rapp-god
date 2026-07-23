import { geohashEncode } from './geo.js';
import { hashString } from './rng.js';

const DEFAULT_PALETTE = ['#7cc8a4', '#4f83c2', '#e6b86a'];

function channelHex(value) {
  return Math.max(0, Math.min(255, Math.round(value))).toString(16).padStart(2, '0');
}

function rgbHex(red, green, blue) {
  return `#${channelHex(red)}${channelHex(green)}${channelHex(blue)}`;
}

export function thoughtTraits(text = '') {
  const normalized = String(text).trim().replace(/\s+/gu, ' ').slice(0, 2_000);
  if (!normalized) return null;
  const words = normalized.split(' ');
  const letters = [...normalized].filter((character) => /[\p{L}\p{N}]/u.test(character));
  const punctuation = [...normalized].filter((character) => /[.!?,:;]/u.test(character)).length;
  const hash = hashString(normalized.toLocaleLowerCase()).toString(16).padStart(8, '0');
  return {
    hash,
    wordBand: Math.min(7, Math.floor(words.length / 4)),
    cadence: Math.round((punctuation / Math.max(1, words.length)) * 1_000) / 1_000,
    density: Math.round((letters.length / Math.max(1, normalized.length)) * 1_000) / 1_000
  };
}

export async function analyzeImage(file) {
  if (!file) return null;
  const bitmap = await createImageBitmap(file);
  const canvas = document.createElement('canvas');
  canvas.width = 48;
  canvas.height = 48;
  const context = canvas.getContext('2d', { willReadFrequently: true });
  context.drawImage(bitmap, 0, 0, 48, 48);
  bitmap.close?.();
  const pixels = context.getImageData(0, 0, 48, 48).data;
  const buckets = new Map();
  let lumaTotal = 0;
  let lumaSquared = 0;
  let samples = 0;
  for (let index = 0; index < pixels.length; index += 16) {
    if (pixels[index + 3] < 32) continue;
    const red = pixels[index];
    const green = pixels[index + 1];
    const blue = pixels[index + 2];
    const luma = 0.2126 * red + 0.7152 * green + 0.0722 * blue;
    lumaTotal += luma;
    lumaSquared += luma ** 2;
    samples += 1;
    const key = `${red >> 5}:${green >> 5}:${blue >> 5}`;
    const bucket = buckets.get(key) || { red: 0, green: 0, blue: 0, count: 0 };
    bucket.red += red;
    bucket.green += green;
    bucket.blue += blue;
    bucket.count += 1;
    buckets.set(key, bucket);
  }
  const palette = [...buckets.values()]
    .sort((a, b) => b.count - a.count)
    .slice(0, 3)
    .map((bucket) => rgbHex(bucket.red / bucket.count, bucket.green / bucket.count, bucket.blue / bucket.count));
  while (palette.length < 3) palette.push(DEFAULT_PALETTE[palette.length]);
  const mean = lumaTotal / Math.max(1, samples);
  const variance = lumaSquared / Math.max(1, samples) - mean ** 2;
  return {
    palette,
    luma: Math.round(mean / 255 * 1_000) / 1_000,
    contrast: Math.round(Math.sqrt(Math.max(0, variance)) / 128 * 1_000) / 1_000,
    orientation: file.type || 'image'
  };
}

export async function analyzeSound(file) {
  if (!file) return null;
  const AudioContext = globalThis.AudioContext || globalThis.webkitAudioContext;
  if (!AudioContext) return { energy: 0.5, texture: 0.5, durationBand: 1, kind: file.type || 'audio' };
  const context = new AudioContext();
  try {
    const audio = await context.decodeAudioData(await file.arrayBuffer());
    const data = audio.getChannelData(0);
    const stride = Math.max(1, Math.floor(data.length / 24_000));
    let energy = 0;
    let crossings = 0;
    let samples = 0;
    let previous = 0;
    for (let index = 0; index < data.length; index += stride) {
      const sample = data[index];
      energy += sample ** 2;
      if ((sample >= 0) !== (previous >= 0)) crossings += 1;
      previous = sample;
      samples += 1;
    }
    return {
      energy: Math.round(Math.min(1, Math.sqrt(energy / Math.max(1, samples)) * 4) * 1_000) / 1_000,
      texture: Math.round(Math.min(1, crossings / Math.max(1, samples) * 12) * 1_000) / 1_000,
      durationBand: Math.min(7, Math.floor(audio.duration / 5)),
      kind: file.type || 'audio'
    };
  } finally {
    await context.close().catch(() => {});
  }
}

export function createMoment({
  label,
  thought,
  date,
  mood = 'open',
  picture = null,
  sound = null,
  weather = null,
  location,
  placeLabel = ''
}) {
  const when = Number.isFinite(Number(date)) ? Number(date) : Date.now();
  const thoughtSignal = thoughtTraits(thought);
  const sources = ['time', 'place'];
  if (weather) sources.push('weather');
  if (picture) sources.push('picture');
  if (sound) sources.push('sound');
  if (thoughtSignal) sources.push('thought');
  const publicSignal = {
    schema: 'rapp-go-moment/1.0',
    sources,
    day: Math.floor(when / 86_400_000) * 86_400_000,
    hourBand: Math.floor(new Date(when).getHours() / 4),
    mood,
    place: { cell: geohashEncode(location.lat, location.lng, 6) },
    picture,
    sound,
    thought: thoughtSignal,
    weather: weather ? {
      temperatureBand: Math.round(Number(weather.temperature) / 3),
      code: Number(weather.code),
      windBand: Math.round(Number(weather.wind) / 3),
      isDay: Boolean(weather.isDay)
    } : null
  };
  const privateMemory = {
    label: String(label || 'the moment I began').trim().slice(0, 120),
    thought: String(thought || '').trim().slice(0, 2_000),
    at: when,
    mood,
    placeLabel: String(placeLabel || '').trim().slice(0, 120),
    sources,
    mediaReleased: true
  };
  return { publicSignal, privateMemory };
}

export function momentSourceLabel(moment) {
  const sources = moment?.sources || [];
  const names = {
    thought: 'a thought', picture: 'a picture', sound: 'a sound', weather: 'the weather',
    time: 'a time', place: 'a place'
  };
  return sources.map((source) => names[source] || source).join(' · ');
}

export function momentIcon(source) {
  return { thought: '“”', picture: '▧', sound: '∿', weather: '◌', time: '◷', place: '⌖' }[source] || '·';
}
