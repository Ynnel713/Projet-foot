// Géométrie de la frise de momentum (ticket v2-ecran-match/11a, constantes validées par le propriétaire le 19/11/2026).
// Module sans import : testé sous node.
export const FRISE_PX = 72; // hauteur totale (plafond de la zone basse, décision EM-04 du 18/11/2026)
export const GOAL_ROW_PX = 8; // rangée des buts au-dessus (domicile) et en dessous (extérieur) des barres
export const BAR_HALF_PX = 22; // demi-hauteur des barres, de part et d'autre de l'axe
export const LABEL_ROW_PX = 12; // repères de minutes
export const BAR_GAP_PX = 2;
export const DOMAIN_MIN = 105; // domaine fixe : les barres ne bougent pas quand le temps additionnel arrive
export const AXIS_Y = GOAL_ROW_PX + BAR_HALF_PX; // 30
export const BARS_BOTTOM_Y = GOAL_ROW_PX + 2 * BAR_HALF_PX; // 52
export const HALF_TIME_MIN = 45;

// Nombre de minutes représentées : 105, plus si le match dure davantage.
export const domainMinutes = (lastMinute) => Math.max(DOMAIN_MIN, Math.ceil(lastMinute ?? 0));

// Abscisse (px) d'un instant `minute` sur une frise de `width` px.
export const minuteX = (minute, width, domain) => (minute / domain) * width;

// Barre de la minute m : abscisse et largeur, avec l'écart entre barres (1 px de chaque côté), 1 px au moins.
// `endMinute` (facultatif) : fin du match ; la barre d'une dernière minute incomplète s'arrête à cet instant, donc au
// curseur de fin, au lieu d'occuper tout son créneau (ticket 11b, réserve A1 de l'expert). Sans effet sur les autres.
export function barBox(m, width, domain, endMinute = Infinity) {
  const w = width / domain;
  const box = { x: m * w + BAR_GAP_PX / 2, width: Math.max(1, w - BAR_GAP_PX) };
  const end = minuteX(endMinute, width, domain);
  if (box.x + box.width <= end) return box;
  const clipped = Math.max(1, end - box.x);
  return { x: Math.min(box.x, end - clipped), width: clipped };
}

// Repères : 0', 15', 30', 45' en 1re période ; trait de mi-temps au début de la 2e période, puis 60', 75', 90' comptés
// depuis ce début. Tant que la lecture n'a pas atteint la 2e période (`halfReached` faux), son début réel n'est pas
// montré (il trahirait la durée du temps additionnel) : repères posés comme si elle commençait à 45', sans trait.
export function ticks(secondHalfStart, halfReached) {
  const start = halfReached && secondHalfStart != null ? secondHalfStart : HALF_TIME_MIN;
  return {
    labels: [
      { minute: 0, label: "0'" },
      { minute: 15, label: "15'" },
      { minute: 30, label: "30'" },
      { minute: 45, label: "45'" },
      { minute: start + 15, label: "60'" },
      { minute: start + 30, label: "75'" },
      { minute: start + 45, label: "90'" },
    ],
    halfLine: halfReached ? start : null,
  };
}

// Marqueurs de but (ticket v2-ecran-match/12, décisions du propriétaire du 19/11/2026) : pastille de 8 px dans la rangée
// des buts du côté de l'équipe qui marque, à la minute du but ; deux pastilles du même côté gardent au moins
// `GOAL_GAP_PX` entre leurs centres (la seconde est poussée vers la droite, sans sortir de la frise).
export const GOAL_DOT_PX = 8;
export const GOAL_GAP_PX = 9;

export function goalMarkers(goals, width, domain) {
  const last = { home: -Infinity, away: -Infinity };
  return goals.map((g, i) => {
    const ideal = minuteX(g.minute, width, domain);
    const x = Math.min(width - GOAL_DOT_PX / 2, Math.max(GOAL_DOT_PX / 2, ideal, last[g.team] + GOAL_GAP_PX));
    last[g.team] = x;
    return { i, team: g.team, x, y: g.team === "home" ? GOAL_ROW_PX / 2 : BARS_BOTTOM_Y + GOAL_ROW_PX / 2 };
  });
}
