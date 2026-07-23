const fs = require("fs");
const H = require("../hologram.js");

let pass = 0, fail = 0;
const ok = (n, c, e) => { if (c) pass++; else { fail++; console.log("FAIL:", n, e || ""); } };

const legacy = {
  v: 1,
  t: "Legacy bloom",
  a: "@tester",
  b: "forest",
  k: [
    { at: 0, s: 0.2, l: 0.1, p: 0.0, g: 0.3, h: 300, x: 0, z: 0 },
    { at: 50, s: 0.6, l: 0.5, p: 0.9, g: 0.8, h: 330, x: 0.8, z: -0.4 },
    { at: 99, s: 0.4, l: 0.2, p: 0.3, g: 0.5, h: 180, x: -0.6, z: 0.5 }
  ]
};

const cart = H.legacyMomentToCartridgeSync(legacy);
const layers = cart.genome.layers;
const form = layers.find(l => l.role === "form");
const surface = layers.find(l => l.role === "surface");
const motion = layers.find(l => l.role === "motion");

ok("legacy converts to cartridge schema", cart.schema === "hologram-cartridge/1.0");
ok("id is 12-char content hash", /^[0-9a-f]{12}$/.test(cart.id), cart.id);
ok("title and author preserved", cart.title === legacy.t && cart.author === legacy.a);
ok("biome is preserved in born.from", cart.born && cart.born.from === legacy.b, JSON.stringify(cart.born));
ok("form maps body, limbs, limb_len, spikes", form && form.limbs === 4 && form.body_r >= 0 && form.body_r <= 1 && form.limb_len >= 0 && form.limb_len <= 1 && Number.isInteger(form.spikes) && form.spikes >= 0 && form.spikes <= 8, JSON.stringify(form));
ok("surface maps glow and 4-color palette", surface && surface.glow >= 0 && surface.glow <= 1 && Array.isArray(surface.palette) && surface.palette.length === 4 && surface.palette.every(c => /^#[0-9a-f]{6}$/i.test(c)), JSON.stringify(surface));
ok("motion derives breathe drift pulse", motion && ["breathe", "drift", "pulse"].every(k => motion[k] >= 0 && motion[k] <= 1), JSON.stringify(motion));
ok("hash is canonical genome hash", cart.id === H.sha256hexSync(H.canonical(cart.genome)).slice(0, 12), cart.id);

const file = JSON.parse(fs.readFileSync(require("path").join(__dirname, "..", "moments.json"), "utf8"));
ok("converted moments file contains cartridges", Array.isArray(file.moments) && file.moments.length > 0 && file.moments.every(H.isCartridge), file.moments && file.moments.length);
ok("converted moments have valid ids", file.moments.every(m => m.id === H.sha256hexSync(H.canonical(m.genome)).slice(0, 12)), "moments.json ids");
ok("converted moments all keep 4 limbs", file.moments.every(m => m.genome.layers.find(l => l.role === "form").limbs === 4));

console.log(`\nhologram: ${pass}/${pass + fail} passed` + (fail ? "  *** RED ***" : "  ALL GREEN"));
process.exit(fail ? 1 : 0);
