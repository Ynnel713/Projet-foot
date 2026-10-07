// Constantes et calculs du « live » rejoué : le match est déjà simulé côté moteur, l'écran le REJOUE à une horloge accélérée
// (1 minute de match = 0,6 s en x1). Aucun résultat n'est recalculé ici : tout vient des événements réels de l'API.
export const MATCH_END = 90;
export const TICK_MS = 100;
export const MIN_PER_TICK = 1 / 6; // en x1 : 1 minute de match = 6 ticks de 100 ms = 0,6 s
export const SPEEDS = [1, 2, 4];

// Buts des AUTRES matchs de la journée, chronologiques, avec le score du match juste après le but (pour l'alerte « Lyon 1-0 Lille »).
// `matches` : réponse de GET /matches?journee=N (champ `scorers` : club, player, minute). Les matchs non joués sont ignorés.
export function buildOtherGoals(matches) {
  const goals = [];
  matches.forEach((m, matchIndex) => {
    if (!m.played || !m.scorers) return;
    const ordered = [...m.scorers].sort((a, b) => a.minute - b.minute);
    let home = 0;
    let away = 0;
    ordered.forEach((s, i) => {
      if (s.club === m.home) home += 1;
      else away += 1;
      goals.push({
        key: `${matchIndex}-${i}`,
        minute: s.minute,
        home: m.home,
        away: m.away,
        scoreHome: home,
        scoreAway: away,
        club: s.club,
        player: s.player,
      });
    });
  });
  return goals.sort((a, b) => a.minute - b.minute);
}

// Score courant d'un match à `clock` (minute de match, éventuellement fractionnaire) -- pour le ticker « multiplex ».
export function scoreAt(match, clock) {
  let home = 0;
  let away = 0;
  let lastMinute = null;
  (match.scorers ?? []).forEach((s) => {
    if (s.minute > clock) return;
    if (s.club === match.home) home += 1;
    else away += 1;
    lastMinute = Math.max(lastMinute ?? 0, s.minute);
  });
  return { home, away, lastMinute };
}
