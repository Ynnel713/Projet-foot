// Usage : node mesure.cjs <dossier_captures> <étiquette>
const { chromium } = require("playwright");
const out = process.argv[2], tag = process.argv[3];
const SIZES = [[844, 390], [1024, 768], [1280, 720], [1366, 768], [1920, 1080]];
(async () => {
  const b = await chromium.launch();
  const res = {};
  for (const [w, h] of SIZES) {
    const p = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
    await p.goto("http://localhost:5173/v2?fixture=em04&t=30&paused=1");
    await p.waitForSelector("svg[viewBox]", { timeout: 60000 });
    await p.waitForTimeout(1500);
    const m = await p.evaluate(() => {
      const svgs = [...document.querySelectorAll("svg[viewBox]")];
      // terrain = le SVG qui porte le motif du filet (#v2-net) ; aire DESSINÉE (preserveAspectRatio « meet » : le contenu tient dans la boîte)
      const el = document.querySelector("#v2-net").ownerSVGElement; void svgs;
      const box = el.getBoundingClientRect(), vb = el.viewBox.baseVal, k = Math.min(box.width / vb.width, box.height / vb.height);
      const pitch = { width: vb.width * k, height: vb.height * k };
      const scrollers = [...document.querySelectorAll("*")].filter((e) => {
        const s = getComputedStyle(e);
        return /(auto|scroll)/.test(s.overflowY) && e.scrollHeight > e.clientHeight + 1 && e.clientHeight > 0;
      }).map((e) => (e.getAttribute("data-zone") || e.tagName.toLowerCase()) + ":" + (e.scrollHeight - e.clientHeight));
      const cols = [...document.querySelectorAll("[data-zone^=composition]")].map((e) => {
        const r = e.getBoundingClientRect();
        return `${e.getAttribute("data-zone")}:${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.left)}`;
      });
      return {
        pitch: [Math.round(pitch.width), Math.round(pitch.height)],
        aire: Math.round(pitch.width * pitch.height),
        header: !!document.querySelector("header"),
        docScroll: document.documentElement.scrollHeight > innerHeight || document.documentElement.scrollWidth > innerWidth,
        scrollers, cols,
      };
    });
    res[`${w}x${h}`] = m;
    await p.screenshot({ path: `${out}/${tag}-${w}x${h}.png` });
    await p.close();
  }
  const p = await b.newPage({ viewport: { width: 1366, height: 768 } });
  for (const r of ["/", "/v2"]) { await p.goto("http://localhost:5173" + r); await p.waitForTimeout(800); res["route " + r] = { header: !!(await p.$("header")) }; }
  console.log(JSON.stringify(res, null, 1));
  await b.close();
})();
