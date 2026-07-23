import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { qr } from './qr.mjs';

const root = path.dirname(new URL(import.meta.url).pathname);
const read = file => fs.readFileSync(path.join(root, file), 'utf8');
const player = read('player.html');
const index = read('index.html');

function section(source, start, end) {
  const from = source.indexOf(start);
  const to = source.indexOf(end, from);
  assert.notEqual(from, -1, `Missing section start: ${start}`);
  assert.notEqual(to, -1, `Missing section end: ${end}`);
  return source.slice(from, to);
}

function loadSection(source, start, end, exports, globals = {}) {
  const context = vm.createContext({
    TextEncoder,
    TextDecoder,
    URL,
    atob,
    btoa,
    escape,
    decodeURIComponent,
    structuredClone,
    ...globals
  });
  vm.runInContext(
    `${section(source, start, end)}\nglobalThis.__exports = { ${exports.join(',')} };`,
    context
  );
  return context.__exports;
}

const playerGateApi = loadSection(
  player,
  'function hasWellFormedUnicode',
  '\n\nasync function readBounded',
  ['validateCartridge', 'decodeUtf8Bytes'],
  { MAX_CART_BYTES: 2 * 1024 * 1024 }
);
const playerGate = playerGateApi.validateCartridge;
const decodeUtf8Bytes = playerGateApi.decodeUtf8Bytes;
const indexGate = loadSection(
  index,
  'function hasWellFormedUnicode',
  '\n\nfunction journalStatus',
  ['validateEgg'],
  { MAX_CART_BYTES: 2 * 1024 * 1024 }
).validateEgg;
const { canonicalJson } = loadSection(
  player,
  'function hasWellFormedUnicode',
  '\nasync function genomeId',
  ['canonicalJson']
);
const { b64enc, parseCartridgeFragment } = loadSection(
  player,
  'function b64enc',
  '\n\nfunction estimateGenomeFaces',
  ['b64enc', 'parseCartridgeFragment']
);
const { parseKeepFragment } = loadSection(
  index,
  'function parseEggText',
  '\n\nfunction hasWellFormedUnicode',
  ['parseKeepFragment'],
  { MAX_CART_BYTES: 2 * 1024 * 1024 }
);
const { validateRegistry } = loadSection(
  player,
  'function validateRegistry',
  '\n\nfunction getRegistry',
  ['validateRegistry'],
  { location: { href: 'https://example.test/player.html', origin: 'https://example.test' } }
);
const { enforceJournalRetention } = loadSection(
  index,
  'function cartridgeBytes',
  '\n\nasync function commitSpecimen',
  ['enforceJournalRetention'],
  {
    JOURNAL_RECENT_LIMIT: 8,
    JOURNAL_PINNED_LIMIT: 16,
    JOURNAL_BYTE_LIMIT: 24 * 1024 * 1024
  }
);
const { journalTransaction } = loadSection(
  index,
  'function journalTransaction',
  '\n\nfunction journalChanged',
  ['journalTransaction']
);
const { boundedCanvasSize } = loadSection(
  player,
  'function boundedCanvasSize',
  '\n\nfunction resizeCanvas',
  ['boundedCanvasSize']
);
const { handleProtocolMessage } = loadSection(
  player,
  'function handleProtocolMessage',
  '\n\nwindow.addEventListener',
  ['handleProtocolMessage'],
  {
    PROTOCOL_VERSION: 1,
    MOTION: { disposed: false },
    beginLoad() {},
    cancelScheduledFrame() {},
    handleIncomingCartridge() {},
    handlePrepareShare() {}
  }
);
const { readGenome } = loadSection(
  player,
  'function readGenome',
  '\nfunction buildCreatureFaces',
  ['readGenome'],
  {
    TAU: Math.PI * 2,
    clamp: (value, low, high) => Math.max(low, Math.min(high, value)),
    DEFAULT_PALETTE: ['#4488ff', '#2255cc']
  }
);
const { safeEggFilename, canNativeShareFile } = loadSection(
  player,
  'function safeEggFilename',
  "\n\ndocument.getElementById('btn-dl')",
  ['safeEggFilename', 'canNativeShareFile'],
  { navigator: { canShare() { throw new TypeError('unsupported'); } } }
);

let checks = 0;
const check = (name, fn) => {
  fn();
  checks++;
  process.stdout.write(`ok ${checks} - ${name}\n`);
};
const checkAsync = async (name, fn) => {
  await fn();
  checks++;
  process.stdout.write(`ok ${checks} - ${name}\n`);
};

