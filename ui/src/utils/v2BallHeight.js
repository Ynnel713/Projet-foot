// Hauteur du ballon à l'écran V2 (ticket v2-hauteur-ballon/02b1 ; constantes du ticket 02b, point 2) : le ballon est
// dessiné à sa vraie hauteur `z` (bas du ballon, m, lue dans la trace) et grossit en montant ; son ombre reste au sol,
// rapetisse et pâlit. Fonctions pures, testées par `node --test` (v2BallHeight.test.js). Habillage seulement.

export const BALL_R = 0.5; // ballon au sol (m ; 0,4 avant le ticket v2-ecran-match/07, validé par le propriétaire le 18/11/2026)
const GROWTH_PER_M = 0.05; // rayon du ballon : + 5 % par mètre de hauteur…
const GROWTH_MAX = 0.4; // … jusqu'à + 40 % (8 m et au-delà)
const SHADOW_SHRINK_PER_M = 0.05; // rayon de l'ombre : − 5 % par mètre…
const SHADOW_MIN = 0.5; // … jusqu'à la moitié du ballon au sol (10 m et au-delà)
const SHADOW_OPACITY_GROUND = 0.3; // opacité de l'ombre au ras du sol…
const SHADOW_OPACITY_HIGH = 0.1; // … et à SHADOW_FADE_M de hauteur et au-delà
const SHADOW_FADE_M = 10;

const height = (z) => Math.max(0, Number.isFinite(z) ? z : 0);

// Rayon dessiné du ballon à la hauteur `z`.
export function ballRadius(z) {
  return BALL_R * (1 + Math.min(GROWTH_MAX, GROWTH_PER_M * height(z)));
}

// Ombre du ballon à la hauteur `z` : rayon (m) et opacité ; `null` au sol (le ballon couvre sa propre ombre).
export function ballShadow(z) {
  const h = height(z);
  if (h <= 0) return null;
  const k = Math.min(1, h / SHADOW_FADE_M);
  return {
    r: BALL_R * Math.max(SHADOW_MIN, 1 - SHADOW_SHRINK_PER_M * h),
    opacity: SHADOW_OPACITY_GROUND + (SHADOW_OPACITY_HIGH - SHADOW_OPACITY_GROUND) * k,
  };
}
