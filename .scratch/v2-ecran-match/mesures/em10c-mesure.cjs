// Ticket v2-ecran-match/10c. Usage : node em10c-mesure.cjs <dossier_captures> (Vite sur :5173 ; traces réelles
// em11-om-ol et em11-psg-havre). Icônes de but dans la composition : joueurs marqués, nombre, révélation, densité de la
// colonne (le HUD grandit avec les buteurs, EM-08c), défilement des colonnes, troncature des noms.
const { chromium } = require("playwright");
const out = process.argv[2];
const CASES = [
  ["em11-om-ol", 1366, 768, 1], ["em11-om-ol", 1366, 768, 2.05], ["em11-om-ol", 1366, 768, 10], ["em11-om-ol", 1366, 768, 104],
  ["em11-om-ol", 1280, 720, 1], ["em11-om-ol", 1280, 720, 104], ["em11-om-ol", 1920, 1080, 1], ["em11-om-ol", 1920, 1080, 104],
  ["em11-psg-havre", 1366, 768, 104],
];
(async () => {
  const b = await chromium.launch();
  const res = {};
  for (const [fx, w, h, t] of CASES) {
    const p = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
    await p.goto(`http://localhost:5173/v2?fixture=${fx}&t=${t}&paused=1`);
    await p.waitForSelector("svg[viewBox]", { timeout: 120000 });
    await p.waitForTimeout(1500);
    res[`${fx} ${w}x${h}@${t}`] = await p.evaluate(() => {
      const col = (s) => {
        const z = document.querySelector(`[data-zone=composition-${s}]`);
        if (!z || !z.getBoundingClientRect().width) return null;
        const marks = [...z.querySelectorAll("[data-goal]")].map((m) => {
          const li = m.closest("li");
          const name = li.querySelector("[data-name]");
          return `${name.textContent}:${m.dataset.goal}:${m.innerText.trim() || "1"}${name.scrollWidth > name.clientWidth ? ":tronqué" : ""}`;
        });
        return {
          hauteur: Math.round(z.getBoundingClientRect().height), densite: z.querySelector("[data-density]")?.dataset.density,
          defile: z.scrollHeight - z.clientHeight, marques: marks,
        };
      };
      return {
        hud: Math.round(document.querySelector("[data-zone=hud]").getBoundingClientRect().height),
        score: document.querySelector("[data-zone=score]").innerText.replace(/\s/g, ""),
        domicile: col("home"), exterieur: col("away"),
      };
    });
    await p.screenshot({ path: `${out}/em10c-${fx}-${w}x${h}-t${t}.png` });
    await p.close();
  }
  console.log(JSON.stringify(res, null, 1));
  await b.close();
})();