const vectors = JSON.parse(read('canonical-vectors.json'));
check('canonical golden vectors', () => {
  for (const vector of vectors.vectors) {
    const canonical = canonicalJson(vector.value);
    const hash = crypto.createHash('sha256').update(canonical).digest('hex');
    assert.equal(canonical, vector.canonical, vector.name);
    assert.equal(hash, vector.sha256, vector.name);
  }
});

check('canonical rejection vectors', () => {
  for (const vector of vectors.rejections) {
    const value = vm.runInNewContext(vector.javascript);
    assert.throws(() => canonicalJson(value), undefined, vector.name);
  }
});

const eggFiles = fs.readdirSync(path.join(root, 'eggs')).filter(file => file.endsWith('.egg')).sort();
const eggs = eggFiles.map(file => [file, JSON.parse(read(path.join('eggs', file)))]);
check('both gates accept every bundled egg', () => {
  for (const [file, cart] of eggs) {
    assert.doesNotThrow(() => playerGate(structuredClone(cart)), `player: ${file}`);
    assert.doesNotThrow(() => indexGate(structuredClone(cart)), `index: ${file}`);
  }
});

check('phenotype atlas covers every renderer enum and multi-window composition', () => {
  const forms = new Set(), patterns = new Set(), symmetries = new Set();
  let hasMultiWindow = false;
  for (const [, cart] of eggs) {
    for (const layer of cart.genome.layers) {
      if (layer.role === 'form') {
        forms.add(layer.shape);
        symmetries.add(layer.symmetry);
      } else if (layer.role === 'surface') patterns.add(layer.pattern);
    }
    if ((cart.genome.compose && cart.genome.compose.windows || []).length > 1) hasMultiWindow = true;
  }
  assert.deepEqual([...forms].sort(), ['blob', 'ring', 'segment', 'star']);
  assert.deepEqual([...patterns].sort(), ['glow', 'solid', 'spot', 'stripe']);
  assert.deepEqual([...symmetries].sort(), ['bilateral', 'radial']);
  assert.equal(hasMultiWindow, true);
});

const invalidFixtures = [
  null,
  {},
  { schema: 'hologram-cartridge/1.0', genome: { layers: [{ role: 'unknown' }] } },
  { schema: 'hologram-cartridge/1.0', genome: { layers: [{ role: 'form' }, { role: 'surface' }], compose: true } },
  { schema: 'hologram-cartridge/1.0', genome: { layers: [{ role: 'form' }, { role: 'surface' }], compose: { windows: [[]], loop: true } } },
  { schema: 'hologram-cartridge/1.0', genome: { layers: [{ role: 'form' }, { role: 'surface', opacity: -1 }] } },
  { schema: 'hologram-cartridge/1.0', title: '\ud800', genome: { layers: [{ role: 'form' }, { role: 'surface' }] } },
  { schema: 'hologram-cartridge/1.0', title: 'x'.repeat(513), genome: { layers: [{ role: 'form' }, { role: 'surface' }] } },
  { schema: 'hologram-cartridge/1.0', extra: new Array(50001), genome: { layers: [{ role: 'form' }, { role: 'surface' }] } }
];
check('both gates reject the same malformed fixtures', () => {
  for (const fixture of invalidFixtures) {
    assert.throws(() => playerGate(structuredClone(fixture)));
    assert.throws(() => indexGate(structuredClone(fixture)));
  }
});

check('UTF-8 decoding is fatal on malformed byte sequences', () => {
  assert.equal(decodeUtf8Bytes(Uint8Array.from([0x7b, 0x7d])), '{}');
  assert.throws(() => decodeUtf8Bytes(Uint8Array.from([0xc3, 0x28])), /not valid UTF-8/);
});

check('render-cost budget rejects excessive windows', () => {
  const layers = [];
  const windows = [];
  for (let i = 0; i < 8; i++) {
    layers.push({ role: 'form', shape: 'star', segments: 24, limbs: 14, spikes: 14 });
    layers.push({ role: 'surface', palette: ['#ffffff'] });
    windows.push([i * 2, i * 2 + 1]);
  }
  const cart = { schema: 'hologram-cartridge/1.0', genome: { layers, compose: { windows, loop: true } } };
  assert.throws(() => playerGate(cart), /framing budget/);
});

check('render-cost budget admits under-budget ring windows', () => {
  const layers = [];
  const windows = [];
  for (let i = 0; i < 7; i++) {
    layers.push({ role: 'form', shape: 'ring', segments: 24, limbs: 14, spikes: 14 });
    layers.push({ role: 'surface', palette: ['#ffffff'] });
    windows.push([i * 2, i * 2 + 1]);
  }
  const cart = { schema: 'hologram-cartridge/1.0', genome: { layers, compose: { windows, loop: true } } };
  assert.doesNotThrow(() => playerGate(structuredClone(cart)));
  assert.doesNotThrow(() => indexGate(structuredClone(cart)));
});

