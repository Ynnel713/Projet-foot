// "Tour N" -> terminologie foot standard, calculée depuis le nombre de confrontations du tour (1 confrontation = finale, 2 = 1/2,
// 4 = 1/4, 8 = 1/8...) plutôt que depuis `round.number` -- une finale qui s'appelait "Tour 4" n'a pas de sens pour l'utilisateur
// (retour terrain du 29/09/2026).
export function roundLabel(nbTies) {
  if (nbTies === 1) return "Finale";
  if (nbTies === 2) return "1/2 finale";
  return `1/${nbTies}e de finale`;
}

// Libellé d'un tour : celui imposé par le moteur (« Barrages » de la Ligue des Champions) sinon déduit du nombre de confrontations.
export function roundTitle(round) {
  return round.label ?? roundLabel(round.ties.length);
}

// Parcours d'un club dans le tableau : une entrée par tour joué, `{ round, opponent, scored, conceded, penalties }` (`opponent` null = exempt ;
// `penalties` = [pour, contre] ou null). Les scores sont ceux du club (cumul sur les manches).
export function pathOf(rounds, club) {
  const path = [];
  for (const round of rounds) {
    const tie = round.ties.find((t) => t.home === club || t.away === club);
    if (!tie || tie.winner == null) continue;
    if (tie.is_bye) {
      path.push({ round, opponent: null, scored: null, conceded: null, penalties: null });
      continue;
    }
    const atHome = tie.home === club;
    const penalties = tie.penalty_score ? (atHome ? tie.penalty_score : [tie.penalty_score[1], tie.penalty_score[0]]) : null;
    path.push({
      round,
      opponent: atHome ? tie.away : tie.home,
      scored: atHome ? tie.home_goals : tie.away_goals,
      conceded: atHome ? tie.away_goals : tie.home_goals,
      penalties,
    });
  }
  return path;
}
