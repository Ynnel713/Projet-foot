// Ticket v2-ecran-match/13. Usage : node em13-mesure.cjs <dossier_captures> (Vite sur :5173 ; trace réelle em11-om-ol :
// buts à 2,037' (OL), 7,208', 9,658' (OM)… ; 2e période à 52' ; fin à 103,99'). Lecture réelle (pas en pause) : on
// relève toutes les 25 ms les bandeaux, le score, le badge et le temps de match lu (minute du HUD), en horloge réelle.
const { chromium } = require("playwright");
const out = process.argv[2];
const sample = () => ({
  t: performance.now(),
  but: document.querySelector("[data-banner=but]")?.innerText ?? null,
  envoi: !!document.querySelector("[data-banner=coup-envoi]"),
  mi: !!document.querySelector("[data-banner=mi-temps]"),
  fin: !!document.querySelector("[data-banner=fin]"),
  score: document.querySelector("[data-zone=score]")?.innerText.replace(/\s/g, ""),
  badge: document.querySelector("[data-zone=etat]")?.innerText,
  minute: document.querySelector("[data-zone=minute]")?.innerText,
});
async function run(b, name, query, seconds, shots = []) {
  const p = await b.newPage({ viewport: { width: 1366, height: 768 }, deviceScaleFactor: 1 });
  await p.goto(`http://localhost:5173/v2?fixture=em11-om-ol&${query}`);
  await p.waitForSelector("[data-zone=score]", { timeout: 120000 });
  const log = [];
  const t0 = Date.now();
  let shot = 0;
  while (Date.now() - t0 < seconds * 1000) {
    const s = await p.evaluate(sample);
    log.push(s);
    for (const [key, file] of shots) if (s[key] && !shots.done?.[file]) { shots.done = { ...shots.done, [file]: 1 }; await p.screenshot({ path: `${out}/em13-${file}.png` }); shot++; }
    await p.waitForTimeout(25);
  }
  // intervalles (horloge réelle) pendant lesquels une clé est vraie
  const spans = (key) => {
    const r = []; let start = null;
    for (const s of log) { const on = !!s[key]; if (on && start == null) start = s.t; if (!on && start != null) { r.push(+((s.t - start) / 1000).toFixed(2)); start = null; } }
    if (start != null) r.push(`${((log.at(-1).t - start) / 1000).toFixed(2)}+`);
    return r;
  };
  const firstBut = log.find((s) => s.but);
  const scoreChange = log.find((s, i) => i && s.score !== log[i - 1].score);
  const res = {
    but: spans("but"), texteBut: firstBut?.but ?? null, envoi: spans("envoi"), mi: spans("mi"), fin: spans("fin"),
    ralenti: spans("badgeRalenti"),
    ecartScoreBandeau_ms: firstBut && scoreChange ? Math.round(firstBut.t - scoreChange.t) : null,
    scores: [...new Set(log.map((s) => s.score))], badges: [...new Set(log.map((s) => s.badge))],
    minutes: [log[0].minute, log.at(-1).minute],
  };
  return { p, res, log };
}
(async () => {
  const b = await chromium.launch();
  const R = {};
  // badge RALENTI : clé dérivée
  const wrap = async (name, q, secs, shots) => {
    const { p, res, log } = await run(b, name, q, secs, shots);
    log.forEach((s) => (s.badgeRalenti = s.badge === "RALENTI"));
    const spans = (key) => { const r = []; let st = null; for (const s of log) { const on = !!s[key]; if (on && st == null) st = s.t; if (!on && st != null) { r.push(+((s.t - st) / 1000).toFixed(2)); st = null; } } if (st != null) r.push(`${((log.at(-1).t - st) / 1000).toFixed(2)}+`); return r; };
    res.ralenti = spans("badgeRalenti");
    R[name] = res;
    return p;
  };
  (await wrap("coup-envoi-x1", "t=0&speed=1", 4, [["envoi", "coup-envoi"]])).close();
  (await wrap("but-x1", "t=1.98&speed=1", 30, [["but", "but"], ["badgeRalenti", "ralenti"]])).close();
  (await wrap("but-x8", "t=1.9&speed=8", 6, [])).close();
  (await wrap("depart-apres-but", "t=2.1&speed=1", 3, [])).close();
  (await wrap("mi-temps-x8", "t=51.8&speed=8", 6, [["mi", "mi-temps"]])).close();
  (await wrap("en-cours", "t=30&speed=1", 1, [["score", "en-cours"]])).close();
  // fin : lecture jusqu'au bout, carte, pointeur, fermeture
  const p = await wrap("fin-x1", "t=103.95&speed=1", 6, [["fin", "fin"]]);
  R.finInteractions = await p.evaluate(() => {
    const card = document.querySelector("[data-banner=fin]");
    return {
      texte: card?.innerText.replace(/\n+/g, " | "),
      boutons: [...(card?.querySelectorAll("button") ?? [])].map((x) => x.getAttribute("aria-label") || x.innerText),
      ligneZoneBasse: document.querySelector("[data-zone=bas]").innerText.includes("Match terminé"),
    };
  });
  await p.click("[data-banner=fin] button[aria-label=Fermer]");
  R.finInteractions.apresFermeture = await p.evaluate(() => !!document.querySelector("[data-banner=fin]"));
  await p.close();
  // pointeur : bandeaux transparents (élément sous le centre du bandeau de mi-temps et de but)
  const q = await b.newPage({ viewport: { width: 1366, height: 768 }, deviceScaleFactor: 1 });
  await q.goto("http://localhost:5173/v2?fixture=em11-om-ol&t=0&speed=1");
  await q.waitForSelector("[data-banner=coup-envoi]", { timeout: 120000 });
  R.pointeur = await q.evaluate(() => {
    const el = document.querySelector("[data-banner=coup-envoi]");
    const r = el.getBoundingClientRect();
    const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
    return { pointerEvents: getComputedStyle(el).pointerEvents, cibleSousLeBandeau: hit.closest("[data-banner]") ? "bandeau" : hit.tagName };
  });
  await q.close();
  console.log(JSON.stringify(R, null, 1));
  await b.close();
})();
