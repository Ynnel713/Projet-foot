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
export function barBox(m, width, domain) {
  const w = width / domain;
  return { x: m * w + BAR_GAP_PX / 2, width: Math.max(1, w - BAR_GAP_PX) };
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
