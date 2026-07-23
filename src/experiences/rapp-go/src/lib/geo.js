const BASE32 = '0123456789bcdefghjkmnpqrstuvwxyz';
const EARTH_RADIUS_M = 6_371_000;

export function clamp(value, minimum, maximum) {
  return Math.min(maximum, Math.max(minimum, value));
}

export function normalizeLocation(location) {
  const lat = Number(location?.lat ?? location?.latitude);
  const lng = Number(location?.lng ?? location?.lon ?? location?.longitude);
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) throw new TypeError('A finite latitude and longitude are required');
  return { lat: clamp(lat, -85.05112878, 85.05112878), lng: ((lng + 540) % 360) - 180 };
}

export function haversineMeters(a, b) {
  const first = normalizeLocation(a);
  const second = normalizeLocation(b);
  const radians = (degrees) => degrees * Math.PI / 180;
  const dLat = radians(second.lat - first.lat);
  const dLng = radians(second.lng - first.lng);
  const value = Math.sin(dLat / 2) ** 2
    + Math.cos(radians(first.lat)) * Math.cos(radians(second.lat)) * Math.sin(dLng / 2) ** 2;
  return 2 * EARTH_RADIUS_M * Math.asin(Math.sqrt(value));
}

export function offsetLocation(origin, eastMeters, northMeters) {
  const point = normalizeLocation(origin);
  const lat = point.lat + (northMeters / EARTH_RADIUS_M) * (180 / Math.PI);
  const lng = point.lng + (eastMeters / (EARTH_RADIUS_M * Math.cos(point.lat * Math.PI / 180))) * (180 / Math.PI);
  return normalizeLocation({ lat, lng });
}

export function geohashEncode(latitude, longitude, precision = 7) {
  const point = normalizeLocation({ lat: latitude, lng: longitude });
  let latRange = [-90, 90];
  let lngRange = [-180, 180];
  let hash = '';
  let bit = 0;
  let character = 0;
  let useLongitude = true;

  while (hash.length < precision) {
    const range = useLongitude ? lngRange : latRange;
    const value = useLongitude ? point.lng : point.lat;
    const midpoint = (range[0] + range[1]) / 2;
    if (value >= midpoint) {
      character |= 1 << (4 - bit);
      range[0] = midpoint;
    } else {
      range[1] = midpoint;
    }
    useLongitude = !useLongitude;
    bit += 1;
    if (bit === 5) {
      hash += BASE32[character];
      bit = 0;
      character = 0;
    }
  }
  return hash;
}

export function geohashDecode(hash) {
  if (!hash || typeof hash !== 'string') throw new TypeError('A geohash string is required');
  let latRange = [-90, 90];
  let lngRange = [-180, 180];
  let useLongitude = true;

  for (const character of hash.toLowerCase()) {
    const value = BASE32.indexOf(character);
    if (value < 0) throw new TypeError(`Invalid geohash character: ${character}`);
    for (let mask = 16; mask > 0; mask >>= 1) {
      const range = useLongitude ? lngRange : latRange;
      const midpoint = (range[0] + range[1]) / 2;
      if (value & mask) range[0] = midpoint;
      else range[1] = midpoint;
      useLongitude = !useLongitude;
    }
  }

  return {
    lat: (latRange[0] + latRange[1]) / 2,
    lng: (lngRange[0] + lngRange[1]) / 2,
    bounds: {
      south: latRange[0],
      west: lngRange[0],
      north: latRange[1],
      east: lngRange[1]
    }
  };
}

export function privacyCell(location, precision = 5) {
  const point = normalizeLocation(location);
  const hash = geohashEncode(point.lat, point.lng, precision);
  const center = geohashDecode(hash);
  return { hash, lat: center.lat, lng: center.lng, bounds: center.bounds };
}
