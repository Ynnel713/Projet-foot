// EM-07 : planche de rendu. Clone le vrai marqueur d'un joueur du terrain (rond, relief, numéro) pour chaque couleur
// (principales et secondaires des kits, replis), avec les variables d'équipe calculées par la règle d'EM-03
// (teamColorVars), sur le gazon réel. Mesure aussi le contraste numéro / fond pour chaque couleur.
// node planche.cjs <kits.json> <sortie.png>
const { chromium } = require("playwright");
const fs = require("fs");
const [kitsPath, outPng] = process.argv.slice(2);
const kits = JSON.parse(fs.readFileSync(kitsPath, "utf8"));
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1366, height: 768 }, deviceScaleFactor: 2 });
  await p.goto("http://localhost:5173/v2?fixture=em04&t=30&paused=1");
  await p.waitForSelector("#v2-net", { state: "attached", timeout: 60000 });
  await p.waitForTimeout(1500);
  const res = await p.evaluate(async (kits) => {
    const tc = await import("/src/utils/teamColors.js");
    const colors = new Set([tc.FALLBACK.home, tc.FALLBACK.away, tc.OFF_WHITE, "#000000"]);
    for (const [pc, sc] of Object.values(kits)) { if (pc) colors.add(pc.toLowerCase()); if (sc) colors.add(sc.toLowerCase()); }
    const list = [...colors];
    const svg = document.querySelector("#v2-net").ownerSVGElement;
    const marker = svg.querySelector("circle[data-relief]").parentNode;
    const ns = "http://www.w3.org/2000/svg";
    const COLS = 30, STEP = 3.2;
    const board = document.createElementNS(ns, "svg");
    const rows = Math.ceil(list.length / COLS);
    board.setAttribute("viewBox", `0 0 ${COLS * STEP + 1} ${rows * STEP + 1}`);
    board.setAttribute("style", "position:fixed;left:0;top:0;width:1366px;height:768px;z-index:99;background:#24603a");
    // les <defs> du terrain (relief, masque) sont dans le document : les url(#...) des clones les trouvent
    let minContrast = 99, worst = "";
    list.forEach((c, i) => {
      const vars = tc.teamColorVars(tc.teamColors({ home: { color: c, known_kit: true }, away: { color: c === "#000000" ? "#ffffff" : "#000000", known_kit: true } }));
      const g = marker.cloneNode(true);
      const cx = 1.6 + (i % COLS) * STEP, cy = 1.6 + Math.floor(i / COLS) * STEP;
      const body = g.querySelectorAll("circle");
      const x0 = +body[0].getAttribute("cx"), y0 = +body[0].getAttribute("cy");
      g.setAttribute("transform", `translate(${cx - x0} ${cy - y0})`);
      // équipe « home » pour tous les clones, numéro fixe à deux chiffres (cas le plus large)
      g.querySelectorAll("circle").forEach((e) => { const st = e.getAttribute("style") || ""; e.setAttribute("style", st.replace(/--team-away/g, "--team-home")); });
      const t = g.querySelector("text"); if (t) { t.textContent = "88"; t.setAttribute("style", (t.getAttribute("style") || "").replace(/--team-away/g, "--team-home")); }
      g.querySelector("line")?.setAttribute("opacity", "0");
      Object.entries(vars).forEach(([k, v]) => g.style.setProperty(k, v));
      board.appendChild(g);
      const ink = vars["--team-home-ink"], fill = vars["--team-home"];
      const r = tc.contrast(fill, ink); if (r < minContrast) { minContrast = r; worst = `${fill} / ${ink}`; }
    });
    document.body.appendChild(board);
    return { couleurs: list.length, contrasteMin: +minContrast.toFixed(2), pire: worst };
  }, kits);
  await p.waitForTimeout(500);
  await p.screenshot({ path: outPng });
  console.log(JSON.stringify(res));
  await b.close();
})();
