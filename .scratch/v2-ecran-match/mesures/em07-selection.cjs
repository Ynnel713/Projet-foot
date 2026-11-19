// EM-07 : un clic sur un marqueur sélectionne le joueur (anneau blanc de 0,4 m, panneau d'intention), un second clic le désélectionne.
const { chromium } = require("playwright");
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1366, height: 768 } });
  await p.goto("http://localhost:5173/v2?fixture=em04&t=30&paused=1");
  await p.waitForSelector("#v2-net", { state: "attached", timeout: 60000 });
  await p.waitForTimeout(1500);
  const state = () => p.evaluate(() => {
    const ring = [...document.querySelectorAll("circle")].filter((c) => (c.getAttribute("style") || "").includes("stroke: white") && c.getAttribute("stroke-width") === "0.4");
    return { anneauxSelection: ring.length, panneau: document.querySelector("[data-zone=bas]").innerText.split("\n").find((l) => /\(/.test(l)) || null };
  });
  const box = await (await p.$$("circle[data-relief]"))[0].boundingBox();
  await p.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
  await p.waitForTimeout(300);
  const apres1 = await state();
  await p.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
  await p.waitForTimeout(300);
  console.log(JSON.stringify({ apresClic: apres1, apresSecondClic: await state() }));
  await b.close();
})();
