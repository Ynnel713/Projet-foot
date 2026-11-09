import { memo } from "react";
import dims from "../../utils/pitchGeometry.json";
import { COS, GROUND_MATRIX, project } from "../../utils/v2Projection";

// Terrain simple, réutilise seulement les COTES réelles de la V1 (pitchGeometry.json, dérivé de
// ligue1sim.pitch_geometry) -- pas le composant PitchField.jsx lui-même, dont l'orientation est
// couplée à l'historique spécifique de l'écran PitchView (voir docs/TRD_V2.md, D-V01 : module V2
// séparé). viewBox en mètres réels : les positions de la trace (mêmes mètres) s'y posent sans
// conversion.
// Ticket v2-ecran-match/01 : déplacé depuis routes/V2Match.jsx ; pelouse, marquages, buts et bancs immobiles mémoïsés.
const L = dims.pitch_length_m;
const W = dims.pitch_width_m;
const GOAL_WIDTH = dims.goal_width_m;
const CENTER_CIRCLE_R = dims.center_circle_radius_m;
const PA_DEPTH = dims.penalty_area_depth_m;
const PA_WIDTH = dims.penalty_area_width_m;
const GA_DEPTH = dims.goal_area_depth_m;
const GA_WIDTH = dims.goal_area_width_m;
const SPOT = dims.penalty_spot_distance_m;
const ARC_R = dims.penalty_arc_radius_m;
const NET = dims.goal_net_depth_m;
const CORNER_R = dims.corner_arc_radius_m;

// Habillage inspiré d'une vue aérienne de stade (retour du propriétaire, 24/10/2026) : pelouse tondue en bandes,
// marquages complets, buts avec filets, bord de terrain et piste. Dessiné en SVG plutôt qu'en photo : la photo est
// prise en légère perspective, les joueurs (positions en mètres) ne tomberaient pas sur ses lignes.
const MARGIN = 6; // bord de pelouse autour des lignes (m)
const TRACK = 2; // piste autour du bord (m)
const STRIPES = 18; // bandes de tonte sur la longueur
const LINE = { fill: "none", stroke: "rgba(255,255,255,0.9)", strokeWidth: 0.15 };

const BENCH_ZONE = 7; // bande sous la piste, côté tribune principale, où sont les bancs (m)
const BENCH_Y = W + MARGIN + TRACK + 3; // axe des bancs
const BENCH_GAP = 4; // des bancs à la ligne médiane (m)
const SEAT = 1.6; // largeur d'un siège (m)
const WARMING_UP = 3; // remplaçants de champ qui s'échauffent en 2e période

function PlayerNumber({ x, y, value, size = 1.4 }) {
  if (value == null) return null;
  return (
    <text
      x={x}
      y={y}
      textAnchor="middle"
      dominantBaseline="central"
      fontSize={size}
      fontWeight="bold"
      fill="white"
      stroke="rgba(0,0,0,0.6)"
      strokeWidth={0.2}
      paintOrder="stroke"
      style={{ pointerEvents: "none" }}
    >
      {value}
    </text>
  );
}

