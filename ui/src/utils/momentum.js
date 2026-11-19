// Pression territoriale par minute (ticket v2-ecran-match/11b, constantes validées par le propriétaire le 19/11/2026).
// Module sans import : testé sous node.
//
// Poussée d'un instant = position du ballon dans la longueur (repère moteur : domicile attaque vers x croissant tout le
// match), accentuée près des buts (dx·|dx|), plus un bonus à l'équipe qui a le ballon ; moyenne sur la minute. Formule
// inchangée depuis l'ancien `Momentum.jsx` ; seules l'échelle (fixe) et les minutes prises en compte (terminées) changent.
export const POSSESSION_BONUS = 0.15;
export const FULL_SCALE = 0.6; // valeur représentée en pleine hauteur ; écrêtée au-delà
export const MIN_BAR_PX = 1; // une minute jouée se voit, même neutre
export const LABEL = "Pression territoriale";

// Poussée d'une image `t` sur un terrain de longueur `length` (> 0 : domicile, < 0 : extérieur).
export function tickPush(t, length) {
  const dx = (t.ball.x - length / 2) / (length / 2);
  const holderTeam = t.ball.holder && t.players.find((p) => p.name === t.ball.holder)?.team;
  return dx * Math.abs(dx) + (holderTeam === "home" ? POSSESSION_BONUS : holderTeam === "away" ? -POSSESSION_BONUS : 0);
}

// Minutes terminées à l'instant lu `shownMin` : la barre d'une minute n'apparaît qu'une fois la minute entièrement vue,
// donc elle ne moyenne que des images déjà vues et ne déborde jamais le curseur. Exception : une fois le match fini et
// lu jusqu'au bout, sa dernière minute (souvent incomplète) est comptée.
export function completedMinutes(shownMin, lastMinute, done) {
  if (done && lastMinute != null && shownMin >= lastMinute) return Math.ceil(lastMinute);
  return Math.max(0, Math.floor(shownMin));
}

// Valeur moyenne de chacune des `complete` premières minutes (null : minute sans image).
export function momentumByMinute(ticks, complete, length) {
  const sums = new Array(complete).fill(0);
  const counts = new Array(complete).fill(0);
  for (const t of ticks) {
    const m = Math.floor(t.minute);
    if (m >= complete) continue;
    sums[m] += tickPush(t, length);
    counts[m] += 1;
  }
  return sums.map((v, m) => (counts[m] ? v / counts[m] : null));
}

// Hauteur (px) de la barre d'une valeur `v`, sur une demi-hauteur de `halfPx` : échelle fixe, 1 px au moins.
export function barHeight(v, halfPx) {
  return Math.min(halfPx, Math.max(MIN_BAR_PX, (Math.abs(v) / FULL_SCALE) * halfPx));
}
