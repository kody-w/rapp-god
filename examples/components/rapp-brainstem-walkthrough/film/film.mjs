// Film the RAPP Brainstem full-guide walkthrough (14 steps) from REAL surfaces:
// the live installer page, the rendered guide on GitHub, and the actual running
// brainstem at localhost:7071 — then produce the captioned walkthrough through
// RAPP Video's live Walkthrough Studio.
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(__dirname, 'out');
fs.mkdirSync(OUT, { recursive: true });

const GUIDE = 'https://github.com/kody-w/rapp-installer/blob/main/skill.md';
const INSTALLER = 'https://kody-w.github.io/rapp-installer/';
const RAPP_VIDEO = 'https://kody-w.github.io/rapp-video/';

// ---------- Act 1: record the real surfaces ----------
const browser = await chromium.launch({ channel: 'chromium', headless: true, args: ['--autoplay-policy=no-user-gesture-required'] });
const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 }, recordVideo: { dir: OUT, size: { width: 1280, height: 800 } } });
const page = await ctx.newPage();
const t0 = Date.now();
const marks = [];
const mark = (label) => { marks.push({ label, t: (Date.now() - t0) / 1000 }); console.log(`mark ${label} @ ${marks.at(-1).t.toFixed(1)}s`); };

const scrollToStep = async (n, dwell = 5000) => {
  const h = page.locator(`h3:has-text("Step ${n}:")`).first();
  await h.scrollIntoViewIfNeeded();
  await page.mouse.wheel(0, -120);            // breathing room above the heading
  await page.waitForTimeout(dwell);
};

// Intro: the public installer page
await page.goto(INSTALLER, { waitUntil: 'load' });
mark('intro');
await page.waitForTimeout(3500);

// Steps 1-2: the rendered guide on GitHub
await page.goto(GUIDE, { waitUntil: 'load' });
await page.waitForTimeout(1500);
mark('step1'); await scrollToStep(1, 5500);
mark('step2'); await scrollToStep(2, 5500);

// Step 3: the install one-liner on the public page
mark('step3');
await page.goto(INSTALLER, { waitUntil: 'load' });
await page.waitForTimeout(1200);
await page.mouse.wheel(0, 500);
await page.waitForTimeout(5000);

// Step 4: the REAL brainstem — live chat on camera
mark('step4');
await page.goto('http://localhost:7071/', { waitUntil: 'load' });
await page.waitForTimeout(2000);
const input = page.locator('#input');
await input.click();
await input.pressSequentially('Hello! What can you do?', { delay: 55 });
await page.waitForTimeout(400);
await page.click('#send');
await page.waitForTimeout(13000);            // the real answer arrives on camera

// Step 5: Tier 1 complete — real health endpoint
mark('step5');
await page.goto('http://localhost:7071/health', { waitUntil: 'load' });
await page.waitForTimeout(4500);

// Steps 6-7: guide sections
await page.goto(GUIDE, { waitUntil: 'load' });
await page.waitForTimeout(1200);
mark('step6'); await scrollToStep(6, 4500);
mark('step7'); await scrollToStep(7, 4500);

// Step 8: the real ARM template in the repo
mark('step8');
await page.goto('https://github.com/kody-w/rapp-installer/blob/main/azuredeploy.json', { waitUntil: 'load' });
await page.waitForTimeout(5000);

// Steps 9-11: guide sections
await page.goto(GUIDE, { waitUntil: 'load' });
await page.waitForTimeout(1200);
mark('step9'); await scrollToStep(9, 4500);
mark('step10'); await scrollToStep(10, 4500);
mark('step11'); await scrollToStep(11, 4500);

// Step 12: the Power Platform solution zip in the repo listing
mark('step12');
await page.goto('https://github.com/kody-w/rapp-installer', { waitUntil: 'load' });
await page.waitForTimeout(1500);
const zipRow = page.locator('text=MSFTAIBASMultiAgentCopilot').first();
await zipRow.scrollIntoViewIfNeeded({ timeout: 2500 }).catch(() => page.mouse.wheel(0, 400));
await page.waitForTimeout(4000);

// Steps 13-14: guide sections
await page.goto(GUIDE, { waitUntil: 'load' });
await page.waitForTimeout(1200);
mark('step13'); await scrollToStep(13, 4500);
mark('step14'); await scrollToStep(14, 6000);

// Outro: back to the installer page
mark('outro');
await page.goto(INSTALLER, { waitUntil: 'load' });
await page.waitForTimeout(2500);
mark('end');

await page.close();
const rawFile = fs.readdirSync(OUT).filter(f => f.endsWith('.webm') && f.length > 30)
  .map(f => path.join(OUT, f)).sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs)[0];
await ctx.close();
const RAW = path.join(OUT, 'raw-guide-session.webm');
fs.copyFileSync(rawFile, RAW); fs.unlinkSync(rawFile);
fs.writeFileSync(path.join(OUT, 'marks.json'), JSON.stringify(marks, null, 2));
console.log('raw:', RAW, fs.statSync(RAW).size, 'bytes;', marks.length, 'marks');

// ---------- Build the 14-step timeline from measured boundaries ----------
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

// ---------- Act 2: produce through the LIVE RAPP Video ----------
const page2 = await browser.newPage({ viewport: { width: 1440, height: 950 } });
page2.on('pageerror', e => console.error('pageerror:', e.message));
await page2.goto(RAPP_VIDEO, { waitUntil: 'load' });
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
