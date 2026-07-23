// Act 2 only: rebuild the timeline from saved marks and re-render through the
// live RAPP Video — no re-shoot. Keep in sync with film.mjs's timeline block.
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(__dirname, 'out');
const RAW = path.join(OUT, 'raw-guide-session.webm');
const marks = JSON.parse(fs.readFileSync(path.join(OUT, 'marks.json')));

const CAPTIONS = {
  step1: 'Check the environment — Python 3.11, Git, and the GitHub CLI',
  step2: 'Authenticate GitHub — your Copilot seat is the AI engine, no API keys',
  step3: 'Install the brainstem — one clone, one pip install, one CLI wrapper',
  step4: 'Start and verify — the brainstem answers live on localhost:7071',
  step5: 'Tier 1 complete — /health shows your local agent server alive',
  step6: 'Tier 2 begins — check the Azure prerequisites (az, func)',
  step7: 'Authenticate Azure — give your brainstem a cloud body',
  step8: 'Deploy Azure resources — one ARM template, unique names',
  step9: 'Assign RBAC roles — storage access, done right',
  step10: 'Deploy the function — the same brainstem, now always-on',
  step11: 'Tier 2 complete — the cloud state is saved',
  step12: 'Tier 3 — import the Power Platform solution into Copilot Studio',
  step13: 'Configure the connector to point at your Azure Function',
  step14: 'Publish — your agent goes live in Teams and M365 Copilot',
};
const ZOOMS = { step3: { zoom: 1.4, cx: 0.5, cy: 0.55 }, step4: { zoom: 1.25, cx: 0.5, cy: 0.55 } };
const at = (label) => marks.find(m => m.label === label).t;
const timeline = [{ title: 'RAPP Brainstem — the full guide in 14 steps', dur: 2.6 }];
const order = Object.keys(CAPTIONS);
for (let i = 0; i < order.length; i++) {
  const label = order[i];
  const next = i + 1 < order.length ? order[i + 1] : 'outro';
  const seg = { srcIn: Math.max(0, at(label) - 0.1), srcOut: at(next) - 0.1, caption: CAPTIONS[label] };
  if (ZOOMS[label]) seg.camera = ZOOMS[label];
  timeline.push(seg);
}
timeline.push({ title: 'Start at Tier 1 — kody-w.github.io/rapp-installer', dur: 2.8 });
timeline.push({ title: 'No API keys. No lock-in. Produced with RAPP Video.', dur: 2.6 });
fs.writeFileSync(path.join(OUT, 'timeline.json'), JSON.stringify(timeline, null, 2));
console.log('timeline segments:', timeline.length);

const browser = await chromium.launch({ channel: 'chromium', headless: true, args: ['--autoplay-policy=no-user-gesture-required'] });
const page2 = await browser.newPage({ viewport: { width: 1440, height: 950 } });
page2.on('pageerror', e => console.error('pageerror:', e.message));
await page2.goto('https://kody-w.github.io/rapp-video/', { waitUntil: 'load' });
await page2.waitForFunction(() => window.RAPP_VIDEO && window.RAPP_VIDEO.state === 'idle');
await page2.click('[data-tab="walkthrough"]');
await page2.setInputFiles('#wt-video-input', RAW);
await page2.waitForTimeout(2500);
await page2.evaluate((tl) => {
  const ta = document.getElementById('wt-timeline');
  ta.value = JSON.stringify(tl, null, 2);
  ta.dispatchEvent(new Event('input', { bubbles: true }));
}, timeline);
await page2.waitForTimeout(600);
await page2.click('#wt-render-btn');
await page2.waitForFunction(() => window.RAPP_VIDEO.state === 'rendering' || window.RAPP_VIDEO.state === 'error', null, { timeout: 20000, polling: 200 });
await page2.waitForFunction(() => window.RAPP_VIDEO.state === 'done' || window.RAPP_VIDEO.state === 'error', null, { timeout: 600000, polling: 1000 });
const state = await page2.evaluate(() => ({ s: window.RAPP_VIDEO.state, b: window.RAPP_VIDEO.lastBlob }));
console.log('render:', JSON.stringify(state));
if (state.s === 'done') {
  const g = await page2.evaluate(async () => {
    const blob = await fetch(document.getElementById('wt-result-video').src).then(r => r.blob());
    const buf = await blob.arrayBuffer(); const bytes = new Uint8Array(buf);
    let s = ''; for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
    return { b64: btoa(s), type: blob.type };
  });
  const outFile = path.join(OUT, 'brainstem-guide-walkthrough' + (/mp4/.test(g.type) ? '.mp4' : '.webm'));
  fs.writeFileSync(outFile, Buffer.from(g.b64, 'base64'));
  console.log('PRODUCED:', outFile, fs.statSync(outFile).size, 'bytes', g.type);
}
await browser.close();
process.exit(state.s === 'done' ? 0 : 1);
