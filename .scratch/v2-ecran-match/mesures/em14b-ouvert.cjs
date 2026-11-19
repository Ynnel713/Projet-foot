// Ticket v2-ecran-match/14b : durée des images à × 8, panneau fermé puis ouvert (même page, build de production servi
// sur le port donné, harnais d'EM-01 chargé pour démarrer la trace em11-psg-havre). Usage : node em14b-ouvert.cjs <port>
const { chromium } = require("playwright");
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1366, height: 768 }, deviceScaleFactor: 1 });
  await p.goto(`http://localhost:${process.argv[2]}/`);
  await p.addScriptTag({ url: "/__fx/harness.js" });
  p.evaluate(() => __bench("em11-psg-havre", "fps", 40)); // lance la lecture × 8 (relevé interne ignoré)
  await p.waitForSelector("[data-zone=bouton-stats]", { timeout: 60000 }); await p.waitForTimeout(3000);
  const gaps = (s) => p.evaluate((secs) => new Promise((done) => { const g = []; let prev = performance.now(); const until = prev + secs * 1000;
    const f = (now) => { g.push(now - prev); prev = now; if (now < until) requestAnimationFrame(f); else { g.sort((a, b) => a - b); done({ images: g.length, mediane: +g[Math.floor(g.length / 2)].toFixed(1), p95: +g[Math.floor(g.length * 0.95)].toFixed(1), max: +g.at(-1).toFixed(1) }); } };
    requestAnimationFrame(f); }), s);
  const ferme = await gaps(8);
  await p.click("[data-zone=bouton-stats]"); await p.waitForTimeout(500);
  const ouvert = await gaps(8);
  console.log(JSON.stringify({ ferme, ouvert, minuteFin: await p.evaluate(() => document.querySelector("[data-zone=minute]").innerText) }));
  await b.close();
})();
