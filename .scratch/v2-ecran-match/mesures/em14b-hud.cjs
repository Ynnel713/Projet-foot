// Ticket v2-ecran-match/14b : effet du bouton Stats sur le HUD (largeur visible des noms de club, colonnes latérales,
// centrage du score). Usage : node em14b-hud.cjs <port> (Vite ; trace em11-om-ol à 45').
const { chromium } = require("playwright");
const port = process.argv[2];
(async () => {
  const b = await chromium.launch(); const res = {};
  for (const [w, h] of [[844, 390], [1024, 768], [1366, 768], [1920, 1080]]) {
    const p = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
    await p.goto(`http://localhost:${port}/v2?fixture=em11-om-ol&t=45&paused=1`);
    await p.waitForSelector("[data-zone=score]", { timeout: 120000 }); await p.waitForTimeout(800);
    res[`${w}x${h}`] = await p.evaluate(() => {
      const hud = document.querySelector("[data-zone=hud]");
      const cols = getComputedStyle(hud).gridTemplateColumns;
      const names = [...hud.querySelectorAll("[data-zone=score]")[0].parentElement.querySelectorAll("span[title]")].slice(0, 2)
        .map((n) => `${Math.round(n.clientWidth)}/${Math.round(n.scrollWidth)}`);
      const s = document.querySelector("[data-zone=score]").getBoundingClientRect(), t = document.querySelector("[data-zone=terrain] svg[viewBox]").getBoundingClientRect();
      return { colonnes: cols, noms_visible_sur_complet: names, ecart: +((s.left + s.width / 2) - (t.left + t.width / 2)).toFixed(1), hud: Math.round(hud.getBoundingClientRect().height), stats: !!document.querySelector("[data-zone=bouton-stats]") };
    });
    await p.close();
  }
  console.log(JSON.stringify(res)); await b.close();
})();
