// Ticket v2-ecran-match/13b. Usage : node em13b-mesure.cjs <dossier_captures> (Vite sur :5173, trace em11-om-ol).
// HUD : hauteur, centre du score − centre du terrain ; pendant un ralenti : badge d'état, pastille des commandes.
const { chromium } = require("playwright");
const out = process.argv[2];
(async () => {
  const b = await chromium.launch(); const res = {};
  const hud = () => {
    const box = (e) => e.getBoundingClientRect();
    const s = box(document.querySelector("[data-zone=score]")), p = box(document.querySelector("[data-zone=terrain] svg[viewBox]"));
    return { hud: Math.round(box(document.querySelector("[data-zone=hud]")).height), ecart: +((s.left + s.width / 2) - (p.left + p.width / 2)).toFixed(1),
      badge: document.querySelector("[data-zone=etat]").innerText,
      pastilleCommandes: [...document.querySelectorAll("[data-zone=hud] span")].filter((x) => x.innerText === "RALENTI" && !x.matches("[data-zone=etat]")).length,
      passer: !!document.querySelector('[aria-label="Passer le ralenti"]') };
  };
  for (const [w, h, t] of [[1366, 768, 1], [1366, 768, 104], [1024, 768, 104], [1920, 1080, 104], [844, 390, 104]]) {
    const p = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
    await p.goto(`http://localhost:5173/v2?fixture=em11-om-ol&t=${t}&paused=1`);
    await p.waitForSelector("[data-zone=score]", { timeout: 120000 }); await p.waitForTimeout(1000);
    res[`${w}x${h}@${t}`] = await p.evaluate(hud); await p.close();
  }
  const p = await b.newPage({ viewport: { width: 1366, height: 768 }, deviceScaleFactor: 1 });
  await p.goto("http://localhost:5173/v2?fixture=em11-om-ol&t=1.98&speed=1");
  await p.waitForFunction(() => document.querySelector("[data-zone=etat]")?.innerText === "RALENTI", null, { timeout: 120000, polling: 50 });
  await p.waitForTimeout(500);
  res["ralenti 1366x768"] = await p.evaluate(hud);
  await p.screenshot({ path: `${out}/em13b-ralenti-1366.png`, clip: { x: 0, y: 0, width: 1366, height: 110 } });
  console.log(JSON.stringify(res, null, 1)); await b.close();
})();
