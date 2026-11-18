// Contraste du numéro sous le relief : fond mélangé à du blanc (opacité k), pour les couleurs principales et secondaires.
import fs from "node:fs";
import { contrast, inkOf, FALLBACK, OFF_WHITE } from "../../../ui/src/utils/teamColors.js";
const kits = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const mix = (hex, k) => "#" + [1, 3, 5].map((i) => Math.round(parseInt(hex.slice(i, i + 2), 16) * (1 - k) + 255 * k).toString(16).padStart(2, "0")).join("");
const colors = new Set([FALLBACK.home, FALLBACK.away, OFF_WHITE, "#000000"]);
for (const [p, s] of Object.values(kits)) { if (p) colors.add(p.toLowerCase()); if (s) colors.add(s.toLowerCase()); }
for (const k of [0, 0.05, 0.1]) {
  let min = 99, worst = "", n = 0;
  for (const c of colors) { const ink = inkOf(c); const r = contrast(mix(c, k), ink); if (r < 4.5) n++; if (r < min) { min = r; worst = `${c} encre ${ink}`; } }
  console.log(`éclaircissement ${k * 100} % : ${colors.size} couleurs, contraste min ${min.toFixed(2)} (${worst}), sous 4,5:1 : ${n}`);
}
