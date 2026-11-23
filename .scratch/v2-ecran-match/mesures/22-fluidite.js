// Mesure de fluidité du ticket v2-hauteur-ballon/02b : même trace, même vitesse (×1), processeur ralenti 6 fois,
// Chromium sans affichage, 30 s de lecture ; fichiers de chaque version servis depuis son dossier de build, API simulée.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const [dist, fixture, seconds = '30', throttle = '6'] = process.argv.slice(2);
const data = JSON.parse(fs.readFileSync(fixture, 'utf8'));
const { lineups, ...trace } = data;
const types = { '.js': 'application/javascript', '.css': 'text/css', '.html': 'text/html', '.svg': 'image/svg+xml',
  '.png': 'image/png', '.json': 'application/json', '.webmanifest': 'application/manifest+json', '.woff2': 'font/woff2' };
(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 }, serviceWorkers: 'block' });
  await context.route('**/*', async (route) => {
    const url = new URL(route.request().url());
    const p = url.pathname;
    const json = (body) => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
    if (p === '/api/clubs') return json([{ name: trace.home }, { name: trace.away }]);
    if (p === '/api/v2/lineup') return json(url.searchParams.get('club') === trace.home ? lineups.home : lineups.away);
    if (p === '/api/v2/matches/start') return json({ id: 'mesure' });
    if (p.startsWith('/api/v2/matches/')) {
      const t = Number(url.searchParams.get('from_tick') || 0);
      const b = Number(url.searchParams.get('from_ball') || 0);
      const e = Number(url.searchParams.get('from_event') || 0);
      return json({ ...trace, done: true, error: null, first_tick: t, ticks: trace.ticks.slice(t),
        ball_track: (trace.ball_track || []).slice(b), events: (trace.events || []).slice(e) });
    }
    if (p.startsWith('/api/')) return json([]);
    let file = path.join(dist, p);
    if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) file = path.join(dist, 'index.html');
    return route.fulfill({ status: 200, contentType: types[path.extname(file)] || 'application/octet-stream', body: fs.readFileSync(file) });
  });
  const page = await context.newPage();
  await page.goto('http://mesure.local/v2', { timeout: 120000 });
  await page.getByRole('button', { name: /Lancer le match/ }).click();
  await page.waitForFunction(() => document.querySelectorAll('svg circle').length > 40, null, { timeout: 120000 });
  await page.waitForTimeout(3000);
  const cdp = await context.newCDPSession(page);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: Number(throttle) });
  await cdp.send('Performance.enable');
  const metric = async () => Object.fromEntries((await cdp.send('Performance.getMetrics')).metrics.map((m) => [m.name, m.value]));
  const m0 = await metric();
  const snap = () => page.evaluate(() => [...document.querySelectorAll('svg circle')].slice(0, 400).map((c) => `${c.getAttribute('cx')},${c.getAttribute('cy')}`).join('|'));
  const before = await snap();
  const frames = await page.evaluate((ms) => new Promise((resolve) => {
    let n = 0; const t0 = performance.now(); const gaps = []; let last = t0;
    const tick = (now) => { n += 1; gaps.push(now - last); last = now; if (now - t0 < ms) requestAnimationFrame(tick); else resolve({ n, ms: now - t0, gaps }); };
    requestAnimationFrame(tick);
  }), Number(seconds) * 1000);
  const fps = frames.n / (frames.ms / 1000);
  const sorted = frames.gaps.slice(1).sort((a, b) => a - b);
  const p95 = sorted[Math.floor(0.95 * sorted.length)];
  const after = await snap();
  const m1 = await metric();
  const d = (k) => +(((m1[k] - m0[k]) / frames.n) * 1000).toFixed(2);
  const split = { task: d('TaskDuration'), script: d('ScriptDuration'), layout: d('LayoutDuration'), style: d('RecalcStyleDuration') };
  const clock = before === after ? 'IMMOBILE' : 'en lecture';
  console.log(JSON.stringify({ dist: path.basename(dist), fps: +fps.toFixed(2), frames: frames.n, p95_ms: +p95.toFixed(1), clock, ms_par_image: split }));
  await browser.close();
})();
