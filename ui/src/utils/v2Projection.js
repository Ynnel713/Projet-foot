// Caméra fixe inclinée de l'écran V2, sans perspective (ticket v2-hauteur-ballon/01, étude docs/ETUDE_HAUTEUR_V2.md
// section 5). Une seule projection pour tout ce que l'écran pose sur le terrain : (x, y) au sol et z en hauteur, en
// mètres, donnent un point de l'écran, en mètres aussi. Le terrain est écrasé de cos α dans le sens de la largeur, et
// un point à la hauteur z remonte de z·sin α. Le sens de la longueur (x) ne change pas.
// α = 25° depuis la verticale : valeur validée par le propriétaire le 04/11/2026 après prototype (0° contre 35°).
const TILT = (25 * Math.PI) / 180;
export const COS = Math.cos(TILT);
export const SIN = Math.sin(TILT);

export function project(x, y, z = 0) {
  return { x, y: y * COS - z * SIN };
}

// Même projection pour tout un dessin posé à plat (pelouse, lignes, filets) : matrice SVG de z = 0.
export const GROUND_MATRIX = `matrix(1 0 0 ${COS} 0 0)`;
