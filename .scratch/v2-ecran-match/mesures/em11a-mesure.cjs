// Ticket v2-ecran-match/11a. Usage : node em11a-mesure.cjs <dossier_captures> (Vite sur :5173, trace em11-om-ol :
// 2e période à 52', fin à 104'). Frise : largeur, hauteur, barres par rapport au curseur, repères, stabilité des barres.
const { chromium } = require("playwright");
const out = process.argv[2];
const CASES = [[1366, 768, 10], [1366, 768, 30], [1366, 768, 51.5], [1366, 768, 60], [1366, 768, 103.9], [1024, 768, 60], [1920, 1080, 60], [844, 390, 60]];
(async () => {
  const b = await chromium.launch();
  const res = {};
  for (const [w, h, t] of CASES) {
    const p = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
    await p.goto(`http://localhost:5173/v2?fixture=em11-om-ol&t=${t}&paused=1`);
    await p.waitForSelector("svg[viewBox]", { timeout: 120000 });
    await p.waitForTimeout(1500);
    res[`${w}x${h}@${t}`] = await p.evaluate(() => {
      const z = document.querySelector("[data-zone=momentum]");
      if (!z || !z.getBoundingClientRect().width) return { frise: "masquée" };
      const bas = document.querySelector("[data-zone=bas]");
      const cs = getComputedStyle(bas);
      const inner = bas.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
      const r = z.getBoundingClientRect();
      const bars = [...z.querySelectorAll("[data-bar]")].map((e) => ({ m: +e.dataset.bar, x: +e.getAttribute("x"), w: +e.getAttribute("width"), h: +e.getAttribute("height") }));
      const cursor = +z.querySelector("[data-cursor]").getAttribute("x1");
      const tick = Object.fromEntries([...z.querySelectorAll("[data-tick]")].map((e) => [e.dataset.tick, +(+e.getAttribute("x")).toFixed(1)]));
      const half = z.querySelector("[data-half-line]");
      return {
        frise: `${Math.round(r.width)}x${Math.round(r.height)}`, zoneInterieure: Math.round(inner),
        barres: bars.length, derniere: bars.at(-1)?.m, barreApresCurseur: bars.filter((b) => b.x >= cursor).length,
        barre5: bars.find((b) => b.m === 5), barre20: bars.find((b) => b.m === 20), curseur: +cursor.toFixed(1),
        mitemps: half ? +(+half.getAttribute("x1")).toFixed(1) : null, reperes: tick,
        pxParMinute: +(r.width / 105).toFixed(2),
        defilementBas: bas.scrollHeight - bas.clientHeight, page: document.documentElement.scrollHeight > innerHeight,
      };
    });
    await p.screenshot({ path: `${out}/em11a-${w}x${h}-t${t}.png` });
    await p.close();
  }
  console.log(JSON.stringify(res, null, 1));
  await b.close();
})();
