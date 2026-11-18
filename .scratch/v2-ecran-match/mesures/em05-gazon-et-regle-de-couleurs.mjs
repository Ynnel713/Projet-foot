import fs from "node:fs";
import { deltaE2000 } from "../../../ui/src/utils/teamColors.js";
const kits = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const OLD = ["#2f7d32", "#3a8f3c"], NEW = ["#24603a", "#2a6b3f"];
const ok = (g, c) => c && g.every((x) => deltaE2000(x, c) >= 25);
let n = 0, perdus = [], gagnes = [];
for (const [club, [p, s]] of Object.entries(kits)) {
  if (!s) continue; n++;
  const a = ok(OLD, s), b = ok(NEW, s);
  if (a && !b) perdus.push(`${club} ${s}`); if (!a && b) gagnes.push(`${club} ${s}`);
}
console.log(`kits avec secondaire : ${n} ; secondaire refusée avec le nouveau gazon seulement : ${perdus.length} ; acceptée seulement avec le nouveau : ${gagnes.length}`);
console.log("perdus :", perdus.join(" | ")); console.log("gagnés :", gagnes.join(" | "));