check('render-cost budget ignores dormant non-looping windows', () => {
  const layers = [
    { role: 'form', shape: 'blob', segments: 4 },
    { role: 'surface', palette: ['#ffffff'] }
  ];
  const windows = [[0, 1]];
  for (let i = 0; i < 8; i++) {
    layers.push({ role: 'form', shape: 'star', segments: 24, limbs: 14, spikes: 14 });
    layers.push({ role: 'surface', palette: ['#ffffff'] });
    windows.push([2 + i * 2, 3 + i * 2]);
  }
  const cart = { schema: 'hologram-cartridge/1.0', genome: { layers, compose: { windows, loop: false } } };
  assert.doesNotThrow(() => playerGate(structuredClone(cart)));
  assert.doesNotThrow(() => indexGate(structuredClone(cart)));
});

check('canonical sparse windows remain accepted', () => {
  const cart = {
    schema: 'hologram-cartridge/1.0',
    genome: {
      layers: [
        { role: 'form', shape: 'blob', segments: 8 },
        { role: 'motion', pulse: 0.5 },
        { role: 'surface', palette: ['#ffffff'] }
      ],
      compose: { windows: [[0, 2]], loop: false }
    }
  };
  assert.doesNotThrow(() => playerGate(structuredClone(cart)));
  assert.doesNotThrow(() => indexGate(structuredClone(cart)));
  const inherited = readGenome({
    layers: [
      { role: 'form', shape: 'blob', segments: 8 },
      { role: 'surface', palette: ['#000000'], pattern: 'solid' },
      { role: 'motion', pulse: 0.5 },
      { role: 'surface', palette: ['#ffffff'], pattern: 'glow' }
    ],
    compose: { windows: [[0, 1, 2], [2, 3]], loop: true }
  }, 2);
  assert.equal(inherited.form.shape, 'blob');
  assert.equal(inherited.surface.pattern, 'glow');
});

const registry = JSON.parse(read('registry.json'));
check('registry structure, aliases, ids, and content hashes', () => {
  validateRegistry(structuredClone(registry));
  for (const entry of registry.entries) {
    const cart = JSON.parse(read(entry.pin_path));
    const hash = crypto.createHash('sha256').update(canonicalJson(cart)).digest('hex');
    const genomeId = crypto.createHash('sha256').update(canonicalJson(cart.genome)).digest('hex').slice(0, 12);
    assert.equal(hash, entry.content_sha256, entry.name);
    assert.equal(genomeId, entry.id, entry.name);
  }
  const collision = structuredClone(registry);
  collision.entries[1].name = collision.entries[0].id;
  assert.throws(() => validateRegistry(collision), /alias namespace/);
});

check('embedded defaults match the cataloged Lumina egg', () => {
  const indexDefault = JSON.parse(index.match(/const FALLBACK_CART = (\{.*\});/)[1]);
  const playerDefault = JSON.parse(player.match(/const DEFAULT_CART = (\{.*\});/)[1]);
  const lumina = JSON.parse(read('eggs/lumina.egg'));
  assert.equal(canonicalJson(indexDefault), canonicalJson(lumina));
  assert.equal(canonicalJson(playerDefault), canonicalJson(lumina));
});

check('base64url fragments are canonical and bounded', () => {
  const encoded = b64enc('{}');
  assert.equal(JSON.stringify(parseCartridgeFragment(encoded)), '{}');
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_';
  const index = alphabet.indexOf(encoded.at(-1));
  assert.throws(() => parseCartridgeFragment(encoded.slice(0, -1) + alphabet[index + 1]), /canonical/);
  assert.throws(
    () => parseCartridgeFragment('A'.repeat(Math.ceil((2 * 1024 * 1024) * 4 / 3) + 8)),
    /2 MiB/
  );
});

check('Journal handoff fragments round-trip exact cartridges', () => {
  const cart = eggs[0][1];
  const encoded = Buffer.from(JSON.stringify(cart), 'utf8').toString('base64url');
  assert.equal(JSON.stringify(parseKeepFragment(encoded)), JSON.stringify(cart));
  assert.throws(() => parseKeepFragment(encoded + 'A'));
});

check('QR version transitions and payload limit', () => {
  assert.equal((qr('x'.repeat(14)).size - 17) / 4, 1);
  assert.equal((qr('x'.repeat(180)).size - 17) / 4, 9);
  assert.equal((qr('x'.repeat(181)).size - 17) / 4, 10);
  assert.equal((qr('x'.repeat(997)).size - 17) / 4, 25);
  assert.throws(() => qr('x'.repeat(998)), /too long/);
});

