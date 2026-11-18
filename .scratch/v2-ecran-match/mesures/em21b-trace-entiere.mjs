// EM-21b, critère C2 : sur toute une trace enregistrée, à pas de 0,02 s de match, l'ondulation du filet est active
// exactement pendant les WAVE_DURATION_S qui suivent chaque but, sur le filet de la vue attendu, et jamais ailleurs.
// Le côté attendu est recalculé indépendamment de netWave : but du domicile en x = longueur (repère du moteur, D-V03),
// retourné en 2e période. node em21b-trace-entiere.mjs <trace.json>
import fs from "node:fs";
import { WAVE_DURATION_S, netWave } from "../../../ui/src/utils/v2NetWave.js";
const t = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const L = 105, half = t.second_half_start_minute ?? 45, goals = t.goals;
const end = t.ticks.at(-1).minute, dt = 0.02 / 60;
let n = 0, active = 0, wrongSide = 0, missing = 0, spurious = 0;
const perGoal = goals.map(() => 0);
for (let m = 0; m <= end; m += dt) {
  n++;
  const w = netWave(goals, m, half, L);
  // but attendu : le plus récent atteint, s'il date de moins de WAVE_DURATION_S (marge de 1e-9 s aux bornes)
  let gi = -1;
  goals.forEach((g, i) => { const s = (m - g.minute) * 60; if (s >= 1e-9 && s < WAVE_DURATION_S - 1e-9) gi = i; });
  if (w) active++;
  if (gi < 0) { if (w && goals.every((g) => { const s = (m - g.minute) * 60; return s < -1e-9 || s > WAVE_DURATION_S + 1e-9; })) spurious++; continue; }
  if (!w) { missing++; continue; }
  perGoal[gi]++;
  const engineX = goals[gi].team === "home" ? L : 0;
  if (w.x !== (m >= half ? L - engineX : engineX)) wrongSide++;
}
console.log(JSON.stringify({ instants: n, buts: goals.length, actifSecondes: +(active * 0.02).toFixed(2), attenduSecondes: goals.length * WAVE_DURATION_S,
  parBut_s: perGoal.map((c) => +(c * 0.02).toFixed(2)), mauvaisCote: wrongSide, manquants: missing, horsFenetre: spurious }));
