// Aspect du ballon à l'écran V2 (ticket v2-ecran-match/21a, constantes validées par le propriétaire le 18/11/2026) :
// roulement du motif et traînée de vitesse, dérivés de la piste du ballon (`ball_track`, un point toutes les 0,1 s) et de
// l'instant lu. Fonctions pures, sans état ni horloge : même piste, même instant, même résultat, quel que soit le nombre
// d'images par seconde. Testées par `node --test` (v2BallLook.test.js). Habillage seulement : rien n'est renvoyé au moteur.
import { ballCut, trackIndex } from "./v2Spline.js";
import { COS } from "./v2Projection.js";

export const PANEL_TILE_M = 0.5; // carreau du motif : un panneau par carreau (m, à l'échelle du ballon dessiné)
export const FREEZE_SPEED = 15; // motif figé quand vitesse (m/s) × vitesse de lecture ≥ ce seuil (> ½ carreau par image à 60 im/s)
export const TRAIL_SPEED = 18; // traînée au-delà de cette vitesse de match (m/s)
export const TRAIL_SECONDS = 0.1; // longueur de la traînée : chemin parcouru pendant ce temps
export const TRAIL_MAX_M = 3; // longueur maximale de la traînée (m)
const RUN_LIMIT = 600; // recherche du début de la course libre : 60 s de piste au plus (borne de coût)

// Mouvement du ballon libre à `minute` (minutes de match) : direction unitaire `dir`, vitesse `speed` (m/s), longueur de
// chemin `distance` parcourue depuis la dernière coupure (changement de porteur, ballon mort, mi-temps : `ballCut`).
// `null` si la piste ne couvre pas l'instant, ou si le ballon est tenu ou mort (pas de traînée).
export function ballMotion(track, minute, half) {
  if (!track || track.length < 2 || minute < track[0].minute || minute > track[track.length - 1].minute) return null;
  const i = trackIndex(track, minute);
  const p1 = track[i];
  const p2 = track[Math.min(track.length - 1, i + 1)];
  if (p2 === p1 || p2.minute <= p1.minute || p1.holder || p1.dead || ballCut(p1, p2, half)) return null;
  const seg = Math.hypot(p2.x - p1.x, p2.y - p1.y);
  const dt = (p2.minute - p1.minute) * 60;
  const f = Math.min(1, Math.max(0, (minute - p1.minute) / (p2.minute - p1.minute)));
  // distance depuis le début de la course libre : somme des pas précédents tant qu'aucune coupure ne les sépare
  let distance = seg * f;
  for (let j = i; j > 0 && i - j < RUN_LIMIT; j -= 1) {
    const a = track[j - 1];
    const b = track[j];
    if (a.holder || a.dead || ballCut(a, b, half)) break;
    distance += Math.hypot(b.x - a.x, b.y - a.y);
  }
  const dir = seg > 1e-9 ? { x: (p2.x - p1.x) / seg, y: (p2.y - p1.y) / seg } : { x: 0, y: 0 };
  return { dir, speed: seg / dt, distance };
}

// Vitesse du ballon à `minute` (m/s), tenu ou libre (la piste suit alors le porteur) : celle du pas de piste qui
// encadre l'instant ; 0 si la piste ne couvre pas l'instant, si le ballon est mort ou si une coupure sépare les deux
// points (le ballon y est replacé : ce n'est pas une vitesse). Sert au seuil de figement du motif.
export function ballSpeed(track, minute, half) {
  if (!track || track.length < 2 || minute < track[0].minute || minute > track[track.length - 1].minute) return 0;
  const i = trackIndex(track, minute);
  const p1 = track[i];
  const p2 = track[Math.min(track.length - 1, i + 1)];
  if (p2 === p1 || p2.minute <= p1.minute || p1.dead || ballCut(p1, p2, half)) return 0;
  return Math.hypot(p2.x - p1.x, p2.y - p1.y) / ((p2.minute - p1.minute) * 60);
}

// Décalage du motif à l'écran (décision du propriétaire du 18/11/2026, après le rejet A1 de l'expert) : le motif est lié
// à la position affichée du ballon (`ground`, repère de la vue, au sol). Le motif est translaté de cette position en plus
// du centre : par rapport au ballon, il avance donc exactement de son déplacement (roulement sans glissement vu de
// dessus), continu partout, virages, réceptions et dribble compris. Ramené au carreau composante par composante (modulo
// positif : le motif se répète en x et en y de l'écran ; le sol est écrasé de cos α dans le sens de la largeur).
// Motif figé (décalage nul) quand vitesse × vitesse de lecture ≥ FREEZE_SPEED : sinon il semblerait tourner à l'envers.
const wrap = (v) => ((v % PANEL_TILE_M) + PANEL_TILE_M) % PANEL_TILE_M;
export function patternOffset(ground, speed, playbackSpeed) {
  if (!ground || speed * playbackSpeed >= FREEZE_SPEED) return { x: 0, y: 0 };
  return { x: wrap(ground.x), y: wrap(ground.y * COS) };
}

// Longueur de la traînée (m) : nulle sous le seuil, chemin des TRAIL_SECONDS précédentes au-delà, plafonnée à
// TRAIL_MAX_M et jamais plus longue que la distance parcourue depuis la dernière coupure (elle ne traverse donc ni un
// but, ni la mi-temps, ni une remise en jeu, ni un changement de porteur).
export function trailLength(motion) {
  if (!motion || motion.speed < TRAIL_SPEED) return 0;
  return Math.min(TRAIL_MAX_M, motion.speed * TRAIL_SECONDS, motion.distance);
}