// Banc d'une équipe sous le terrain (`side` -1 : à gauche de la ligne médiane, 1 : à droite) : entraîneur et
// remplaçants assis ; en 2e période, quelques remplaçants de champ trottinent le long de la ligne de touche, de leur
// côté du terrain (mouvement de va-et-vient purement décoratif, fonction du temps de match lu).
// échauffement à partir du coup d'envoi de la 2e période, après le temps additionnel de la 1re (ticket coach/03)
const Bench = memo(function Bench({ lineup, side, color, seconds, warmUpFromS }) {
  const warmers = seconds >= warmUpFromS ? lineup.bench.filter((p) => p.poste !== "GK").slice(0, WARMING_UP) : [];
  const seated = lineup.bench.filter((p) => !warmers.includes(p));
  const seats = seated.length + 1; // + l'entraîneur, au bout côté ligne médiane
  const length = seats * SEAT + 1;
  const x0 = side < 0 ? L / 2 - BENCH_GAP - length : L / 2 + BENCH_GAP;
  const seatX = (i) => (side < 0 ? x0 + length - 0.5 - SEAT * (i + 0.5) : x0 + 0.5 + SEAT * (i + 0.5));
  // sièges et remplaçants : ronds et chiffres projetés (jamais écrasés) ; les bancs eux-mêmes sont à plat
  const seat = project(seatX(0), BENCH_Y);
  return (
    <g>
      <g transform={GROUND_MATRIX}>
        <rect x={x0} y={BENCH_Y - 1.6} width={length} height={3.2} rx={0.6} fill="rgba(20,24,30,0.85)" stroke="rgba(255,255,255,0.5)" strokeWidth={0.12} />
      </g>
      <g>
        <rect x={seat.x - 0.8} y={seat.y - 0.8} width={1.6} height={1.6} rx={0.3} fill="#222" stroke="white" strokeWidth={0.12} />
        <text x={seat.x} y={seat.y} textAnchor="middle" dominantBaseline="central" fontSize={1} fill="white" fontWeight="bold">
          E
        </text>
        <title>{`Entraîneur${lineup.coach ? ` : ${lineup.coach}` : ""}`}</title>
      </g>
      {seated.map((p, i) => {
        const c = project(seatX(i + 1), BENCH_Y);
        return (
          <g key={p.name}>
            <circle cx={c.x} cy={c.y} r={0.75} fill={color} opacity={0.85} stroke="rgba(0,0,0,0.4)" strokeWidth={0.08} />
            <PlayerNumber x={c.x} y={c.y} value={p.number} size={0.9} />
            <title>{`${p.number} ${p.name} (${p.poste})`}</title>
          </g>
        );
      })}
      {warmers.map((p, i) => {
        // va-et-vient sur 12 m, chacun décalé, entre la ligne de touche et la piste
        const phase = seconds * 0.35 + i * 2.1;
        const c = project(L / 2 + side * (24 + 6 + 6 * Math.sin(phase)), W + 1.5 + i * 1.4);
        return (
          <g key={p.name}>
            <circle cx={c.x} cy={c.y} r={0.9} fill={color} opacity={0.75} stroke="rgba(0,0,0,0.4)" strokeWidth={0.08} />
            <PlayerNumber x={c.x} y={c.y} value={p.number} size={1} />
            <title>{`${p.number} ${p.name} s'échauffe`}</title>
          </g>
        );
      })}
    </g>
  );
});

// Arc de la surface (hors surface uniquement) : intersection du cercle de rayon ARC_R autour du point de penalty
// avec la ligne de surface.
const ARC_DY = Math.sqrt(ARC_R ** 2 - (PA_DEPTH - SPOT) ** 2);

function GoalEnd({ flip }) {
  // Dessin côté x=0 ; `flip` le recopie en miroir côté x=L.
  const y0 = W / 2;
  return (
    <g transform={flip ? `translate(${L} 0) scale(-1 1)` : undefined}>
      <rect x={0} y={y0 - PA_WIDTH / 2} width={PA_DEPTH} height={PA_WIDTH} {...LINE} />
      <rect x={0} y={y0 - GA_WIDTH / 2} width={GA_DEPTH} height={GA_WIDTH} {...LINE} />
      <circle cx={SPOT} cy={y0} r={0.25} fill="white" />
      <path d={`M ${PA_DEPTH} ${y0 - ARC_DY} A ${ARC_R} ${ARC_R} 0 0 1 ${PA_DEPTH} ${y0 + ARC_DY}`} {...LINE} />
    </g>
  );
}

// Joueurs, buts et ballon sur la caméra inclinée (ticket v2-hauteur-ballon/01).
const PLAYER_R = 1.3; // rayon du rond d'un joueur (m)
// Le rond d'un joueur est dessiné à la hauteur de sa taille : sans cela il recouvrirait son ombre. Valeur validée par
// le propriétaire le 06/11/2026 ; si l'ombre est trop discrète sur téléphone, jouer sur son opacité, pas sur cette hauteur.
const PLAYER_LIFT = 1.8;
const SHADOW_K = 0.8; // ombre d'un joueur : ovale de rayon 0,8 × celui du rond (validé le 04/11/2026)
const SHADOW_OPACITY = 0.25;
const CROSSBAR = 2.44; // hauteur de la barre transversale (m)
const BALL_R = 0.4;
const BALL_AIR_R = 0.6;
const BALL_AIR_Z = 1; // hauteur fixe d'un ballon aérien, jusqu'au ticket 02b (vraie hauteur à l'écran)

