import { project } from "../../utils/v2Projection";
import { PANEL_TILE_M, patternOffset } from "../../utils/v2BallLook";

// Ballon du terrain V2 (ticket v2-ecran-match/21a, constantes validées par le propriétaire le 18/11/2026) : disque blanc à
// contour noir (rayon d'EM-07), panneaux pentagonaux sombres qui glissent dans le sens du déplacement (roulement sans
// glissement : motif lié à la position affichée du ballon, figé au-delà du seuil de crénelage, `utils/v2BallLook.js`),
// reflet fixe en haut à gauche, traînée
// derrière un ballon rapide (`trail` en mètres, jamais au-delà de la dernière coupure : `utils/v2BallLook.js`).
// Le ballon est un seul élément : son motif et sa traînée ont leurs propres `<defs>`, reconstruits à chaque image.
const PANEL = "#1C2128"; // teinte des panneaux
const PANEL_R = 0.13; // rayon d'un panneau (m), un par carreau de PANEL_TILE_M
const TRAIL_OPACITY = 0.3; // opacité de la traînée au ras du ballon, nulle au bout

const pentagon = (r) =>
  Array.from({ length: 5 }, (_, k) => {
    const a = -Math.PI / 2 + (k * 2 * Math.PI) / 5;
    return `${(r * Math.cos(a)).toFixed(3)},${(r * Math.sin(a)).toFixed(3)}`;
  }).join(" ");
const PENTAGON = pentagon(PANEL_R);

// `ground` : position au sol du ballon (m, repère de la vue) ; `z` : hauteur dessinée ; `r` : rayon dessiné ;
// `dir` : direction du déplacement dans le repère de la vue (unitaire, au sol) ou null ; `speed` : vitesse du ballon
// (m/s) et `playbackSpeed` : vitesse de lecture, pour le figement du motif ; `trail` : voir plus haut.
export default function BallMarker({ ground, z, r, dead, dir, speed, playbackSpeed, trail }) {
  const c = project(ground.x, ground.y, z);
  const off = patternOffset(ground, speed, playbackSpeed);
  const tail = trail > 0 && dir ? project(ground.x - dir.x * trail, ground.y - dir.y * trail, z) : null;
  let trailPoints = null;
  if (tail) {
    const len = Math.hypot(tail.x - c.x, tail.y - c.y) || 1;
    const n = { x: -(tail.y - c.y) / len, y: (tail.x - c.x) / len }; // normale à l'écran
    trailPoints = `${c.x + n.x * r},${c.y + n.y * r} ${c.x - n.x * r},${c.y - n.y * r} ${tail.x},${tail.y}`;
  }
  return (
    <g style={{ pointerEvents: "none" }} opacity={dead ? 0.6 : 1}>
      <defs>
        <pattern
          id="v2-ball-panels"
          width={PANEL_TILE_M}
          height={PANEL_TILE_M}
          patternUnits="userSpaceOnUse"
          patternTransform={`translate(${c.x + off.x} ${c.y + off.y})`}
        >
          <polygon points={PENTAGON} fill={PANEL} />
          <polygon points={PENTAGON} fill={PANEL} transform={`translate(${PANEL_TILE_M} 0)`} />
          <polygon points={PENTAGON} fill={PANEL} transform={`translate(0 ${PANEL_TILE_M})`} />
          <polygon points={PENTAGON} fill={PANEL} transform={`translate(${PANEL_TILE_M} ${PANEL_TILE_M})`} />
        </pattern>
        <radialGradient id="v2-ball-shine" cx="0.35" cy="0.35" r="0.6">
          <stop offset="0" stopColor="#fff" stopOpacity={0.35} />
          <stop offset="1" stopColor="#fff" stopOpacity={0} />
        </radialGradient>
        {tail && (
          <linearGradient id="v2-ball-trail" gradientUnits="userSpaceOnUse" x1={c.x} y1={c.y} x2={tail.x} y2={tail.y}>
            <stop offset="0" stopColor="#fff" stopOpacity={TRAIL_OPACITY} />
            <stop offset="1" stopColor="#fff" stopOpacity={0} />
          </linearGradient>
        )}
      </defs>
      {trailPoints && <polygon data-ball-trail="" points={trailPoints} fill="url(#v2-ball-trail)" />}
      <circle cx={c.x} cy={c.y} r={r} fill="white" />
      <circle data-ball-panels="" cx={c.x} cy={c.y} r={r} fill="url(#v2-ball-panels)" />
      <circle cx={c.x} cy={c.y} r={r} fill="url(#v2-ball-shine)" />
      <circle data-ball="" cx={c.x} cy={c.y} r={r} fill="none" stroke="black" strokeWidth={0.1} />
    </g>
  );
}
