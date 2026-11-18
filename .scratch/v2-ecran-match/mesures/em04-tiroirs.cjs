const { chromium } = require("playwright");
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 844, height: 390 } });
  await p.goto("http://localhost:5173/v2?fixture=em04&t=30&paused=1");
  await p.waitForSelector("#v2-net", { state: "attached", timeout: 60000 });
  await p.waitForTimeout(1000);
  const vis = async () => p.evaluate(() => ["home", "away"].map((s) => {
    const r = document.querySelector(`[data-zone=tiroir-${s}]`).getBoundingClientRect();
    return `${s}:${Math.round(r.left)}..${Math.round(r.right)}`;
  }).join(" "));
  console.log("fermés", await vis());
  await p.click("[data-zone=languette-home]"); await p.waitForTimeout(400);
  console.log("domicile ouvert", await vis(), "aria", await p.getAttribute("[data-zone=languette-home]", "aria-expanded"));
  await p.screenshot({ path: "apres-844x390-tiroir-domicile.png" });
  await p.click("[data-zone=languette-home]"); await p.click("[data-zone=languette-away]"); await p.waitForTimeout(400);
  console.log("extérieur ouvert", await vis());
  await p.screenshot({ path: "apres-844x390-tiroir-exterieur.png" });
  // un joueur reste sélectionnable au centre, tiroirs fermés
  await p.click("[data-zone=languette-away]"); await p.waitForTimeout(400);
  await b.close();
})();
