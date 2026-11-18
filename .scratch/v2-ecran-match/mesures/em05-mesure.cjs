// EM-05 : usage node mesure.cjs <dossier> <étiquette>. Trace réelle em04, minute 30, en pause.
const { chromium } = require("playwright");
const out = process.argv[2], tag = process.argv[3];
const SIZES = [[844, 390], [1024, 768], [1280, 720], [1366, 768], [1920, 1080]];
(async () => {
  const b = await chromium.launch();
  const res = {};
  for (const [w, h] of SIZES) {
    const p = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
    await p.goto("http://localhost:5173/v2?fixture=em04&t=30&paused=1");
    await p.waitForSelector("#v2-net", { state: "attached", timeout: 60000 });
    await p.waitForTimeout(1500);
    res[`${w}x${h}`] = await p.evaluate(() => {
      const svg = document.querySelector("#v2-net").ownerSVGElement;
      const ctm = svg.getScreenCTM();
      const L = 105, W = 68, COS = Math.cos((35 * Math.PI) / 180);
      const scr = (x, y) => { const q = new DOMPoint(x, y * COS).matrixTransform(ctm); return [q.x, q.y]; };
      // marquages : rectangle des lignes de touche/de but, point central, points de penalty (cercles blancs)
      const rects = [...svg.querySelectorAll("rect")].filter((r) => +r.getAttribute("width") === L && +r.getAttribute("height") === W && r.getAttribute("x") === "0");
      const box = rects[0].getBoundingClientRect();
      const spots = [...svg.querySelectorAll("circle")].filter((c) => c.getAttribute("fill") === "white" && +c.getAttribute("r") < 0.5)
        .map((c) => { const r = c.getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; });
      const sw = getComputedStyle(rects[0]);
      const k = ctm.a; // px par mètre
      const ve = rects[0].getAttribute("vector-effect");
      const linePx = ve === "non-scaling-stroke" ? parseFloat(rects[0].getAttribute("stroke-width")) : parseFloat(rects[0].getAttribute("stroke-width")) * k;
      const expect = { coinHG: scr(0, 0), coinBD: scr(L, W), centre: scr(L / 2, W / 2), penG: scr(11, W / 2), penD: scr(L - 11, W / 2) };
      const got = { coinHG: [box.left, box.top], coinBD: [box.right, box.bottom] };
      const near = (pt) => spots.map((s) => Math.hypot(s[0] - pt[0], s[1] - pt[1])).sort((a, b2) => a - b2)[0];
      // getBoundingClientRect d'un élément SVG : géométrie seule, sans l'épaisseur du trait
      const half = 0;
      const ecarts = {
        coinHG: Math.hypot(got.coinHG[0] + half - expect.coinHG[0], got.coinHG[1] + half - expect.coinHG[1]),
        coinBD: Math.hypot(got.coinBD[0] - half - expect.coinBD[0], got.coinBD[1] - half - expect.coinBD[1]),
        centre: near(expect.centre), penG: near(expect.penG), penD: near(expect.penD),
      };
      const rouge = [...svg.querySelectorAll("[fill]")].some((e) => /9c4a3c/i.test(e.getAttribute("fill")));
      return {
        jeu: [Math.round(box.width), Math.round(box.height)], aireJeu: Math.round(box.width * box.height),
        pxParMetre: +k.toFixed(2), traitPx: +linePx.toFixed(2),
        ecartsPx: Object.fromEntries(Object.entries(ecarts).map(([n, v]) => [n, +v.toFixed(2)])),
        rouge, defilement: document.documentElement.scrollHeight > innerHeight || document.documentElement.scrollWidth > innerWidth,
      };
    });
    await p.screenshot({ path: `${out}/${tag}-${w}x${h}.png` });
    await p.close();
  }
  console.log(JSON.stringify(res, null, 1));
  await b.close();
})();