// But en volume (`x` : ligne de but, `out` : -1 côté x = 0, 1 côté x = L), tout par la projection.
// La caméra ne tourne qu'autour de l'axe x : le plan du cadre (x constant) est vu par la tranche, poteaux et barre
// tombent sur la ligne de but. Ce qui rend la hauteur lisible, c'est la cage : toit du filet à 2,44 m et filets
// latéraux, qui s'étendent en x sur la profondeur du filet (rouverture du 09/11/2026).
const GoalFrame = memo(function GoalFrame({ x, out }) {
  const ys = [W / 2 - GOAL_WIDTH / 2, W / 2 + GOAL_WIDTH / 2];
  const back = x + out * NET;
  const pts = (...p) => p.map(([px, py, pz]) => project(px, py, pz)).map((q) => `${q.x},${q.y}`).join(" ");
  const net = { fill: "url(#v2-net)", stroke: "rgba(255,255,255,0.7)", strokeWidth: 0.1, strokeLinejoin: "round" };
  const [foot0, foot1] = ys.map((y) => project(x, y));
  const [top0, top1] = ys.map((y) => project(x, y, CROSSBAR));
  const stroke = { stroke: "white", strokeWidth: 0.3, strokeLinecap: "round" };
  return (
    <g style={{ pointerEvents: "none" }}>
      {/* filet latéral du fond, toit, filet latéral de devant (vers la caméra), du plus lointain au plus proche */}
      <polygon points={pts([x, ys[0], 0], [back, ys[0], 0], [back, ys[0], CROSSBAR], [x, ys[0], CROSSBAR])} {...net} />
      <polygon points={pts([x, ys[0], CROSSBAR], [back, ys[0], CROSSBAR], [back, ys[1], CROSSBAR], [x, ys[1], CROSSBAR])} {...net} />
      <polygon points={pts([x, ys[1], 0], [back, ys[1], 0], [back, ys[1], CROSSBAR], [x, ys[1], CROSSBAR])} {...net} />
      <line x1={foot0.x} y1={foot0.y} x2={top0.x} y2={top0.y} {...stroke} />
      <line x1={foot1.x} y1={foot1.y} x2={top1.x} y2={top1.y} {...stroke} />
      <line x1={top0.x} y1={top0.y} x2={top1.x} y2={top1.y} {...stroke} />
    </g>
  );
});

// Filet des buts, pelouse et lignes : immobiles, dessinés une seule fois.
const PitchGround = memo(function PitchGround() {
  const pad = MARGIN + TRACK;
  const stripe = L / STRIPES;
  return (
    <>
      <defs>
        <pattern id="v2-net" width={0.5} height={0.5} patternUnits="userSpaceOnUse">
          <rect width={0.5} height={0.5} fill="rgba(255,255,255,0.15)" />
          <path d="M 0 0 L 0.5 0 M 0 0 L 0 0.5" stroke="rgba(255,255,255,0.6)" strokeWidth={0.05} />
        </pattern>
      </defs>
      {/* 1. pelouse et lignes : à plat, écrasées par la même projection (z = 0) */}
      <g transform={GROUND_MATRIX}>
        <rect x={-pad} y={-pad} width={L + 2 * pad} height={W + 2 * pad + BENCH_ZONE} fill="#5a5f66" />
        <rect x={-pad} y={-pad} width={L + 2 * pad} height={W + 2 * pad} fill="#9c4a3c" />
        <rect x={-MARGIN} y={-MARGIN} width={L + 2 * MARGIN} height={W + 2 * MARGIN} fill="#2f7d32" />
        {Array.from({ length: STRIPES }, (_, i) => (
          <rect key={i} x={i * stripe} y={-MARGIN} width={stripe} height={W + 2 * MARGIN} fill={i % 2 ? "#3a8f3c" : "#2f7d32"} />
        ))}

        <rect x={0} y={0} width={L} height={W} {...LINE} />
        <line x1={L / 2} y1={0} x2={L / 2} y2={W} {...LINE} />
        <circle cx={L / 2} cy={W / 2} r={CENTER_CIRCLE_R} {...LINE} />
        <circle cx={L / 2} cy={W / 2} r={0.3} fill="white" />
        {[
          [0, 0, 0],
          [L, 0, 90],
          [L, W, 180],
          [0, W, 270],
        ].map(([x, y, rot]) => (
          <path key={rot} d={`M ${CORNER_R} 0 A ${CORNER_R} ${CORNER_R} 0 0 1 0 ${CORNER_R}`} transform={`translate(${x} ${y}) rotate(${rot})`} {...LINE} />
        ))}
        <GoalEnd />
        <GoalEnd flip />
      </g>
    </>
  );
});

