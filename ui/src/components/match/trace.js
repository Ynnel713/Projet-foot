import dims from "../../utils/pitchGeometry.json";
import { goalBall } from "../../utils/v2GoalBall";

// Lecture d'une trace V2 à un instant donné (ticket v2-ecran-match/01 : déplacé depuis routes/V2Match.jsx).
export const L = dims.pitch_length_m;
export const W = dims.pitch_width_m;
const HALF_TIME_MIN = 45; // repli tant que le moteur n'a pas encore donné le début de la 2e période

// Début de la 2e période selon le moteur (ticket v2-coach-et-gestion-de-match/07).
export const halfStart = (trace) => trace.second_half_start_minute ?? HALF_TIME_MIN;
// Minute affichée, temps additionnel compris (ticket v2-coach-et-gestion-de-match/03, même règle que
// `v2engine.added_time.display_minute`) : 12', 45+2', 67', 90+4'. Renvoie aussi la période et, en temps additionnel,
// les minutes annoncées.
export function clock(trace, minute) {
  const second = trace.second_half_start_minute != null && minute >= trace.second_half_start_minute;
  const elapsed = second ? minute - trace.second_half_start_minute : minute;
  const base = second ? HALF_TIME_MIN : 0;
  const added = elapsed >= HALF_TIME_MIN;
  return {
    second,
    label: added ? `${base + HALF_TIME_MIN}+${Math.floor(elapsed - HALF_TIME_MIN) + 1}'` : `${Math.floor(base + elapsed)}'`,
    announced: added ? trace.added_minutes?.[second ? 1 : 0] : null,
  };
}

// Position à `seconds` de match, interpolée entre les deux ticks enregistrés qui l'encadrent. Les joueurs gardent
// le même ordre d'un tick à l'autre (liste construite une fois côté moteur).
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
  const minute = mix(a.minute, b.minute);
  // but entre les deux images : le ballon entre dans le but au lieu de glisser vers le rond central
  const scored = goalBall(a, b, minute, trace.goals, dims.pitch_length_m, dims.pitch_width_m);
  // mode (« sol » / « aérien ») et ballon mort : ceux de l'image de départ (ticket v2-hauteur-ballon/01)
  const state = { mode: a.ball.mode, dead: a.ball.dead };
  return {
    minute,
    players: a.players.map((p, k) => ({ ...p, x: mix(p.x, b.players[k].x), y: mix(p.y, b.players[k].y) })),
    ball: scored
      ? { ...scored, holder: null, ...state }
      : { x: mix(a.ball.x, b.ball.x), y: mix(a.ball.y, b.ball.y), holder: a.ball.holder, ...state },
  };
}

// Demi-tour de la scène autour du rond central (2e période) : chaque équipe attaque l'autre but.
export function rotated(tick) {
  const turn = (o) => ({ ...o, x: L - o.x, y: W - o.y });
  return { ...tick, players: tick.players.map(turn), ball: turn(tick.ball) };
}

// Situation de jeu d'une équipe à `minute` : dernier changement enregistré avant cet instant (ticket v2-collectif/03).
export function situationAt(trace, team, minute) {
  return (trace.situations || []).filter((s) => s.team === team && s.minute <= minute).at(-1)?.situation || "";
}
