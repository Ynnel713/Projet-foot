const { chromium } = require('playwright');
const out = process.argv[2];
const shots = JSON.parse(process.argv[3]);
(async () => {
  const browser = await chromium.launch();
  for (const s of shots) {
    const page = await browser.newPage({ viewport: { width: s.w, height: s.h }, deviceScaleFactor: 2 });
    await page.goto(`http://localhost:5173/v2?fixture=hauteur02b&t=${s.t}&paused=1`, { timeout: 120000 });
    await page.waitForSelector('[data-ball]', { timeout: 120000 });
    await page.waitForTimeout(1500);
    const info = await page.evaluate(() => {
      const b = document.querySelector('[data-ball]'); const sh = document.querySelector('[data-ball-shadow]');
      return { ball: b && { cx: b.getAttribute('cx'), cy: b.getAttribute('cy'), r: b.getAttribute('r') },
               shadow: sh && { cx: sh.getAttribute('cx'), cy: sh.getAttribute('cy'), rx: sh.getAttribute('rx'), op: sh.getAttribute('opacity') } };
    });
    console.log(s.name, JSON.stringify(info));
    await page.screenshot({ path: `${out}/${s.name}.png` });
    await page.close();
  }
  await browser.close();
})();