export default function V2Pitch({ tick, seconds, warmUpFromS, numbers, lineups, selected, onSelect }) {
  const pad = MARGIN + TRACK;
  const height = (W + 2 * pad + BENCH_ZONE) * COS;
  // du fond (y petit) vers l'avant : le joueur le plus proche de la caméra recouvre le plus lointain
  const players = [...tick.players]
    .sort((a, b) => a.y - b.y)
    .map((p) => ({ ...p, ground: project(p.x, p.y), body: project(p.x, p.y, PLAYER_LIFT) }));
  const holder = players.find((p) => p.name === tick.ball.holder);
  const air = tick.ball.mode === "aérien";
  const ballGround = project(tick.ball.x, tick.ball.y);
  const ball = project(tick.ball.x, tick.ball.y, air ? BALL_AIR_Z : 0);
  const ballR = air ? BALL_AIR_R : BALL_R;
  // bancs : immobiles avant l'échauffement, inutile de leur passer le temps qui court
  const benchSeconds = seconds >= warmUpFromS ? seconds : 0;
  return (
    <svg
      viewBox={`${-pad} ${-pad * COS} ${L + 2 * pad} ${height}`}
      className="w-full max-w-4xl rounded-lg"
      style={{ aspectRatio: `${L + 2 * pad} / ${height}` }}
    >
      <PitchGround />
      {lineups && <Bench lineup={lineups.home} side={-1} color="#4f8ef7" seconds={benchSeconds} warmUpFromS={warmUpFromS} />}
      {lineups && <Bench lineup={lineups.away} side={1} color="#e0b84a" seconds={benchSeconds} warmUpFromS={warmUpFromS} />}

      {/* 2. ombres au sol */}
      {players.map((p) => (
        <ellipse
          key={`shadow-${p.name}`}
          cx={p.ground.x}
          cy={p.ground.y}
          rx={PLAYER_R * SHADOW_K}
          ry={PLAYER_R * SHADOW_K * COS}
          fill="black"
          opacity={SHADOW_OPACITY}
          style={{ pointerEvents: "none" }}
        />
      ))}
      {air && (
        <ellipse
          cx={ballGround.x}
          cy={ballGround.y}
          rx={ballR}
          ry={ballR * COS}
          fill="black"
          opacity={0.3}
          style={{ pointerEvents: "none" }}
        />
      )}

      {/* 3. joueurs, triés du fond vers l'avant : vrais cercles */}
      {players.map((p) => (
        <g key={p.name} onClick={() => onSelect(p.name === selected ? null : p.name)} style={{ cursor: "pointer" }}>
          <circle
            cx={p.body.x}
            cy={p.body.y}
            r={PLAYER_R}
            fill={p.team === "home" ? "#4f8ef7" : "#e0b84a"}
            stroke={p.name === selected ? "white" : "rgba(0,0,0,0.4)"}
            strokeWidth={p.name === selected ? 0.4 : 0.1}
          />
          <PlayerNumber x={p.body.x} y={p.body.y} value={numbers[p.name]} />
        </g>
      ))}

      {/* 4. buts en hauteur */}
      <GoalFrame x={0} out={-1} />
      <GoalFrame x={L} out={1} />

      {/* 5. ballon : plus gros et remonté s'il est aérien (hauteur fixe d'un mètre, provisoire) ; atténué s'il est mort */}
      <circle
        cx={ball.x}
        cy={ball.y}
        r={ballR}
        fill="white"
        stroke="black"
        strokeWidth={0.1}
        opacity={tick.ball.dead ? 0.6 : 1}
        style={{ pointerEvents: "none" }}
      />

      {/* 6. nom du porteur, sous son rond ; le contour sombre le garde lisible sur la pelouse comme sur les lignes */}
      {holder && (
        <text
          x={holder.body.x}
          y={holder.body.y + 3.2}
          textAnchor="middle"
          fontSize={1.8}
          fontWeight="bold"
          fill="white"
          stroke="black"
          strokeWidth={0.35}
          paintOrder="stroke"
          style={{ pointerEvents: "none" }}
        >
          {holder.name}
        </text>
      )}
    </svg>
  );
}
