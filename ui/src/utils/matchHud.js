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
  replay: { label: "RALENTI", tone: "accent" }, // ticket v2-ecran-match/13
  loading: { label: "CHARGEMENT…", tone: "muted" },
  live: { label: "EN DIRECT", tone: "live" },
};

export function matchBadge({ finished, halfBanner, replaying, waiting }) {
  if (finished) return BADGES.finished;
  if (halfBanner) return BADGES.halftime;
  if (replaying) return BADGES.replay;
  if (waiting) return BADGES.loading;
  return BADGES.live;
}

// Buteurs révélés (ticket v2-ecran-match/08c, décisions du propriétaire du 19/11/2026) : pour chaque équipe, un buteur
// par ligne avec les minutes de ses buts, dans l'ordre de son premier but ; seulement les buts déjà lus (même règle que
// `revealedScore`). `team` d'un but = équipe qui marque ; un but contre son camp est rangé sous elle, marqué « csc ».
// `minuteLabel(minute)` : libellé de l'horloge du HUD (ex. 2', 45+3'). Au-delà de `maxLines` buteurs, les
// `maxLines - 1` premiers puis une ligne « +n autres » (`hidden`), pour tenir en `maxLines` lignes.
export const SCORER_LINES = 3;

export function revealedScorers(goals, shownS, minuteLabel, maxLines = SCORER_LINES) {
  const result = {};
  for (const team of ["home", "away"]) {
    const rows = [];
    for (const g of goals) {
      if (g.team !== team || g.minute * 60 > shownS) continue;
      const name = g.scorer || "But";
      const ownGoal = Boolean(g.own_goal);
      let row = rows.find((r) => r.name === name && r.ownGoal === ownGoal);
      if (!row) rows.push((row = { name, ownGoal, minutes: [] }));
      row.minutes.push(minuteLabel(g.minute));
    }
    const shown = rows.length > maxLines ? rows.slice(0, maxLines - 1) : rows;
    result[team] = { all: rows, shown, hidden: rows.length - shown.length };
  }
  return result;
}

// Nom affiché dans le HUD : sans le prénom (premier mot), comme une retransmission : « Kvaratskhelia », « Van Neck »,
// « Egan-Riley » ; un nom d'un seul mot reste entier.
export const hudName = (name) => {
  const words = name.trim().split(/\s+/);
  return words.length > 1 ? words.slice(1).join(" ") : name;
};

// Texte d'une ligne (info-bulle, nom complet) : « Loïs Openda 3', 8' », « Clinton Mata (csc) 52' ».
export const scorerText = (row) => `${row.name}${row.ownGoal ? " (csc)" : ""} ${row.minutes.join(", ")}`;

// Texte du bandeau de but (ticket v2-ecran-match/13) : « BUT · 23' · Kvaratskhelia · Paris Saint-Germain » ; csc
// indiqué ; buteur inconnu : sans nom.
export function goalBannerText(goal, minuteLabel, club) {
  const name = goal.scorer ? `${hudName(goal.scorer)}${goal.own_goal ? " (csc)" : ""}` : null;
  return ["BUT", minuteLabel, name, club].filter(Boolean).join(" · ");
}
