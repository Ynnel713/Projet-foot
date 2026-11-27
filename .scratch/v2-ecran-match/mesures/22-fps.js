// Fluidité de l'écran V2 (tickets v2-hauteur-ballon/02b2, v2-ecran-match/22) : node 22-fps.js <url de base> <dossier des réponses figées> <étiquette> [répétitions]
// Copie de `.scratch/v2-hauteur-ballon/mesures/02b2-fps.js`, changements : ralenti processeur réglable (FPS_RATE, 6 par défaut) ;
// attente du terrain identique pour tous les états, sans `[data-ball]` (voir plus bas : biais du banc du 02b2).
// Même match pour tous les états (réponses d'API figées, interceptées), vitesse de lecture par défaut (×1), processeur
// ralenti 6 fois (CDP), images comptées par requestAnimationFrame pendant 30 s, à partir de 10 s de lecture.
const fs = require("fs");
const { chromium } = require("playwright");
(async () => {
  const [base, dir, label, reps = "3"] = process.argv.slice(2);
  const clubs = fs.readFileSync(`${dir}/clubs.json`, "utf8");
  const names = JSON.parse(fs.readFileSync(`${dir}/names.json`, "utf8"));
  const lineups = { [names.home]: fs.readFileSync(`${dir}/lineup-home.json`, "utf8"), [names.away]: fs.readFileSync(`${dir}/lineup-away.json`, "utf8") };
  const trace = JSON.parse(fs.readFileSync(`${dir}/trace.json`, "utf8"));
  const browser = await chromium.launch();
  const results = [];
  for (let r = 0; r < Number(reps); r += 1) {
    const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
    await page.route("**/api/**", async (route) => {
      const url = new URL(route.request().url());
      const json = (body) => route.fulfill({ status: 200, contentType: "application/json", body });
      if (url.pathname === "/api/clubs") return json(clubs);
      if (url.pathname === "/api/v2/lineup") return json(lineups[url.searchParams.get("club")]);
      if (url.pathname === "/api/v2/matches/start") return json(JSON.stringify({ id: "fps" }));
      if (url.pathname === "/api/v2/matches/fps") {
        const q = (k) => Number(url.searchParams.get(k) || 0);
        return json(JSON.stringify({ ...trace, done: true, error: null, first_tick: q("from_tick"),
          ticks: trace.ticks.slice(q("from_tick")), ball_track: trace.ball_track.slice(q("from_ball")), events: trace.events.slice(q("from_event")) }));
      }
      return route.fulfill({ status: 404, body: "{}" });
    });
    await page.goto(`${base}/v2`);
    await page.getByRole("button", { name: "Lancer le match" }).click();
    // même fenêtre pour tous les états (ticket 22) : terrain présent, puis 10 s de lecture et 30 s de mesure. Le banc du
    // 02b2 attendait `[data-ball]` (apparu au 21a) jusqu'à 60 s : avant le 21a, la mesure tombait après l'arrêt de la
    // lecture (vers 1 min de match sur cette trace, après le premier but), sur une page immobile.
    await page.waitForSelector("svg circle", { state: "attached", timeout: 60000 });
    const cdp = await page.context().newCDPSession(page);
    await cdp.send("Emulation.setCPUThrottlingRate", { rate: Number(process.env.FPS_RATE || 6) });
    await page.waitForTimeout(10000);
    const frames = await page.evaluate(() => new Promise((resolve) => {
      let n = 0; const t0 = performance.now(); const gaps = []; let last = t0;
      const step = (t) => { n += 1; gaps.push(t - last); last = t; if (t - t0 < 30000) requestAnimationFrame(step); else resolve({ n, ms: t - t0, worst: Math.max(...gaps), long: gaps.filter((g) => g > 50).length }); };
      requestAnimationFrame(step);
    }));
    results.push({ fps: (frames.n * 1000) / frames.ms, worst_ms: frames.worst, frames_over_50ms: frames.long });
    await page.close();
  }
  await browser.close();
  const fpsList = results.map((x) => x.fps);
  console.log(JSON.stringify({ label, mean_fps: fpsList.reduce((a, b) => a + b) / fpsList.length, runs: results }));
})();
