// EM-06 : captures en 2e période (échauffement) et position des remplaçants qui s'échauffent. node deuxieme.cjs <dossier> <étiquette>
const { chromium } = require("playwright");
const [out, tag] = process.argv.slice(2);
(async () => {
  const b = await chromium.launch();
  const res = {};
  for (const [w, h, t] of [[1280, 720, 30], [1280, 720, 60], [844, 390, 60], [1920, 1080, 60]]) {
    const p = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
    await p.goto(`http://localhost:5173/v2?fixture=em04&t=${t}&paused=1`);
    await p.waitForSelector("#v2-net", { state: "attached", timeout: 60000 });
    await p.waitForTimeout(1500);
    res[`${w}x${h} t=${t}`] = await p.evaluate(() => {
      const svg = document.querySelector("#v2-net").ownerSVGElement;
      const vb = svg.viewBox.baseVal;
      const COS = Math.cos((35 * Math.PI) / 180);
      // remplaçants qui s'échauffent : leur <title> se termine par « s'échauffe » ; y sol = cy / COS (z = 0)
      const warm = [...svg.querySelectorAll("title")].filter((t) => /s'échauffe$/.test(t.textContent)).map((t) => {
        const c = t.parentNode.querySelector("circle");
        return { y_sol_m: +(c.cy.baseVal.value / COS).toFixed(2), r_m: +c.r.baseVal.value };
      });
      return { viewBox_h_m: +vb.height.toFixed(2), viewBox_w_m: +vb.width.toFixed(2), echauffement: warm };
    });
    await p.screenshot({ path: `${out}/${tag}-${w}x${h}-t${t}.png` });
    await p.close();
  }
  console.log(JSON.stringify(res, null, 1));
  await b.close();
})();
