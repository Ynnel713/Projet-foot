// EM-21b, critère C3 : recul du milieu du fond du filet (point arrière du toit, polygone à 5 sommets) lu dans le DOM,
// pour les deux filets, juste après un but de chaque période, puis 2,5 s après (retour au repos) ; captures du filet.
// Trace em04 : but domicile à 4,39 (1re période : filet de droite, x = 105) ; but domicile à 75,69 (2e période, scène
// retournée : filet de gauche, x = 0). node em21b-dom.cjs <dossier>
const { chromium } = require("playwright");
const out = process.argv[2];
const CASES = [
  { nom: "but-1re-periode", goal: 4.39, side: "droite" },
  { nom: "but-2e-periode", goal: 75.69, side: "gauche" },
];
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1366, height: 768 }, deviceScaleFactor: 2 });
  const read = async (t) => {
    await p.goto(`http://localhost:5173/v2?fixture=em04&t=${t}&paused=1&speed=1`);
    await p.waitForSelector("#v2-net", { state: "attached", timeout: 60000 });
    await p.waitForTimeout(800);
    return p.evaluate(() => {
      const roofs = [...document.querySelectorAll('polygon[fill="url(#v2-net)"]')].filter((pg) => pg.getAttribute("points").trim().split(" ").length === 5);
      // toit : [ligne de but, coin du fond, milieu du fond, coin du fond, ligne de but] ; x du milieu du fond
      return roofs.map((pg) => { const pts = pg.getAttribute("points").trim().split(" ").map((s) => s.split(",").map(Number)); return { ligne: +pts[0][0].toFixed(2), fondMilieu: +pts[2][0].toFixed(3), fondCoin: +pts[1][0].toFixed(3) }; });
    });
  };
  const res = {};
  for (const c of CASES) {
    const juste = await read(c.goal + 0.05 / 60);
    await p.screenshot({ path: `${out}/em21b-${c.nom}-ondule.png` });
    const repos = await read(c.goal + 2.5 / 60);
    res[c.nom] = { cote: c.side, justeApres: juste, auRepos: repos };
  }
  console.log(JSON.stringify(res, null, 1));
  await b.close();
})();
