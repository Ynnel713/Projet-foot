// Ticket v2-ecran-match/11b. Usage : node em11b-mesure.cjs <dossier_captures> <ref.json> [trace] [cas JSON] (Vite sur
// :5173 ; trace par défaut em11-om-ol : 2e période à 52', fin à 103,99' ; em11b-fin-96 : la même tronquée à 96,3', finie,
// pour une fin en milieu de minute, réserve A1 de l'expert). ref.json : hauteurs attendues, calculées à part en Python avec
// l'ancienne formule et l'échelle fixe 0,6 (1 px au moins, 22 px au plus). Vérifie : fin de barre ≤ curseur, minutes
// terminées seulement, hauteurs = référence, barres 5 et 20 inchangées quand le match avance, libellé.
const { chromium } = require("playwright");
const fs = require("fs");
const [out, refPath, fixture = "em11-om-ol", casesJson] = process.argv.slice(2);
const ref = JSON.parse(fs.readFileSync(refPath, "utf8")).hauteur;
const CASES = casesJson ? JSON.parse(casesJson) : [[1366, 768, 10], [1366, 768, 30], [1366, 768, 51.5], [1366, 768, 60], [1366, 768, 103.9], [1366, 768, 104], [1024, 768, 60], [1920, 1080, 60]];
(async () => {
  const b = await chromium.launch();
  const res = {};
  for (const [w, h, t] of CASES) {
    const p = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
    await p.goto(`http://localhost:5173/v2?fixture=${fixture}&t=${t}&paused=1`);
    await p.waitForSelector("svg[viewBox]", { timeout: 120000 });
    await p.waitForTimeout(1500);
    const r = await p.evaluate(() => {
      const z = document.querySelector("[data-zone=momentum]");
      const bars = [...z.querySelectorAll("[data-bar]")].map((e) => ({ m: +e.dataset.bar, x: +e.getAttribute("x"), w: +e.getAttribute("width"), h: +e.getAttribute("height") }));
      const svg = z.querySelector("svg");
      return {
        frise: `${Math.round(z.getBoundingClientRect().width)}x${Math.round(z.getBoundingClientRect().height)}`,
        bars, curseur: +z.querySelector("[data-cursor]").getAttribute("x1"),
        libelle: svg.getAttribute("aria-label"), titre: svg.querySelector("title")?.textContent,
      };
    });
    const ecarts = r.bars.map((x) => Math.abs(x.h - ref[x.m]));
    res[`${fixture} ${w}x${h}@${t}`] = {
      frise: r.frise, barres: r.bars.length, derniere: r.bars.at(-1)?.m, curseur: +r.curseur.toFixed(1),
      finDerniereBarre: r.bars.length ? +(r.bars.at(-1).x + r.bars.at(-1).w).toFixed(1) : null,
      barresAuDelaDuCurseur: r.bars.filter((x) => x.x + x.w > r.curseur + 1e-6).length,
      ecartMaxHauteurPx: +Math.max(0, ...ecarts).toFixed(4),
      barre5: r.bars.find((x) => x.m === 5), barre20: r.bars.find((x) => x.m === 20),
      a1px: r.bars.filter((x) => x.h === 1).length, a22px: r.bars.filter((x) => x.h === 22).length,
      libelle: r.libelle, titre: r.titre,
    };
    await p.screenshot({ path: `${out}/em11b-${fixture === "em11-om-ol" ? "" : fixture + "-"}${w}x${h}-t${t}.png` });
    await p.close();
  }
  console.log(JSON.stringify(res, null, 1));
  await b.close();
})();
