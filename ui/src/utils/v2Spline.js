// Interpolation courbe de la trace V2 à l'écran (ticket v2-correctifs-ecran/04b) : Catmull-Rom centripète (alpha = 0,5,
// validé par le propriétaire le 16/11/2026) entre les deux points qui encadrent l'instant, avec leurs deux voisins. La
// courbe passe par les points réels du moteur ; la variante centripète ne fait ni boucle ni dépassement dans un virage
// serré. Fonctions pures, sans dépendance, testées par `node --test` (v2Spline.test.js).

const ALPHA = 0.5;
const EPS = 1e-6;

// Écart de nœud entre deux points (distance^alpha), jamais nul : deux points confondus (ballon arrêté) ne divisent pas
// par zéro.
const knot = (p, q) => Math.max(EPS, Math.hypot(q.x - p.x, q.y - p.y) ** ALPHA);

// Point de la courbe entre p1 (f = 0) et p2 (f = 1), avec p0 et p3 pour la forme. Un voisin absent (coupure, bord de la
// trace) est remplacé par le point qu'il borde : la courbe y part en ligne droite.
export function catmullRom(p0, p1, p2, p3, f) {
  if (!p0) p0 = p1;
  if (!p3) p3 = p2;
  const d12 = Math.hypot(p2.x - p1.x, p2.y - p1.y);
  if (d12 < EPS) return { x: p1.x, y: p1.y };
  const t0 = 0;
  const t1 = t0 + knot(p0, p1);
  const t2 = t1 + knot(p1, p2);
  const t3 = t2 + knot(p2, p3);
  const t = t1 + (t2 - t1) * f;
  // Barry-Goldman, coordonnée par coordonnée
  const lerp = (a, b, ta, tb) => {
    const w = tb - ta < EPS ? 0 : (t - ta) / (tb - ta);
    return { x: a.x + (b.x - a.x) * w, y: a.y + (b.y - a.y) * w };
  };
  const a1 = lerp(p0, p1, t0, t1);
  const a2 = lerp(p1, p2, t1, t2);
  const a3 = lerp(p2, p3, t2, t3);
  const b1 = lerp(a1, a2, t0, t2);
  const b2 = lerp(a2, a3, t1, t3);
  return lerp(b1, b2, t1, t2);
}

// La période change entre deux instants (mi-temps : tout le monde est replacé d'un coup).
const crossesHalf = (m1, m2, half) => m1 < half && m2 >= half;

// Le ballon ne doit pas être lissé entre deux points de la piste : changement de porteur, ballon mort (sortie, remise en
// jeu, but : le moteur le pose au point de remise) ou mi-temps.
export function ballCut(u, v, half) {
  return u.holder !== v.holder || !!u.dead !== !!v.dead || (u.dead && v.dead) || crossesHalf(u.minute, v.minute, half);
}

// Les joueurs ne sont pas lissés entre deux images de part et d'autre d'une remise en jeu (le moteur pose le preneur au
// point de remise) ou de la mi-temps.
export function playersCut(a, b, half) {
  return !!a.ball.dead !== !!b.ball.dead || crossesHalf(a.minute, b.minute, half);
}

// Index du point de `track` qui ouvre l'intervalle contenant `minute` (points régulièrement espacés, minutes arrondies
// au 1e-5 près par l'API : l'estimation est corrigée par les voisins).
export function trackIndex(track, minute) {
  const last = track.length - 1;
  if (last <= 0) return 0;
  const step = (track[last].minute - track[0].minute) / last;
  let i = step > 0 ? Math.floor((minute - track[0].minute) / step) : 0;
  i = Math.min(last, Math.max(0, i));
  while (i < last && track[i + 1].minute <= minute) i += 1;
  while (i > 0 && track[i].minute > minute) i -= 1;
  return i;
}

// Position du ballon libre à `minute`, lue dans la piste (un point par pas du moteur). `null` si la piste ne couvre pas
// l'instant (trace sans piste, ou rejeu en direct en avance sur elle) : l'appelant garde l'interpolation des images.
// Hauteur `z` (ticket v2-hauteur-ballon/02b) : en ligne droite entre deux points (0,1 s), sans calcul physique ; la
// courbe du vol est celle des points du moteur. Une piste sans hauteur (trace ancienne) donne 0.
const zOf = (p) => p.z ?? 0;
export function ballFromTrack(track, minute, half) {
  if (!track || track.length < 2 || minute < track[0].minute || minute > track[track.length - 1].minute) return null;
  const i = trackIndex(track, minute);
  const p1 = track[i];
  const p2 = track[Math.min(track.length - 1, i + 1)];
  if (p2 === p1 || p2.minute <= p1.minute) return { point: p1, x: p1.x, y: p1.y, z: zOf(p1) };
  const f = Math.min(1, Math.max(0, (minute - p1.minute) / (p2.minute - p1.minute)));
  const z = zOf(p1) + (zOf(p2) - zOf(p1)) * f;
  if (ballCut(p1, p2, half)) {
    // saut net pour un ballon mort ou la mi-temps ; changement de porteur : ligne droite sur un pas (0,1 s)
    if (p1.dead || p2.dead || crossesHalf(p1.minute, p2.minute, half)) return { point: p1, x: p1.x, y: p1.y, z: zOf(p1) };
    return { point: p1, x: p1.x + (p2.x - p1.x) * f, y: p1.y + (p2.y - p1.y) * f, z };
  }
  const p0 = i > 0 && !ballCut(track[i - 1], p1, half) ? track[i - 1] : null;
  const p3 = i + 2 < track.length && !ballCut(p2, track[i + 2], half) ? track[i + 2] : null;
  const c = catmullRom(p0, p1, p2, p3, f);
  return { point: p1, x: c.x, y: c.y, z };
}

// Ballon affiché à `minute` (hors but entre deux images, réglé par `v2GoalBall.js`) : tenu, il suit la position
// affichée de son porteur (pas de décalage entre le joueur et son ballon) ; libre, la piste fine ; sans piste qui couvre
// l'instant, `fallback` (interpolation des images, comme avant le 04b) et le porteur `fallbackHolder`.
export function displayBall(track, minute, half, players, fallback, fallbackHolder) {
  const fine = ballFromTrack(track, minute, half);
  const holder = fine ? fine.point.holder : fallbackHolder;
  const carrier = holder ? players.find((p) => p.name === holder) : null;
  const at = carrier ?? fine ?? fallback;
  // tenu : au pied de son porteur ; libre : la hauteur de la piste, sinon celle des images (`fallback.z`)
  const z = carrier ? 0 : (fine ? fine.z : fallback.z ?? 0);
  return { x: at.x, y: at.y, z, holder: holder ?? null };
}

// Positions des joueurs entre les images `a` (index i) et `b`, lissées avec les images voisines. `f` : fraction de
// l'intervalle. Renvoie, pour chaque joueur (même ordre d'une image à l'autre), { x, y }.
export function playersBetween(ticks, i, f, half) {
  const last = ticks.length - 1;
  const a = ticks[i];
  const b = ticks[Math.min(last, i + 1)];
  if (b === a || playersCut(a, b, half)) {
    return a.players.map((p, k) => ({ x: p.x + (b.players[k].x - p.x) * f, y: p.y + (b.players[k].y - p.y) * f }));
  }
  const prev = i > 0 && !playersCut(ticks[i - 1], a, half) ? ticks[i - 1] : null;
  const next = i + 2 <= last && !playersCut(b, ticks[i + 2], half) ? ticks[i + 2] : null;
  return a.players.map((p, k) => catmullRom(prev?.players[k], p, b.players[k], next?.players[k], f));
}
