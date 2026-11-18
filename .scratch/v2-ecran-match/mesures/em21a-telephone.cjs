// EM-21a, remarque A3 de l'expert : ballon lent sur téléphone en paysage (844×390), capture zoomée au pixel réel
// (deviceScaleFactor 1) et rayon du ballon à l'écran. node em21a-telephone.cjs <dossier>
const { chromium } = require("playwright");
const out = process.argv[2];
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 844, height: 390 }, deviceScaleFactor: 1 });
  await p.goto("http://localhost:5173/v2?fixture=em04&t=20.1483333333332&paused=1&speed=1");
  await p.waitForSelector("#v2-ball-panels", { state: "attached", timeout: 60000 });
  await p.waitForTimeout(800);
  const r = await (await p.$("circle[data-ball]")).boundingBox();
  await p.screenshot({ path: `${out}/telephone-ballon.png`, clip: { x: r.x - 12, y: r.y - 8, width: 24, height: 16 } });
  console.log(JSON.stringify({ rayonPx: +(r.width / 2).toFixed(2) }));
  await b.close();
})();
