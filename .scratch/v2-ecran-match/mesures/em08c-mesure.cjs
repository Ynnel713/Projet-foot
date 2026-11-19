// Ticket v2-ecran-match/08c. Usage : node em08c-mesure.cjs <dossier_captures> (Vite sur :5173 ; traces réelles
// em11-om-ol (9 buts, 2e période à 52') et em11-psg-havre (10-0, 4 buteurs)). Buteurs du HUD : lignes par équipe,
// textes, hauteur du HUD, centre du score par rapport au centre du terrain, débordements, défilement de page.
const { chromium } = require("playwright");
const out = process.argv[2];
const CASES = [
  ["em11-om-ol", 1366, 768, 1], ["em11-om-ol", 1366, 768, 2.03], ["em11-om-ol", 1366, 768, 2.05], ["em11-om-ol", 1366, 768, 10],
  ["em11-om-ol", 1366, 768, 104], ["em11-om-ol", 1024, 768, 104], ["em11-om-ol", 1920, 1080, 104], ["em11-om-ol", 844, 390, 104],
  ["em11-psg-havre", 1366, 768, 1], ["em11-psg-havre", 1366, 768, 30], ["em11-psg-havre", 1366, 768, 104],
  ["em11-psg-havre", 1024, 768, 104], ["em11-psg-havre", 1920, 1080, 104],
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
      const box = (e) => e && e.getBoundingClientRect();
      const side = (s) => {
        const ul = document.querySelector(`[data-scorers=${s}]`);
        if (!ul) return null;
        const lis = [...ul.querySelectorAll("li")];
        return {
          lignes: lis.length,
          textes: lis.map((li) => li.innerText.replace(/\n/g, " ")),
          debordements: lis.flatMap((li) => [...li.querySelectorAll("span")]).filter((s) => s.scrollWidth > s.clientWidth + 0.5).map((s) => s.innerText),
          minutesTronquees: [...ul.querySelectorAll("li > span:last-child")].filter((s) => s.scrollWidth > s.clientWidth + 0.5).length,
          hauteur: Math.round(box(ul).height), visible: box(ul).height > 0, survol: ul.getAttribute("title"),
        };
      };
      const score = box(document.querySelector("[data-zone=score]"));
      const pitch = box(document.querySelector("[data-zone=terrain] svg[viewBox]"));
      return {
        score: document.querySelector("[data-zone=score]").innerText.replace(/\s/g, ""),
        hud: Math.round(box(document.querySelector("[data-zone=hud]")).height),
        ecartCentreScore: +((score.left + score.width / 2) - (pitch.left + pitch.width / 2)).toFixed(1),
        domicile: side("home"), exterieur: side("away"),
        pageDefile: document.documentElement.scrollHeight > innerHeight,
      };
    });
    await p.screenshot({ path: `${out}/em08c-${fx}-${w}x${h}-t${t}.png`, clip: { x: 0, y: 0, width: w, height: Math.min(h, 160) } });
    await p.close();
  }
  console.log(JSON.stringify(res, null, 1));
  await b.close();
})();
