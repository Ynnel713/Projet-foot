// Ticket v2-ecran-match/10b : tiroir domicile ouvert en un toucher à 844×390. Usage : node em10b-tiroir.cjs <dossier>
const { chromium } = require("playwright");
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 844, height: 390 }, deviceScaleFactor: 1, hasTouch: true });
  await p.goto("http://localhost:5173/v2?fixture=em10a&t=30&paused=1");
  await p.waitForSelector("svg[viewBox]", { timeout: 120000 });
  await p.waitForTimeout(1000);
  await p.tap("[data-zone=languette-home]");
  await p.waitForTimeout(400);
  const r = await p.evaluate(() => {
    const t = document.querySelector("[data-zone=tiroir-home]"), q = t.getBoundingClientRect();
    const tit = [...t.querySelectorAll("[data-card=titulaire]")].filter((c) => { const x = c.getBoundingClientRect(); return x.top >= q.top && x.bottom <= q.bottom && x.left >= 0; });
    return { gauche: Math.round(q.left), ouvert: t.getAttribute("aria-hidden") === "false", titulairesVisibles: tit.length, densite: t.querySelector("[data-density]").dataset.density };
  });
  console.log(JSON.stringify(r));
  await p.screenshot({ path: `${process.argv[2]}/em10b-844x390-tiroir-ouvert.png` });
  await b.close();
})();
