// EM-07 : node marqueurs.cjs <dossier> <kits.json>. Trace em04, minute 30, en pause, 1366x768.
const { chromium } = require("playwright");
const fs = require("fs");
const [out, kitsPath] = process.argv.slice(2);
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1366, height: 768 }, deviceScaleFactor: 1 });
  await p.goto("http://localhost:5173/v2?fixture=em04&t=30&paused=1");
  await p.waitForSelector("#v2-net", { state: "attached", timeout: 60000 });
  await p.waitForTimeout(1500);
  // 1. géométrie : ballon, rayons, relief présent et masqué
  const geo = await p.evaluate(() => {
    const svg = document.querySelector("#v2-net").ownerSVGElement;
    const circles = [...svg.querySelectorAll("circle")];
    const ball = circles.filter((c) => c.getAttribute("fill") === "white" && c.getAttribute("stroke") === "black").map((c) => +c.getAttribute("r"));
    const relief = [...svg.querySelectorAll("circle[data-relief]")];
    return { ballons: ball, reliefs: relief.length, masque: relief[0]?.getAttribute("mask"), rayons: [...new Set(relief.map((c) => +c.getAttribute("r")))] };
  });
  // 2. pixels : centre de chaque rond (zone du numéro) avec et sans relief -> identiques ; bord haut gauche -> éclairci
  const pts = await p.evaluate(() => [...document.querySelectorAll("circle[data-relief]")].map((c) => {
    const r = c.getBoundingClientRect();
    return { cx: r.x + r.width / 2, cy: r.y + r.height / 2, R: r.width / 2 };
  }));
  const shot = async (name) => { await p.screenshot({ path: `${out}/${name}.png` }); };
  await shot("relief-avec");
  await p.addStyleTag({ content: "circle[data-relief]{display:none}" });
  await shot("relief-sans");
  await b.close();
  fs.writeFileSync(`${out}/relief-points.json`, JSON.stringify(pts));
  console.log(JSON.stringify(geo));
})();
