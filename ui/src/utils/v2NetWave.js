// Filet qui ondule sur un but (ticket v2-ecran-match/21b, constantes validées par le propriétaire le 18/11/2026) :
// animation décorative déclenchée par le but lu dans la trace (`trace.goals`), sur le temps de match lu, sans calcul
// physique. Le creusement au point d'entrée réel du ballon, selon sa vitesse, reste au ticket v2-mise-en-scene/05.
// Fonction pure, sans état ni horloge : même trace, même instant, même résultat ; rejouée naturellement pendant le ralenti
// du but, jamais avant que la lecture ne l'atteigne (US-29). Testée par `node --test` (v2NetWave.test.js).

export const WAVE_AMPLITUDE_M = 0.8; // recul du milieu du fond du filet à l'instant du but (m)
export const WAVE_CORNER_M = 0.3; // recul des coins du fond (m)
export const WAVE_FREQUENCY_HZ = 2;
export const WAVE_DECAY_S = 0.5; // constante d'amortissement (s de match)
export const WAVE_DURATION_S = 2; // durée de l'ondulation (s de match, ≤ REPLAY_AFTER_S de useMatchPlayback)

// Ondulation à `minute` : `{ x, k }` avec `x` la ligne de but du filet concerné dans le repère de la vue (0 ou `length`)
// et `k` le facteur de recul (de 1 à l'instant du but vers 0, oscillant : multiplier par WAVE_AMPLITUDE_M ou
// WAVE_CORNER_M) ; `null` hors des WAVE_DURATION_S qui suivent un but. Le domicile marque en x = `length` dans le repère
// du moteur (D-V03, `v2GoalBall.js`) ; en 2e période (`minute` ≥ `half`), la scène est retournée : ce but est dessiné
// en x = 0. `half` doit suivre le même prédicat que la rotation de la scène (`clock` de `trace.js`) : début de 2e période
// donné par le moteur, `Infinity` tant qu'il est inconnu (calcul en direct encore en 1re période).
export function netWave(goals, minute, half, length) {
  if (!goals?.length) return null;
  for (let i = goals.length - 1; i >= 0; i -= 1) {
    const g = goals[i];
    const t = (minute - g.minute) * 60;
    if (t < 0) continue;
    if (t >= WAVE_DURATION_S) return null; // le dernier but déjà atteint est fini : aucun autre ne peut être en cours
    const engineX = g.team === "home" ? length : 0;
    const x = minute >= half ? length - engineX : engineX;
    const k = Math.exp(-t / WAVE_DECAY_S) * Math.cos(2 * Math.PI * WAVE_FREQUENCY_HZ * t);
    return { x, k };
  }
  return null;
}
