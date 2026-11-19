// Ticket v2-ecran-match/14b. Usage : node em14b-mesure.cjs <dossier_captures> <attendu.json> (Vite sur :5173, trace
// em11-om-ol). Panneau ouvert : valeurs affichées contre matchStats (EM-14a), visibilité du HUD, du terrain et de la
// frise, centrage du score, défilement, lecture qui continue à × 8, feuille du bas à 844×390, bouton de la carte de fin.
const { chromium } = require("playwright");
const fs = require("fs");
const [out, attenduPath] = process.argv.slice(2);
const attendu = JSON.parse(fs.readFileSync(attenduPath, "utf8"));
const read = () => {
  const box = (e) => e && e.getBoundingClientRect();
  const d = document.querySelector("[data-zone=statistiques]");
  const rows = Object.fromEntries([...d.querySelectorAll("[data-stat]")].map((li) => [li.dataset.stat,
    [li.querySelector("[data-side=home]").innerText, li.querySelector("[data-side=away]").innerText]]));
  const visible = (sel) => { const r = box(document.querySelector(sel)); if (!r || !r.width) return false;
    const hit = document.elementFromPoint(r.left + r.width / 2 - (sel.includes("terrain") ? r.width / 4 : 0), r.top + r.height / 2); return !hit?.closest("[data-zone=statistiques]"); };
  const s = box(document.querySelector("[data-zone=score]")), p = box(document.querySelector("[data-zone=terrain] svg[viewBox]"));
  const dr = box(d);
  return { rows, tiroir: `${Math.round(dr.width)}x${Math.round(dr.height)} @ (${Math.round(dr.left)},${Math.round(dr.top)})`,
    hudVisible: visible("[data-zone=hud]"), terrainVisible: visible("[data-zone=terrain] svg[viewBox]"), friseVisible: visible("[data-zone=momentum]"),
    ecartScore: +((s.left + s.width / 2) - (p.left + p.width / 2)).toFixed(1), page: document.documentElement.scrollHeight > innerHeight,
    minute: document.querySelector("[data-zone=minute]").innerText };
};
const fmt = (k, v) => (v == null ? ["—", "—"] : k === "possession" ? [`${v.home} %`, `${v.away} %`] : [`${v.home}`, `${v.away}`]);
(async () => {
  const b = await chromium.launch(); const res = {};
  for (const [w, h, t] of [[1366, 768, 10], [1366, 768, 45], [1024, 768, 103.9], [1920, 1080, 45], [844, 390, 45], [390, 844, 45]]) {
    const p = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
    await p.goto(`http://localhost:5173/v2?fixture=em11-om-ol&t=${t}&paused=1`);
    await p.waitForSelector("[data-zone=bouton-stats]", { timeout: 120000 }); await p.waitForTimeout(800);
    await p.click("[data-zone=bouton-stats]"); await p.waitForTimeout(400);
    const r = await p.evaluate(read);
    const exp = attendu[String(t)];
    r.ecarts = exp ? Object.entries(r.rows).filter(([k, v]) => JSON.stringify(v) !== JSON.stringify(fmt(k, exp[k]))).map(([k, v]) => `${k}: ${v} ≠ ${fmt(k, exp[k])}`) : "pas d'attendu";
    await p.screenshot({ path: `${out}/em14b-${w}x${h}-t${t}.png` });
    await p.keyboard.press("Escape"); await p.waitForTimeout(200);
    r.fermeEchap = !(await p.$("[data-zone=statistiques]"));
    res[`${w}x${h}@${t}`] = r; await p.close();
  }
  // lecture qui continue à × 8, panneau ouvert
  const p = await b.newPage({ viewport: { width: 1366, height: 768 }, deviceScaleFactor: 1 });
  await p.goto("http://localhost:5173/v2?fixture=em11-om-ol&t=20&speed=8");
  await p.waitForSelector("[data-zone=bouton-stats]", { timeout: 120000 });
  await p.click("[data-zone=bouton-stats]");
  const a = await p.evaluate(read); await p.waitForTimeout(6000); const z = await p.evaluate(read);
  await p.screenshot({ path: `${out}/em14b-1366x768-x8.png` });
  res.lectureX8 = { avant: [a.minute, a.rows.shots, a.rows.possession], apres6s: [z.minute, z.rows.shots, z.rows.possession] };
  await p.close();
  // carte de fin : bouton Statistiques
  const q = await b.newPage({ viewport: { width: 1366, height: 768 }, deviceScaleFactor: 1 });
  await q.goto("http://localhost:5173/v2?fixture=em11-om-ol&t=104&paused=1");
  await q.waitForSelector("[data-banner=fin]", { timeout: 120000 });
  await q.click("[data-banner=fin] >> text=Statistiques"); await q.waitForTimeout(300);
  res.carteDeFin = { panneauOuvert: !!(await q.$("[data-zone=statistiques]")), carteFermee: !(await q.$("[data-banner=fin]")) };
  await q.screenshot({ path: `${out}/em14b-fin-1366.png` });
  console.log(JSON.stringify(res, null, 1)); await b.close();
})();
