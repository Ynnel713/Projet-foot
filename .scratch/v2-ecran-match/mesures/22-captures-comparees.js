const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  for (const [w, h] of [[1280, 800], [375, 812]]) for (const t of ['4.632', '4.6483', '6.5055']) for (const port of [5174, 5173]) {
    const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
    await page.goto(`http://localhost:${port}/v2?fixture=hauteur02b&t=${t}&paused=1`, { timeout: 120000 });
    await page.waitForSelector('[data-ball]', { timeout: 120000 });
    await page.waitForTimeout(1500);
    const svg = await page.evaluate(() => { const r = document.querySelector('[data-ball]').ownerSVGElement.getBoundingClientRect(); return `${r.x},${r.y},${r.width},${r.height}`; });
    const name = `${port === 5174 ? 'avant' : 'apres'}-${w}-${t}`;
    await page.screenshot({ path: `${process.argv[2]}/${name}.png` });
    console.log(name, svg);
    await page.close();
  }
  await browser.close();
})();