check('canvas backing store always honors its pixel budget', () => {
  for (const [width, height, dpr] of [
    [480, 480, 2],
    [4000, 3000, 1],
    [100, 10000, 2],
    [7680, 4320, 2],
    [1, 10000, 3],
    [200000, 200000, 2],
    [1, 2000000, 2]
  ]) {
    const size = boundedCanvasSize(width, height, dpr);
    assert.ok(size.width * size.height <= 1600000, `${width}x${height}@${dpr}`);
    assert.ok(size.width <= 8192 && size.height <= 8192, `${width}x${height}@${dpr} dimension`);
    if (size.width > 1 && size.height > 1) {
      const aspectError = Math.abs((size.width / size.height) / (width / height) - 1);
      assert.ok(aspectError < 0.02, `${width}x${height}@${dpr} aspect`);
    }
  }
});

check('download filenames remain browser-safe and byte-bounded', () => {
  const filename = safeEggFilename('x'.repeat(400) + ': bad/name', 'abcdef0123456789');
  assert.ok(new TextEncoder().encode(filename).byteLength <= 140);
  assert.doesNotMatch(filename, /[<>:"/\\|?*\u0000-\u001f]/);
  assert.match(filename, /-abcdef01\.egg$/);
  assert.equal(canNativeShareFile({}), false);
});

check('protocol returns terminal errors for malformed payloads', () => {
  assert.match(player, /if \(window\.parent === window\) return;/);
  assert.match(player, /'forward-drop'/);
  for (const payload of [null, false, 0, '']) {
    const responses = [];
    handleProtocolMessage(payload, response => responses.push(response));
    assert.equal(responses.length, 1);
    assert.equal(responses[0].type, 'protocol-error');
  }
  const responses = [];
  handleProtocolMessage(
    { type: 'load-cartridge', version: 1, loadId: 'bad', cart: null },
    response => responses.push(response)
  );
  assert.equal(responses.length, 1);
  assert.equal(responses[0].type, 'error');
  assert.equal(responses[0].loadId, 'bad');
});

check('journal retention is pin-safe, byte-bounded, and count-bounded', () => {
  const records = [
    ...Array.from({ length: 2 }, (_, index) => ({
      contentId: `p${index}`, pinned: true, bytes: 100, lastOpenedAt: index
    })),
    ...Array.from({ length: 12 }, (_, index) => ({
      contentId: `r${index}`, pinned: false, bytes: 100, lastOpenedAt: index
    }))
  ];
  const deleted = new Set();
  const store = {
    getAll() {
      const request = { result: records };
      Object.defineProperty(request, 'onsuccess', { set: handler => handler() });
      return request;
    },
    delete(contentId) { deleted.add(contentId); }
  };
  const transaction = { aborted: false, abort() { this.aborted = true; } };
  enforceJournalRetention(store, transaction, 'r11');
  assert.equal(transaction.aborted, false);
  assert.equal(records.filter(record => !record.pinned && !deleted.has(record.contentId)).length, 8);
  assert.equal(records.filter(record => record.pinned && deleted.has(record.contentId)).length, 0);

  const pins = Array.from({ length: 17 }, (_, index) => ({
    contentId: `pin${index}`, pinned: true, bytes: 1, lastOpenedAt: index
  }));
  const pinStore = {
    getAll() {
      const request = { result: pins };
      Object.defineProperty(request, 'onsuccess', { set: handler => handler() });
      return request;
    },
    delete() {}
  };
  const pinTransaction = { aborted: false, abort() { this.aborted = true; } };
  enforceJournalRetention(pinStore, pinTransaction);
  assert.equal(pinTransaction.aborted, true);
  assert.match(pinTransaction.journalError.message, /16 pinned/);

  pins[0].pinned = false;
  const reducingTransaction = { aborted: false, abort() { this.aborted = true; } };
  enforceJournalRetention(pinStore, reducingTransaction, pins[0].contentId, { allowPolicyReduction: true });
  assert.equal(reducingTransaction.aborted, false);
});

await checkAsync('journal transactions preserve request-level quota errors until abort', async () => {
  const transaction = {};
  const quota = new DOMException('Quota exceeded', 'QuotaExceededError');
  const result = journalTransaction(transaction);
  let settled = false;
  result.catch(() => { settled = true; });
  transaction.onerror({ target: { error: quota } });
  await Promise.resolve();
  assert.equal(settled, false);
  transaction.onabort();
  await assert.rejects(result, error => error.name === 'QuotaExceededError');
});

process.stdout.write(`# ${checks} conformance groups passed\n`);
