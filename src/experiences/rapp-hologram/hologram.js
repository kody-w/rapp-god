(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory(require("crypto"));
  else root.HologramBridge = factory(null);
})(typeof self !== "undefined" ? self : this, function (nodeCrypto) {
  "use strict";

  function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }
  function lerp(a, b, t) { return a + (b - a) * t; }
  function hueWrap(h) { return ((+h % 360) + 360) % 360; }
  function hueDist(a, b) {
    var d = Math.abs(hueWrap(a) - hueWrap(b));
    return Math.min(d, 360 - d);
  }
  function canonical(v) {
    if (Array.isArray(v)) return "[" + v.map(canonical).join(",") + "]";
    if (v && typeof v === "object") return "{" + Object.keys(v).sort().map(function (k) { return JSON.stringify(k) + ":" + canonical(v[k]); }).join(",") + "}";
    return JSON.stringify(v);
  }
  function sha256hexSync(str) {
    if (!nodeCrypto) throw new Error("sync SHA-256 unavailable");
    return nodeCrypto.createHash("sha256").update(str).digest("hex");
  }
  async function sha256hex(str) {
    if (typeof crypto !== "undefined" && crypto.subtle) {
      var buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(str));
      return Array.from(new Uint8Array(buf)).map(function (b) { return b.toString(16).padStart(2, "0"); }).join("");
    }
    return sha256hexSync(str);
  }
  function hslToHex(h, s, l) {
    h = hueWrap(h) / 360; s = clamp(s, 0, 1); l = clamp(l, 0, 1);
    var r, g, b;
    if (s === 0) r = g = b = l;
    else {
      var hue2rgb = function (p, q, t) {
        if (t < 0) t += 1;
        if (t > 1) t -= 1;
        if (t < 1 / 6) return p + (q - p) * 6 * t;
        if (t < 1 / 2) return q;
        if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
        return p;
      };
      var q = l < 0.5 ? l * (1 + s) : l + s - l * s;
      var p = 2 * l - q;
      r = hue2rgb(p, q, h + 1 / 3);
      g = hue2rgb(p, q, h);
      b = hue2rgb(p, q, h - 1 / 3);
    }
    return "#" + [r, g, b].map(function (v) { return Math.round(v * 255).toString(16).padStart(2, "0"); }).join("");
  }
  function paletteFromHue(h) {
    h = hueWrap(h);
    return [
      hslToHex(h, 0.88, 0.42),
      hslToHex(h + 18, 0.92, 0.54),
      hslToHex(h + 42, 0.76, 0.70),
      hslToHex(h - 24, 0.66, 0.28)
    ];
  }
  function clampF(f) {
    return { at: f.at | 0, s: +f.s || 0, l: +f.l || 0, p: +f.p || 0, g: +f.g || 0, h: +f.h || 0, x: +f.x || 0, z: +f.z || 0 };
  }
  function lerpF(a, b, t) {
    var ah = hueWrap(a.h), bh = hueWrap(b.h), hd = ((bh - ah + 540) % 360) - 180;
    return {
      s: lerp(a.s, b.s, t),
      l: lerp(a.l, b.l, t),
      p: lerp(a.p, b.p, t),
      g: lerp(a.g, b.g, t),
      h: hueWrap(ah + hd * t),
      x: lerp(a.x, b.x, t),
      z: lerp(a.z, b.z, t)
    };
  }
  function expandLegacy(moment) {
    var k = ((moment && moment.k) || []).map(clampF).sort(function (a, b) { return a.at - b.at; });
    if (!k.length) k = [{ at: 0, s: 0.35, l: 0.4, p: 0, g: 0.45, h: 140, x: 0, z: 0 }];
    if (k.length === 1) k = [Object.assign({}, k[0], { at: 0 }), Object.assign({}, k[0], { at: 99 })];
    var out = [];
    for (var i = 0; i < 100; i++) {
      var lo = k[0], hi = k[k.length - 1];
      for (var j = 0; j < k.length; j++) {
        if (k[j].at <= i) lo = k[j];
        if (k[j].at >= i) { hi = k[j]; break; }
      }
      out.push(lerpF(lo, hi, hi.at === lo.at ? 0 : (i - lo.at) / (hi.at - lo.at)));
    }
    return out;
  }
  function summarizeFrames(frames) {
    var sum = { s: 0, l: 0, p: 0, g: 0, x: 0, z: 0 }, sinH = 0, cosH = 0;
    var minX = Infinity, maxX = -Infinity, minZ = Infinity, maxZ = -Infinity;
    var totalStep = 0, maxStep = 0, path = 0;
    for (var i = 0; i < frames.length; i++) {
      var f = frames[i];
      sum.s += f.s; sum.l += f.l; sum.p += f.p; sum.g += f.g; sum.x += f.x; sum.z += f.z;
      var hr = hueWrap(f.h) * Math.PI / 180;
      sinH += Math.sin(hr); cosH += Math.cos(hr);
      minX = Math.min(minX, f.x); maxX = Math.max(maxX, f.x);
      minZ = Math.min(minZ, f.z); maxZ = Math.max(maxZ, f.z);
      if (i > 0) {
        var prev = frames[i - 1];
        var dx = f.x - prev.x, dz = f.z - prev.z;
        var step = (
          Math.abs(f.s - prev.s) +
          Math.abs(f.l - prev.l) +
          Math.abs(f.p - prev.p) +
          Math.abs(f.g - prev.g) +
          (hueDist(f.h, prev.h) / 180) +
          Math.abs(dx) +
          Math.abs(dz)
        ) / 7;
        totalStep += step;
        maxStep = Math.max(maxStep, step);
        path += Math.hypot(dx, dz);
      }
    }
    var n = Math.max(frames.length, 1);
    var rangeX = isFinite(minX) ? maxX - minX : 0;
    var rangeZ = isFinite(minZ) ? maxZ - minZ : 0;
    var avgStep = totalStep / Math.max(1, frames.length - 1);
    var travel = path / Math.max(1, frames.length - 1);
    return {
      body_r: clamp(sum.s / n, 0, 1),
      limb_len: clamp(sum.l / n, 0, 1),
      spikes: clamp(Math.round((sum.p / n) * 8), 0, 8),
      glow: clamp(sum.g / n, 0, 1),
      hue: hueWrap(Math.atan2(sinH / n, cosH / n) * 180 / Math.PI),
      drift: clamp(Math.hypot(rangeX, rangeZ) * 0.55 + travel * 2.1, 0, 1),
      breathe: clamp(avgStep * 3.4 + Math.abs(frames[n - 1].s - frames[0].s) * 0.7, 0, 1),
      pulse: clamp(maxStep * 4.2 + Math.abs(frames[n - 1].g - frames[0].g) * 0.9, 0, 1)
    };
  }
  function legacyGenome(moment) {
    var frames = expandLegacy(moment);
    var s = summarizeFrames(frames);
    return {
      layers: [
        {
          role: "form",
          k: 30,
          shape: "blob",
          limbs: 4,
          segments: 8,
          symmetry: "bilateral",
          body_r: +s.body_r.toFixed(4),
          limb_len: +s.limb_len.toFixed(4),
          spikes: s.spikes
        },
        {
          role: "surface",
          k: 85,
          palette: paletteFromHue(s.hue),
          pattern: "glow",
          glow: +s.glow.toFixed(4),
          opacity: 0.9
        },
        {
          role: "motion",
          k: 60,
          breathe: +s.breathe.toFixed(4),
          drift: +s.drift.toFixed(4),
          pulse: +s.pulse.toFixed(4),
          reach: +clamp((s.drift + s.pulse) / 2, 0, 1).toFixed(4)
        }
      ],
      compose: { windows: [[0, 1, 2]], loop: true }
    };
  }
  function legacyMomentToCartridgeBase(moment) {
    var title = (moment && (moment.title || moment.t)) || "untitled";
    var author = (moment && (moment.author || moment.a)) || "@anon";
    var biome = (moment && moment.b) || "legacy";
    var coord = (moment && moment.pk) || "legacy";
    return {
      schema: "hologram-cartridge/1.0",
      id: "",
      title: title,
      author: author,
      born: { coord: coord, from: biome },
      parents: [],
      genome: legacyGenome(moment || {}),
      sig: ""
    };
  }
  function finalizeCartSync(cart) {
    var out = JSON.parse(JSON.stringify(cart));
    out.id = sha256hexSync(canonical(out.genome)).slice(0, 12);
    return out;
  }
  async function finalizeCart(cart) {
    var out = JSON.parse(JSON.stringify(cart));
    out.id = (await sha256hex(canonical(out.genome))).slice(0, 12);
    return out;
  }
  function isLegacyMoment(v) { return !!(v && Array.isArray(v.k)); }
  function isCartridge(v) { return !!(v && v.schema === "hologram-cartridge/1.0" && v.genome); }
  function normalizePlayableSync(v) {
    if (isCartridge(v)) return v.id || !nodeCrypto ? v : finalizeCartSync(v);
    if (isLegacyMoment(v)) return nodeCrypto ? finalizeCartSync(legacyMomentToCartridgeBase(v)) : legacyMomentToCartridgeBase(v);
    throw new Error("unsupported playable");
  }
  async function normalizePlayable(v) {
    if (isCartridge(v)) return v.id ? v : finalizeCart(v);
    if (isLegacyMoment(v)) return finalizeCart(legacyMomentToCartridgeBase(v));
    throw new Error("unsupported playable");
  }

  return {
    canonical: canonical,
    sha256hex: sha256hex,
    sha256hexSync: sha256hexSync,
    paletteFromHue: paletteFromHue,
    expandLegacy: expandLegacy,
    legacyGenome: legacyGenome,
    legacyMomentToCartridge: function (moment) { return finalizeCart(legacyMomentToCartridgeBase(moment)); },
    legacyMomentToCartridgeSync: function (moment) { return finalizeCartSync(legacyMomentToCartridgeBase(moment)); },
    normalizePlayable: normalizePlayable,
    normalizePlayableSync: normalizePlayableSync,
    isLegacyMoment: isLegacyMoment,
    isCartridge: isCartridge
  };
});
