import { RING_WIDTH_M } from "../../utils/teamColors";

// Marqueur d'un joueur sur le terrain V2 (ticket v2-ecran-match/07, constantes validées par le propriétaire le 18/11/2026) :
// rond à la couleur de l'équipe, anneau clair ou sombre (règle d'EM-03), numéro à contraste garanti, trait du cap
// (ticket v2-realisme/07a), anneau blanc épais quand le joueur est sélectionné. Rayon, anneau, ombre et sélection
// inchangés ; seul ajout, un relief léger : éclaircissement de 10 % en haut à gauche, limité à l'anneau extérieur du rond
// (de RELIEF_INNER du rayon au bord), jamais sous le numéro, pour que son contraste (≥ 4,5:1) reste celui d'EM-03.
export const PLAYER_R = 1.3; // rayon du rond d'un joueur (m)
const RELIEF = 0.1; // éclaircissement maximal, au bord haut gauche
const RELIEF_INNER = 0.75; // le relief commence à 75 % du rayon (un numéro à deux chiffres tient sous 0,93 m du centre)
const SELECTED_RING = 0.4; // anneau du joueur sélectionné (m)

// Dégradé et masque partagés par tous les marqueurs (un seul <defs>, coût de rendu borné), en unités de la boîte du rond.
export function ReliefDefs() {
  return (
    <>
      <linearGradient id="v2-relief" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0.15" stopColor="#fff" stopOpacity={RELIEF} />
        <stop offset="0.5" stopColor="#fff" stopOpacity={0} />
      </linearGradient>
      <mask id="v2-relief-ring" maskContentUnits="objectBoundingBox">
        <circle cx={0.5} cy={0.5} r={0.5} fill="white" />
        <circle cx={0.5} cy={0.5} r={0.5 * RELIEF_INNER} fill="black" />
      </mask>
    </>
  );
}

export function PlayerNumber({ x, y, value, team, size = 1.4 }) {
  if (value == null) return null;
  return (
    <text
      x={x}
      y={y}
      textAnchor="middle"
      dominantBaseline="central"
      fontSize={size}
      fontWeight="bold"
      strokeWidth={0.2}
      paintOrder="stroke"
      // encre et liseré de l'équipe (ticket v2-ecran-match/03)
      style={{ pointerEvents: "none", fill: `var(--team-${team}-ink)`, stroke: `var(--team-${team}-ink-edge)` }}
    >
      {value}
    </text>
  );
}

// `player` : joueur de l'image, avec ses points projetés `body` (centre du rond) et `nose` (bout du trait de cap).
export default function PlayerMarker({ player: p, number, selected, onSelect }) {
  return (
    <g onClick={() => onSelect(selected ? null : p.name)} style={{ cursor: "pointer" }}>
      <line
        x1={p.body.x}
        y1={p.body.y}
        x2={p.nose.x}
        y2={p.nose.y}
        stroke="white"
        strokeWidth={0.35}
        strokeLinecap="round"
        opacity={0.85}
        style={{ pointerEvents: "none" }}
      />
      <circle
        cx={p.body.x}
        cy={p.body.y}
        r={PLAYER_R}
        // couleur, anneau clair ou sombre (RING_WIDTH_M) de l'équipe ; joueur sélectionné : anneau blanc épais
        style={{ fill: `var(--team-${p.team})`, stroke: selected ? "white" : `var(--team-${p.team}-ring)` }}
        strokeWidth={selected ? SELECTED_RING : RING_WIDTH_M}
      />
      <circle
        data-relief=""
        cx={p.body.x}
        cy={p.body.y}
        r={PLAYER_R}
        fill="url(#v2-relief)"
        mask="url(#v2-relief-ring)"
        style={{ pointerEvents: "none" }}
      />
      <PlayerNumber x={p.body.x} y={p.body.y} value={number} team={p.team} />
    </g>
  );
}
