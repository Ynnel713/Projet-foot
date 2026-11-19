// État du HUD de l'écran Match (ticket v2-ecran-match/08). Fonctions pures, sans dépendance : testées sous node.

// Score révélé : buts horodatés jusqu'à `shownS` secondes de match (instant le plus avancé déjà vu, pour que le
// score ne recule pas pendant un ralenti). Logique déplacée telle quelle depuis `MatchScreen.jsx` (US-29 : le score
// n'est jamais en avance sur la lecture).
export function revealedScore(goals, shownS) {
  const revealed = goals.filter((g) => g.minute * 60 <= shownS);
  return {
    home: revealed.filter((g) => g.team === "home").length,
    away: revealed.filter((g) => g.team === "away").length,
  };
}

// Badge d'état (décisions du propriétaire, 19/11/2026) : fin du match, puis bandeau de mi-temps, puis lecture qui a
// rattrapé le calcul du moteur, sinon lecture en cours.
export const BADGES = {
  finished: { label: "TERMINÉ", tone: "gold" },
  halftime: { label: "MI-TEMPS", tone: "neutral" },
  loading: { label: "CHARGEMENT…", tone: "muted" },
  live: { label: "EN DIRECT", tone: "live" },
};

export function matchBadge({ finished, halfBanner, waiting }) {
  if (finished) return BADGES.finished;
  if (halfBanner) return BADGES.halftime;
  if (waiting) return BADGES.loading;
  return BADGES.live;
}
