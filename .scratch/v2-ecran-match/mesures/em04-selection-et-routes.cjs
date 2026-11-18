const { chromium } = require("playwright");
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
  await p.goto("http://localhost:5173/v2?fixture=em04&t=30&paused=1");
  await p.waitForSelector("#v2-net", { state: "attached", timeout: 60000 });
  await p.waitForTimeout(1000);
  await p.mouse.click(659, 437); await p.waitForTimeout(500);
  const bas = await p.evaluate(() => { const e = document.querySelector("[data-zone=bas]"); return { texte: e.innerText.slice(0, 120), h: Math.round(e.getBoundingClientRect().height), deborde: e.scrollHeight - e.clientHeight }; });
  console.log(JSON.stringify(bas));
  await p.screenshot({ path: "apres-1280x720-joueur-selectionne.png" });
  const q = await b.newPage({ viewport: { width: 1280, height: 720 } });
  await q.goto("http://localhost:5173/v2"); await q.waitForTimeout(1500);
  await q.screenshot({ path: "apres-1280x720-reglage.png" });
  console.log("réglage : header", !!(await q.$("header")), "| retour", await q.locator("text=Retour").count());
  await q.goto("http://localhost:5173/"); await q.waitForTimeout(800);
  console.log("accueil : header", !!(await q.$("header")));
  await b.close();
})();
