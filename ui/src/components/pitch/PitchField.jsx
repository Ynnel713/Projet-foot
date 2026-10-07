import dims from "../../utils/pitchGeometry.json";

// Pelouse réaliste (tondue en bandes, lignes officielles à l'échelle) pour
// l'écran match (PitchView) -- remplace le rectangle vert plat d'origine
// (retour terrain du 28/09/2026 : "le terrain n'est pas beau"). Cotes FIFA en
// mètres lues dans ui/src/utils/pitchGeometry.json, DÉRIVÉ de
// src/ligue1sim/pitch_geometry.py (source unique, Phase 5 sous-étape 1 ; ne
// pas les redéfinir ici -- tests/test_pitch_geometry.py vérifie l'égalité).
// Terrain HORIZONTAL comme le reste de PitchView -- but domicile à gauche
// (x=0), but extérieur à droite (x=L).
const L = dims.pitch_length_m;
const W = dims.pitch_width_m;
const PAD = 3; // marge autour du terrain (pour dessiner les cages qui dépassent)
const STRIPES = 18;
const GRASS_A = "#2d8a4e";
const GRASS_B = "#26793f";
const OUT_OF_BOUNDS = "#1c5a30";
const LINE = "rgba(255,255,255,0.92)";
const LINE_W = 0.35; // épaisseur de TRACÉ (visibilité), pas une cote réglementaire

const PEN_DEPTH = dims.penalty_area_depth_m;
const PEN_WIDTH = dims.penalty_area_width_m;
const SIX_DEPTH = dims.goal_area_depth_m;
const SIX_WIDTH = dims.goal_area_width_m;
const SPOT_DIST = dims.penalty_spot_distance_m;
const CIRCLE_R = dims.center_circle_radius_m;
const ARC_R = dims.penalty_arc_radius_m;
const GOAL_WIDTH = dims.goal_width_m;
const GOAL_DEPTH = dims.goal_net_depth_m;
const CORNER_R = dims.corner_arc_radius_m;

// Arc de surface de réparation -- portion du cercle de rayon ARC_R,
// centré sur le point de penalty, visible hors de la surface : les deux
// points où ce cercle croise la ligne de surface, à `depth` du point de
// penalty (16.5 - 11 = 5.5 m).
function penaltyArc(spotX, boxEdgeX, midY, sweepFlag) {
  const depth = Math.abs(boxEdgeX - spotX);
  const half = Math.sqrt(ARC_R * ARC_R - depth * depth);
  return `M ${boxEdgeX} ${midY - half} A ${ARC_R} ${ARC_R} 0 0 ${sweepFlag} ${boxEdgeX} ${midY + half}`;
}

function GoalEnd({ side }) {
  const dir = side === "home" ? 1 : -1;
  const goalLineX = side === "home" ? 0 : L;
  const boxEdgeX = side === "home" ? PEN_DEPTH : L - PEN_DEPTH;
  const sixEdgeX = side === "home" ? SIX_DEPTH : L - SIX_DEPTH;
  const spotX = side === "home" ? SPOT_DIST : L - SPOT_DIST;
  const midY = W / 2;

  return (
    <g fill="none" stroke={LINE} strokeWidth={LINE_W}>
      <rect x={side === "home" ? 0 : boxEdgeX} y={midY - PEN_WIDTH / 2} width={PEN_DEPTH} height={PEN_WIDTH} />
      <rect x={side === "home" ? 0 : sixEdgeX} y={midY - SIX_WIDTH / 2} width={SIX_DEPTH} height={SIX_WIDTH} />
      <circle cx={spotX} cy={midY} r={0.35} fill={LINE} stroke="none" />
      <path d={penaltyArc(spotX, boxEdgeX, midY, side === "home" ? 1 : 0)} />
      {/* cage, dépasse la ligne de but vers l'extérieur */}
      <rect
        x={side === "home" ? -GOAL_DEPTH : L}
        y={midY - GOAL_WIDTH / 2}
        width={GOAL_DEPTH}
        height={GOAL_WIDTH}
        strokeWidth={0.5}
      />
      {/* arcs de coin */}
      <path d={`M ${goalLineX} ${dir > 0 ? CORNER_R : W - CORNER_R} A ${CORNER_R} ${CORNER_R} 0 0 ${dir > 0 ? 0 : 1} ${goalLineX + dir * CORNER_R} ${dir > 0 ? 0 : W}`} />
      <path d={`M ${goalLineX} ${dir > 0 ? W - CORNER_R : CORNER_R} A ${CORNER_R} ${CORNER_R} 0 0 ${dir > 0 ? 1 : 0} ${goalLineX + dir * CORNER_R} ${dir > 0 ? W : 0}`} />
    </g>
  );
}

// Terrain VERTICAL (portrait, 68 x 105) : le dessin ci-dessous reste en coordonnées horizontales (longueur L, largeur W) ; il est
// pivoté de 90° (but du domicile en HAUT, celui de l'extérieur en BAS) par le <g transform> qui enveloppe tout, et le viewBox est
// transposé. Comme le placement du moteur (domicile en haut, x latéral, y profondeur), les joueurs s'affichent sans permutation.
export default function PitchField() {
  const viewBox = `${-PAD} ${-PAD} ${W + PAD * 2} ${L + PAD * 2}`;
  const stripeWidth = L / STRIPES;

  return (
    <svg viewBox={viewBox} preserveAspectRatio="none" className="absolute inset-0 w-full h-full rounded-xl">
      <g transform={`translate(${W} 0) rotate(90)`}>
      <rect x={-PAD} y={-PAD} width={L + PAD * 2} height={W + PAD * 2} fill={OUT_OF_BOUNDS} />
      {Array.from({ length: STRIPES }, (_, i) => (
        <rect key={i} x={i * stripeWidth} y={0} width={stripeWidth} height={W} fill={i % 2 === 0 ? GRASS_A : GRASS_B} />
      ))}

      <g fill="none" stroke={LINE} strokeWidth={LINE_W}>
        <rect x={0} y={0} width={L} height={W} />
        <line x1={L / 2} y1={0} x2={L / 2} y2={W} />
        <circle cx={L / 2} cy={W / 2} r={CIRCLE_R} />
      </g>
      <circle cx={L / 2} cy={W / 2} r={0.35} fill={LINE} />

      <GoalEnd side="home" />
      <GoalEnd side="away" />
      </g>
    </svg>
  );
}
