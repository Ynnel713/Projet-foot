// Minute du match lue dans une trace V2 (déplacé sans modification depuis `components/match/trace.js` par le ticket
// v2-ecran-match/08, pour le tester sous node : ce module n'importe rien).
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
