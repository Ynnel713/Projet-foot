// Minute du match lue dans une trace V2 (déplacé sans modification depuis `components/match/trace.js` par le ticket
// v2-ecran-match/08, pour le tester sous node : ce module n'importe rien).
const HALF_TIME_MIN = 45; // repli tant que le moteur n'a pas encore donné le début de la 2e période
// Vitesse de lecture au-delà de laquelle le HUD masque les secondes (ticket v2-ecran-match/08e, constante validée par
// le propriétaire le 21/11/2026) : affichées à x1, x1,5 et x2 ; masquées à x8 et x32 (illisibles), « 12' » comme avant.
export const SECONDS_MAX_SPEED = 2;

// Début de la 2e période selon le moteur (ticket v2-coach-et-gestion-de-match/07).
export const halfStart = (trace) => trace.second_half_start_minute ?? HALF_TIME_MIN;
// Minute affichée, temps additionnel compris (ticket v2-coach-et-gestion-de-match/03, même règle que
// `v2engine.added_time.display_minute`) : 12', 45+2', 67', 90+4'. Renvoie aussi la période et, en temps additionnel,
// les minutes annoncées. `precise` (ticket v2-ecran-match/08e) : temps joué à la seconde, façon chronomètre télé,
// « 12:42 », « 64:12 », et en temps additionnel le temps joué au-delà de 45' de la période : « 45+1:23 », « 90+3:54 ».
export function clock(trace, minute) {
  const second = trace.second_half_start_minute != null && minute >= trace.second_half_start_minute;
  const elapsed = second ? minute - trace.second_half_start_minute : minute;
  const base = second ? HALF_TIME_MIN : 0;
  const added = elapsed >= HALF_TIME_MIN;
  return {
    second,
    label: added ? `${base + HALF_TIME_MIN}+${Math.floor(elapsed - HALF_TIME_MIN) + 1}'` : `${Math.floor(base + elapsed)}'`,
    announced: added ? trace.added_minutes?.[second ? 1 : 0] : null,
    precise: added ? `${base + HALF_TIME_MIN}+${chrono(elapsed - HALF_TIME_MIN, false)}` : chrono(base + elapsed, true),
  };
}

// Minutes décimales en « m:ss » (« mm:ss » si `pad`), secondes tronquées comme les minutes du libellé.
function chrono(minutes, pad) {
  const total = Math.floor(minutes * 60 + 1e-6); // 12.7 * 60 = 761,99999… : la marge évite de perdre une seconde
  const m = String(Math.floor(total / 60));
  return `${pad ? m.padStart(2, "0") : m}:${String(total % 60).padStart(2, "0")}`;
}

// Texte de la minute du HUD : à la seconde jusqu'à `SECONDS_MAX_SPEED`, à la minute au-delà.
export const hudClockText = (time, speed) => (speed <= SECONDS_MAX_SPEED ? time.precise : time.label);
