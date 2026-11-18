// EM-21a : captures zoomées du ballon (rapide avec traînée ; lent qui roule, deux instants rapprochés en x1), écran entier.
// node captures.cjs <dossier> <étiquette>
const { chromium } = require("playwright");
const [out, tag] = process.argv.slice(2);
const FAST = 21.023333333332403, SLOW = 20.1483333333332;
(async () => {
  const b = await chromium.launch();
  const shot = async (t, speed, name, zoom = true) => {
    const p = await b.newPage({ viewport: { width: 1366, height: 768 }, deviceScaleFactor: zoom ? 4 : 1 });
    await p.goto(`http://localhost:5173/v2?fixture=em04&t=${t}&paused=1${speed ? `&speed=${speed}` : ""}`);
    await p.waitForSelector("#v2-net", { state: "attached", timeout: 60000 });
    await p.waitForTimeout(1500);
    const info = await p.evaluate(() => {
      const c = document.querySelector("circle[data-ball]");
      const pat = document.querySelector("#v2-ball-panels");
      return { trail: !!document.querySelector("[data-ball-trail]"), patternTransform: pat?.getAttribute("patternTransform") };
    });
    if (zoom) {
      const r = await (await p.$("circle[data-ball]")).boundingBox();
      await p.screenshot({ path: `${out}/${tag}-${name}.png`, clip: { x: r.x - 30, y: r.y - 20, width: 60, height: 40 } });
    } else await p.screenshot({ path: `${out}/${tag}-${name}.png` });
    await p.close();
    return info;
  };
  const res = {
    rapide_x1: await shot(FAST, 1, "rapide"),
    lent_x1_a: await shot(SLOW, 1, "lent-a"),
    lent_x1_b: await shot(SLOW + 0.15 / 60, 1, "lent-b"),
    lent_x8: await shot(SLOW, 8, "lent-x8"),
    ecran: await shot(FAST, 1, "ecran", false),
  };
  console.log(JSON.stringify(res, null, 1));
  await b.close();
})();
