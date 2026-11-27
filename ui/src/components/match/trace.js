import dims from "../../utils/pitchGeometry.json";
import { clock, halfStart } from "../../utils/matchClock";
import { goalBall } from "../../utils/v2GoalBall";
import { displayBall, playersBetween } from "../../utils/v2Spline";

// Lecture d'une trace V2 à un instant donné (ticket v2-ecran-match/01 : déplacé depuis routes/V2Match.jsx).
export const L = dims.pitch_length_m;
export const W = dims.pitch_width_m;
// Début de la 2e période et minute affichée : `utils/matchClock.js` (déplacés tels quels par le ticket
// v2-ecran-match/08, pour être testés sous node), ré-exportés ici pour les composants.
export { clock, halfStart };

// Position à `seconds` de match, interpolée entre les deux ticks enregistrés qui l'encadrent. Les joueurs gardent
// le même ordre d'un tick à l'autre (liste construite une fois côté moteur). Ticket v2-correctifs-ecran/04b : courbe
// de Catmull-Rom centripète pour les joueurs (images à 0,5 s) et pour le ballon libre (piste `ball_track`, un point
// toutes les 0,1 s) ; le ballon tenu suit la position affichée de son porteur. Coupures : `utils/v2Spline.js`.
export function interpolatedTick(trace, seconds) {
  const last = trace.ticks.length - 1;
  const exact = Math.min(last, Math.max(0, seconds / trace.tick_seconds));
  const i = Math.min(last, Math.floor(exact));
  const a = trace.ticks[i];
  const b = trace.ticks[Math.min(last, i + 1)];
  // la mi-temps replace tout le monde d'un coup : pas de glissade entre la dernière image de la 1re période et la
  // première de la 2e (elle est cachée par le bandeau)
  const half = halfStart(trace);
  const f = a.minute < half && b.minute >= half ? 0 : exact - i;
  const mix = (u, v) => u + (v - u) * f;
  // cap du corps en degrés (ticket v2-realisme/07a) : par le plus court côté, jamais un tour complet entre deux images
  const mixAngle = (u = 0, v = 0) => u + ((((v - u + 180) % 360) + 360) % 360 - 180) * f;
  const minute = mix(a.minute, b.minute);
  const positions = playersBetween(trace.ticks, i, f, half);
  const players = a.players.map((p, k) => ({
    ...p,
    x: positions[k].x,
    y: positions[k].y,
    facing: mixAngle(p.facing, b.players[k].facing),
  }));
  // but entre les deux images : le ballon entre dans le but au lieu de glisser vers le rond central
  const scored = goalBall(a, b, minute, trace.goals, dims.pitch_length_m, dims.pitch_width_m);
  // mode (« sol » / « aérien ») et ballon mort : ceux de l'image de départ (ticket v2-hauteur-ballon/01)
  const state = { mode: a.ball.mode, dead: a.ball.dead };
  // hauteur entre deux images (ticket v2-hauteur-ballon/02b1) : linéaire, 0 pour une trace qui n'en porte pas
  const z = Math.max(0, mix(a.ball.z ?? 0, b.ball.z ?? 0));
  if (scored) return { minute, players, ball: { ...scored, z, holder: null, ...state } };
  const linear = { x: mix(a.ball.x, b.ball.x), y: mix(a.ball.y, b.ball.y), z };
  const ball = displayBall(trace.ball_track, minute, half, players, linear, a.ball.holder);
  return { minute, players, ball: { ...ball, ...state } };
}

// Demi-tour de la scène autour du rond central (2e période) : chaque équipe attaque l'autre but.
export function rotated(tick) {
  const turn = (o) => ({ ...o, x: L - o.x, y: W - o.y });
  // le cap tourne avec la scène (ticket v2-realisme/07a)
  return { ...tick, players: tick.players.map((p) => ({ ...turn(p), facing: (p.facing ?? 0) + 180 })), ball: turn(tick.ball) };
}

// Situation de jeu d'une équipe à `minute` : dernier changement enregistré avant cet instant (ticket v2-collectif/03).
export function situationAt(trace, team, minute) {
  return (trace.situations || []).filter((s) => s.team === team && s.minute <= minute).at(-1)?.situation || "";
}
