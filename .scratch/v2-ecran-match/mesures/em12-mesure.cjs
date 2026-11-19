// Ticket v2-ecran-match/12. Usage : node em12-mesure.cjs <dossier_captures> (Vite sur :5173 ; traces réelles em11-om-ol
// et em11-psg-havre). Marqueurs de but sur la frise : nombre, côté, couleur, écarts, emoji, info-bulle (souris, toucher).
const { chromium } = require("playwright");
const out = process.argv[2];
const CASES = [
  ["em11-om-ol", 1366, 768, 1], ["em11-om-ol", 1366, 768, 2.05], ["em11-om-ol", 1366, 768, 104],
  ["em11-psg-havre", 1024, 768, 104], ["em11-psg-havre", 1366, 768, 30], ["em11-psg-havre", 1920, 1080, 104],
];
const read = () => {
  const z = document.querySelector("[data-zone=momentum]");
  const marks = [...z.querySelectorAll("[data-goal-marker]")].map((g) => {
    const c = g.querySelectorAll("circle")[1];
    return { i: +g.dataset.goalMarker, team: g.dataset.team, x: +c.getAttribute("cx"), y: +c.getAttribute("cy"), r: +c.getAttribute("r"), fill: getComputedStyle(c).fill, label: g.getAttribute("aria-label") };
  });
  const gaps = {};
  for (const t of ["home", "away"]) {
    const xs = marks.filter((m) => m.team === t).map((m) => m.x);
    gaps[t] = xs.length > 1 ? +Math.min(...xs.slice(1).map((x, k) => x - xs[k])).toFixed(2) : null;
  }
  return {
    frise: Math.round(z.getBoundingClientRect().height), marqueurs: marks.length, emoji: z.innerHTML.includes("⚽"),
    ecartMin: gaps, score: document.querySelector("[data-zone=score]").innerText.replace(/\s/g, ""),
    marks: marks.map((m) => `${m.i}:${m.team}:${m.x.toFixed(1)}:${m.y}:${m.r}:${m.label}`), couleurs: [...new Set(marks.map((m) => `${m.team}=${m.fill}`))],
  };
};
(async () => {
  const b = await chromium.launch();
  const res = {};
  for (const [fx, w, h, t] of CASES) {
    const p = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
    await p.goto(`http://localhost:5173/v2?fixture=${fx}&t=${t}&paused=1`);
    await p.waitForSelector("svg[viewBox]", { timeout: 120000 });
    await p.waitForTimeout(1500);
    const r = await p.evaluate(read);
    if (r.marqueurs) {
      await p.hover("[data-goal-marker='0']");
      await p.waitForTimeout(200);
      r.survol = await p.evaluate(() => document.querySelector("[data-goal-tip]")?.innerText ?? null);
      await p.screenshot({ path: `${out}/em12-${fx}-${w}x${h}-t${t}-survol.png`, clip: { x: 0, y: h - 130, width: w, height: 130 } });
      await p.mouse.move(5, 5);
      await p.waitForTimeout(200);
      r.apresSortie = await p.evaluate(() => document.querySelector("[data-goal-tip]")?.innerText ?? null);
      // info-bulle hors de la zone basse ? (débordement horizontal)
    }
    res[`${fx} ${w}x${h}@${t}`] = r;
    await p.screenshot({ path: `${out}/em12-${fx}-${w}x${h}-t${t}.png`, clip: { x: 0, y: h - 130, width: w, height: 130 } });
    await p.close();
  }
  // toucher : contexte tactile, un toucher ouvre, un second referme ; dernier but (près du bord droit)
  const ctx = await b.newContext({ viewport: { width: 1024, height: 768 }, hasTouch: true, deviceScaleFactor: 1 });
  const p = await ctx.newPage();
  await p.goto("http://localhost:5173/v2?fixture=em11-psg-havre&t=104&paused=1");
  await p.waitForSelector("svg[viewBox]", { timeout: 120000 });
  await p.waitForTimeout(1500);
  const last = await p.evaluate(() => document.querySelectorAll("[data-goal-marker]").length - 1);
  await p.tap(`[data-goal-marker='${last}']`);
  await p.waitForTimeout(200);
  const tip = await p.evaluate(() => {
    const t = document.querySelector("[data-goal-tip]");
    if (!t) return null;
    const r = t.getBoundingClientRect(), z = document.querySelector("[data-zone=bas]").getBoundingClientRect();
    return { texte: t.innerText, dansZone: r.left >= z.left && r.right <= z.right, defileX: document.querySelector("[data-zone=bas]").scrollWidth > document.querySelector("[data-zone=bas]").clientWidth };
  });
  await p.screenshot({ path: `${out}/em12-toucher-1024.png`, clip: { x: 0, y: 638, width: 1024, height: 130 } });
  await p.tap(`[data-goal-marker='${last}']`);
  await p.waitForTimeout(200);
  res.toucher = { premier: tip, apresSecond: await p.evaluate(() => document.querySelector("[data-goal-tip]")?.innerText ?? null) };
  console.log(JSON.stringify(res, null, 1));
  await b.close();
})();
