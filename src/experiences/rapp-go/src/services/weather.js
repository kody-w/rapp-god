import { privacyCell } from '../lib/geo.js';

export const WEATHER_BUCKET_MS = 30 * 60 * 1000;

export const DEMO_WEATHER = Object.freeze({
  temperature: 19,
  code: 2,
  wind: 7,
  isDay: true,
  source: 'demo',
  observedAt: 1_767_700_800_000
});

function fallbackWeather(now) {
  const hour = new Date(now).getHours();
  return {
    temperature: 18,
    code: hour > 6 && hour < 19 ? 2 : 0,
    wind: 5,
    isDay: hour > 6 && hour < 19,
    source: 'offline',
    observedAt: now
  };
}

function normalizeWeather(payload, now, source = 'live') {
  const current = payload?.current || {};
  const temperature = Number(current.temperature_2m);
  const code = Number(current.weather_code ?? current.weathercode);
  const wind = Number(current.wind_speed_10m ?? current.windspeed_10m ?? current.wind_speed);
  const isDay = Number(current.is_day ?? current.isDay);
  if (![temperature, code, wind, isDay].every(Number.isFinite)) throw new Error('Weather response was incomplete');
  return { temperature, code, wind, isDay: Boolean(isDay), source, observedAt: now };
}

export async function getWeather(location, {
  demo = false,
  now = Date.now(),
  fetchImpl = globalThis.fetch,
  store = null,
  timeoutMs = 8_000
} = {}) {
  if (demo) return { ...DEMO_WEATHER };
  const cell = privacyCell(location, 5);
  const bucket = Math.floor(now / WEATHER_BUCKET_MS);
  const cacheKey = `weather.${cell.hash}.${bucket}`;
  const cached = store?.get(cacheKey);
  if (cached) return { ...cached, source: cached.source === 'live' ? 'cache' : cached.source };
  if (typeof fetchImpl !== 'function') return fallbackWeather(now);

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const url = new URL('https://api.open-meteo.com/v1/forecast');
    url.searchParams.set('latitude', cell.lat.toFixed(5));
    url.searchParams.set('longitude', cell.lng.toFixed(5));
    url.searchParams.set('current', 'temperature_2m,weather_code,wind_speed_10m,is_day');
    url.searchParams.set('timezone', 'auto');
    const response = await fetchImpl(url, { signal: controller.signal });
    if (!response.ok) throw new Error(`Weather service returned ${response.status}`);
    const weather = normalizeWeather(await response.json(), now);
    store?.set(cacheKey, weather);
    return weather;
  } catch {
    return fallbackWeather(now);
  } finally {
    clearTimeout(timer);
  }
}
