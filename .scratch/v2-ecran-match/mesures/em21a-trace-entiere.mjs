// EM-21a, critère C2 : sur toute la piste d'une trace enregistrée, à pas de 0,02 s de match, la traînée ne dépasse jamais
// la distance parcourue depuis la dernière coupure, est nulle sur un ballon tenu ou mort, et part de zéro après chaque
// coupure ; part du temps de ballon libre avec traînée. node em21a-trace-entiere.mjs <trace.json>
import fs from "node:fs";
import { ballMotion, trailLength, TRAIL_SPEED } from "../../../ui/src/utils/v2BallLook.js";
import { ballCut } from "../../../ui/src/utils/v2Spline.js";
const t = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const track = t.ball_track, half = t.second_half_start_minute ?? 45;
const dt = 0.02 / 60;
let n = 0, free = 0, withTrail = 0, overshoot = 0, heldOrDead = 0, afterCut = 0, afterCutTrail = 0, maxTrail = 0;
for (let m = track[0].minute; m <= track.at(-1).minute; m += dt) {
  n++;
  const mo = ballMotion(track, m, half);
  const tr = trailLength(mo);
  if (!mo) { heldOrDead++; if (tr > 0) overshoot++; continue; }
  free++;
  if (tr > 0) withTrail++;
  if (tr > mo.distance + 1e-9) overshoot++;
  maxTrail = Math.max(maxTrail, tr);
}
// premier pas libre après chaque coupure : la traînée y est bornée par la distance (≤ un pas de piste)
for (let i = 1; i < track.length - 1; i++) {
  if (!ballCut(track[i - 1], track[i], half) || track[i].holder || track[i].dead) continue;
  afterCut++;
  const mo = ballMotion(track, track[i].minute + 0.5 * (track[i + 1].minute - track[i].minute), half);
  const tr = trailLength(mo);
  if (mo && tr > mo.distance + 1e-9) afterCutTrail++;
}
console.log(JSON.stringify({ instants: n, ballonLibre: free, tenuOuMort: heldOrDead, partTraineeSurLibre: +(100 * withTrail / free).toFixed(1),
  traineeAuDelaDeLaCoupure: overshoot, traineeMaxM: +maxTrail.toFixed(2), coupuresSuiviesDeBallonLibre: afterCut, depassementApresCoupure: afterCutTrail, seuil: TRAIL_SPEED }));
