// Hauteur du ballon à l'écran V2 (ticket v2-hauteur-ballon/02b, constantes de l'étude docs/ETUDE_HAUTEUR_V2.md
// section 5, validées par le propriétaire le 23/11/2026) : le ballon grossit en montant, son ombre reste au sol sous lui,
// plus petite et plus pâle. Fonctions pures, testées par `node --test` (v2BallHeight.test.js). Habillage seulement.

export const GROWTH_PER_M = 0.05; // grossissement du ballon par mètre de hauteur
export const GROWTH_MAX = 0.4; // grossissement plafonné à + 40 % (atteint à 8 m)
export const SHADOW_SHRINK_PER_M = 0.05; // l'ombre rétrécit de 5 % par mètre…
export const SHADOW_MIN = 0.5; // … jusqu'à la moitié du ballon au sol (atteinte à 10 m)
export const SHADOW_OPACITY_GROUND = 0.3; // opacité de l'ombre d'un ballon au ras du sol
export const SHADOW_OPACITY_HIGH = 0.1; // opacité de l'ombre à SHADOW_FADE_M et au-delà
export const SHADOW_FADE_M = 10;

// Facteur du rayon du ballon à la hauteur `z` (m).
export const ballScale = (z) => 1 + Math.min(GROWTH_MAX, GROWTH_PER_M * Math.max(0, z));

// Facteur du rayon de l'ombre au sol (par rapport au ballon au sol).
export const shadowScale = (z) => Math.max(SHADOW_MIN, 1 - SHADOW_SHRINK_PER_M * Math.max(0, z));

// Opacité de l'ombre : linéaire de SHADOW_OPACITY_GROUND au sol à SHADOW_OPACITY_HIGH à SHADOW_FADE_M, puis constante.
export const shadowOpacity = (z) => {
  const t = Math.min(1, Math.max(0, z) / SHADOW_FADE_M);
  return SHADOW_OPACITY_GROUND + (SHADOW_OPACITY_HIGH - SHADOW_OPACITY_GROUND) * t;
};
