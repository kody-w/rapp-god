import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium, firefox, webkit } from 'playwright';

const root = path.dirname(fileURLToPath(import.meta.url));
const mime = {
  '.egg': 'application/json',
  '.html': 'text/html; charset=utf-8',
  '.json': 'application/json',
  '.mjs': 'text/javascript; charset=utf-8'
};
const server = http.createServer((request, response) => {
  const pathname = decodeURIComponent(new URL(request.url, 'http://localhost').pathname);
  if (pathname === '/invalid-utf8.egg') {
    response.setHeader('content-type', 'application/json');
    response.end(Buffer.from([0xc3, 0x28]));
    return;
  }
  const relative = pathname === '/' ? 'index.html' : pathname.replace(/^\/+/, '');
  const filename = path.resolve(root, relative);
  if (!filename.startsWith(root + path.sep) || !fs.existsSync(filename) || fs.statSync(filename).isDirectory()) {
    response.writeHead(404).end('not found');
    return;
  }
  response.setHeader('content-type', mime[path.extname(filename)] || 'application/octet-stream');
  fs.createReadStream(filename).pipe(response);
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));

const engines = { chromium, firefox, webkit };
const engineName = process.env.BROWSER || 'chromium';
const engine = engines[engineName];
assert.ok(engine, `Unknown browser: ${engineName}`);
const browser = await engine.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 320, height: 568 }, hasTouch: true });
const errors = [];
page.on('pageerror', error => errors.push(error));
page.on('console', message => {
  if (message.type() === 'error') errors.push(new Error(message.text()));
});
page.on('requestfailed', request => errors.push(new Error(`request failed: ${request.url()}`)));
const base = `http://127.0.0.1:${server.address().port}`;

try {
  await page.goto(`${base}/index.html`);
  await page.locator('#title').filter({ hasText: 'Huila sky' }).waitFor();
  await page.locator('#share-dock:not([hidden])').waitFor();
  await page.locator('#share-copy:not([disabled])').waitFor();
  assert.equal(
    await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
    true
  );
  await page.locator('#url').fill(`${base}/invalid-utf8.egg`);
  await page.locator('#loadurl').click();
  await page.locator('#status').filter({ hasText: 'not valid UTF-8' }).waitFor();
  assert.equal(await page.locator('#title').textContent(), 'Huila sky');
  await page.locator('#unload').click();
  await page.locator('#drop').waitFor();

  await page.goto(`${base}/player.html#`);
  await page.locator('#i-title').filter({ hasText: 'Could not verify this egg' }).waitFor();
  await assert.rejects(
    page.locator('#btn-link').click({ timeout: 500 }),
    /disabled|Timeout/
  );

  await page.setViewportSize({ width: 120, height: 120 });
  await page.goto(`${base}/player.html?embed=1#`);
  await page.locator('#embed-error:not([hidden])').waitFor();
  assert.equal(await page.locator('#view-controls').isVisible(), false);
  assert.equal(
    await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth),
    true
  );

  const registry = JSON.parse(fs.readFileSync(path.join(root, 'registry.json'), 'utf8'));
  const moon = registry.entries.find(entry => entry.name === 'moon');
  await page.setViewportSize({ width: 320, height: 568 });
  await page.goto(`${base}/player.html?id=moon&h=${moon.content_sha256}`);
  await page.locator('#i-title').filter({ hasText: "Tonight's Moon" }).waitFor();
  assert.equal(await page.locator('#btn-dl').isEnabled(), true);
  const overlap = await page.evaluate(() => {
    const controls = document.querySelector('#view-controls').getBoundingClientRect();
    const verify = document.querySelector('#verify').getBoundingClientRect();
    return !(controls.right <= verify.left || controls.left >= verify.right ||
      controls.bottom <= verify.top || controls.top >= verify.bottom);
  });
  assert.equal(overlap, false);

  await page.setViewportSize({ width: 800, height: 600 });
  const mismatch = JSON.parse(fs.readFileSync(path.join(root, moon.pin_path), 'utf8'));
  mismatch.id = '000000000000';
  const fragment = Buffer.from(JSON.stringify(mismatch), 'utf8').toString('base64url');
  await page.goto(`${base}/player.html#${fragment}`);
  await page.locator('#verify.mismatch').waitFor();
  const mismatchOverlap = await page.evaluate(() => {
    const controls = document.querySelector('#view-controls').getBoundingClientRect();
    const verify = document.querySelector('#verify').getBoundingClientRect();
    return !(controls.right <= verify.left || controls.left >= verify.right ||
      controls.bottom <= verify.top || controls.top >= verify.bottom);
  });
  assert.equal(mismatchOverlap, false);
  assert.deepEqual(errors, []);
  process.stdout.write(`browser smoke passed: ${engineName}\n`);
} finally {
  await browser.close();
  await new Promise(resolve => server.close(resolve));
}
