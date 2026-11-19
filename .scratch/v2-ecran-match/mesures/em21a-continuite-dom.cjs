// EM-21a, contrôle demandé par l'expert (rejet A1) : sur un ballon lent en diagonale (trace em04, minute 20,148 :
// 7,8 m/s, direction (-0,83 ; -0,55)), décalage du motif lu dans le DOM (patternTransform moins centre du ballon) à
// 30 instants espacés de 1/60 s de match (une image à 60 im/s en x1), soit plusieurs passages de carreau de 0,5 m.
// D'une image à la suivante, l'écart (ramené dans [-T/2, T/2)) doit égaler le déplacement du centre du ballon à l'écran ;
// avant le correctif, un saut de 0,3 à 0,45 m apparaissait à chaque passage. node em21a-continuite-dom.cjs
const { chromium } = require("playwright");
const T = 0.5, START = 20.1483333333332, N = 30;
const unwrap = (d) => ((((d + T / 2) % T) + T) % T) - T / 2;
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1366, height: 768 } });
  const rows = [];
  for (let k = 0; k < N; k++) {
    await p.goto(`http://localhost:5173/v2?fixture=em04&t=${START + k / 3600}&paused=1&speed=1`);
    await p.waitForSelector("#v2-ball-panels", { state: "attached", timeout: 60000 });
    await p.waitForTimeout(250);
    rows.push(await p.evaluate(() => {
      const c = document.querySelector("circle[data-ball]");
      const m = /translate\(([-\d.e]+) ([-\d.e]+)\)/.exec(document.querySelector("#v2-ball-panels").getAttribute("patternTransform"));
      const cx = +c.getAttribute("cx"), cy = +c.getAttribute("cy");
      return { cx, cy, ox: +m[1] - cx, oy: +m[2] - cy };
    }));
  }
  let worst = 0, wraps = 0;
  for (let k = 1; k < N; k++) {
    const a = rows[k - 1], c = rows[k];
    const ex = Math.abs(unwrap(c.ox - a.ox) - (c.cx - a.cx)), ey = Math.abs(unwrap(c.oy - a.oy) - (c.cy - a.cy));
    worst = Math.max(worst, ex, ey);
    if (Math.abs(c.ox - a.ox) > T / 2 || Math.abs(c.oy - a.oy) > T / 2) wraps++;
  }
  const moved = Math.hypot(rows[N - 1].cx - rows[0].cx, rows[N - 1].cy - rows[0].cy);
  console.log(JSON.stringify({ images: N, deplacementEcranM: +moved.toFixed(3), passagesDeCarreau: wraps, ecartMaxM: +worst.toExponential(2) }));
  await b.close();
})();
