import { memo } from "react";
import dims from "../../utils/pitchGeometry.json";
import { COS, GROUND_MATRIX, project } from "../../utils/v2Projection";
import { PITCH_COLORS } from "../../utils/teamColors";
import PlayerMarker, { PLAYER_R, PlayerNumber, ReliefDefs } from "./PlayerMarker";
import BallMarker from "./BallMarker";
import { WAVE_AMPLITUDE_M, WAVE_CORNER_M } from "../../utils/v2NetWave";

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
// Ticket v2-ecran-match/05 (constantes validées par le propriétaire le 18/11/2026, spec du chantier §2.2) : plus de piste
// rouge ni de cadre ; pelouse de 3 m autour des lignes sur un sol sombre qui prolonge le fond de l'écran ; gazon sobre
// (PITCH_COLORS) ; vignette légère et un seul dégradé de profondeur. Coordonnées et projection inchangées : seul le
// viewBox est recadré.
const MARGIN = 3; // bord de pelouse autour des lignes (m ; 6 m avant EM-05)
const STRIPES = 18; // bandes de tonte sur la longueur
const FLOOR = "#0E141B"; // sol sombre autour de la pelouse
const VIGNETTE = 0.08; // assombrissement maximal des bords du gazon
const DEPTH_SHADE = 0.06; // côté lointain (y = 0) plus sombre que le côté proche
// Lignes : 1,5 px à l'écran quelle que soit la taille (trait non mis à l'échelle) ; en mètres, 0,12 m ne ferait que
// 0,45 px sur un téléphone en paysage.
const LINE = { fill: "none", stroke: "rgba(255,255,255,0.85)", strokeWidth: 1.5, vectorEffect: "non-scaling-stroke" };

// Bancs (ticket v2-ecran-match/06, constantes validées par le propriétaire le 18/11/2026) : zone de 4,5 m sous la pelouse
// (12 m de sol avant), bancs au milieu de cette zone, contour à la couleur de l'équipe.
const BENCH_ZONE = 4.5; // zone des bancs sous la pelouse (m)
const BENCH_Y = W + MARGIN + BENCH_ZONE / 2; // axe des bancs (m ; W + 11 avant EM-06)
const FLOOR_BOTTOM = W + MARGIN + BENCH_ZONE; // bas du dessin (m ; W + 15 avant EM-06)
// Remplaçants qui s'échauffent : sur l'herbe, entre la ligne de touche et le bas de la pelouse (W + 3 m).
const WARM_LANES = [0.7, 1.4, 2.1]; // couloirs au-delà de la ligne de touche (m ; 1,5 / 2,9 / 4,3 avant EM-06)
const SUB_R = 0.75; // rond d'un remplaçant, assis ou à l'échauffement (m ; 0,9 à l'échauffement avant EM-06)
const BENCH_GAP = 4; // des bancs à la ligne médiane (m)
const SEAT = 1.6; // largeur d'un siège (m)
const WARMING_UP = 3; // remplaçants de champ qui s'échauffent en 2e période

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
        <rect x={x0} y={BENCH_Y - 1.6} width={length} height={3.2} rx={0.6} fill="rgba(20,24,30,0.85)" style={{ stroke: color }} strokeWidth={0.12} />
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
            <circle cx={c.x} cy={c.y} r={SUB_R} style={{ fill: color }} opacity={0.85} stroke="rgba(0,0,0,0.4)" strokeWidth={0.08} />
            <PlayerNumber x={c.x} y={c.y} value={p.number} team={side < 0 ? "home" : "away"} size={0.9} />
            <title>{`${p.number} ${p.name} (${p.poste})`}</title>
          </g>
        );
      })}
      {warmers.map((p, i) => {
        // va-et-vient sur 12 m, chacun décalé, sur l'herbe entre la ligne de touche et le bas de la pelouse
        const phase = seconds * 0.35 + i * 2.1;
        const c = project(L / 2 + side * (24 + 6 + 6 * Math.sin(phase)), W + WARM_LANES[i]);
        return (
          <g key={p.name}>
            <circle cx={c.x} cy={c.y} r={SUB_R} style={{ fill: color }} opacity={0.75} stroke="rgba(0,0,0,0.4)" strokeWidth={0.08} />
            <PlayerNumber x={c.x} y={c.y} value={p.number} team={side < 0 ? "home" : "away"} size={1} />
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
const FACING_TICK = 1.0; // trait d'orientation : longueur au-delà du rond, dans le sens du corps (m ; ticket v2-realisme/07a)
// Le rond d'un joueur est dessiné à la hauteur de sa taille : sans cela il recouvrirait son ombre. Valeur validée par
// le propriétaire le 06/11/2026 ; si l'ombre est trop discrète sur téléphone, jouer sur son opacité, pas sur cette hauteur.
const PLAYER_LIFT = 1.8;
const SHADOW_K = 0.8; // ombre d'un joueur : ovale de rayon 0,8 × celui du rond (validé le 04/11/2026)
const SHADOW_OPACITY = 0.25;
const CROSSBAR = 2.44; // hauteur de la barre transversale (m)
const BALL_R = 0.5; // ballon au sol (m ; 0,4 avant le ticket v2-ecran-match/07, validé par le propriétaire le 18/11/2026)
const BALL_AIR_R = 0.6;
const BALL_AIR_Z = 1; // hauteur fixe d'un ballon aérien, jusqu'au ticket 02b (vraie hauteur à l'écran)

// But en volume (`x` : ligne de but, `out` : -1 côté x = 0, 1 côté x = L), tout par la projection.
// La caméra ne tourne qu'autour de l'axe x : le plan du cadre (x constant) est vu par la tranche, poteaux et barre
// tombent sur la ligne de but. Ce qui rend la hauteur lisible, c'est la cage : toit du filet à 2,44 m et filets
// latéraux, qui s'étendent en x sur la profondeur du filet (rouverture du 09/11/2026).
// `mid`, `corner` : recul du fond du filet (m) au milieu et aux coins, pendant l'ondulation d'un but (ticket
// v2-ecran-match/21b) ; 0 le reste du temps (valeurs simples : la mémoïsation tient tant que le filet est immobile).
// Le toit devient un pentagone dont le milieu du fond recule davantage ; filets latéraux et toit suivent le fond.
const GoalFrame = memo(function GoalFrame({ x, out, mid = 0, corner = 0 }) {
  const ys = [W / 2 - GOAL_WIDTH / 2, W / 2 + GOAL_WIDTH / 2];
  const back = x + out * (NET + corner);
  const backMid = x + out * (NET + mid);
  const pts = (...p) => p.map(([px, py, pz]) => project(px, py, pz)).map((q) => `${q.x},${q.y}`).join(" ");
  const net = { fill: "url(#v2-net)", stroke: "rgba(255,255,255,0.7)", strokeWidth: 0.1, strokeLinejoin: "round" };
  const [foot0, foot1] = ys.map((y) => project(x, y));
  const [top0, top1] = ys.map((y) => project(x, y, CROSSBAR));
  const stroke = { stroke: "white", strokeWidth: 0.3, strokeLinecap: "round" };
  return (
    <g style={{ pointerEvents: "none" }}>
      {/* filet latéral du fond, toit, filet latéral de devant (vers la caméra), du plus lointain au plus proche */}
      <polygon points={pts([x, ys[0], 0], [back, ys[0], 0], [back, ys[0], CROSSBAR], [x, ys[0], CROSSBAR])} {...net} />
      <polygon points={pts([x, ys[0], CROSSBAR], [back, ys[0], CROSSBAR], [backMid, W / 2, CROSSBAR], [back, ys[1], CROSSBAR], [x, ys[1], CROSSBAR])} {...net} />
      <polygon points={pts([x, ys[1], 0], [back, ys[1], 0], [back, ys[1], CROSSBAR], [x, ys[1], CROSSBAR])} {...net} />
      <line x1={foot0.x} y1={foot0.y} x2={top0.x} y2={top0.y} {...stroke} />
      <line x1={foot1.x} y1={foot1.y} x2={top1.x} y2={top1.y} {...stroke} />
      <line x1={top0.x} y1={top0.y} x2={top1.x} y2={top1.y} {...stroke} />
    </g>
  );
});

// Recul du fond du filet en `x` pendant l'ondulation (0 pour l'autre filet et hors ondulation).
const bulge = (wave, x) => (wave && wave.x === x ? { mid: WAVE_AMPLITUDE_M * wave.k, corner: WAVE_CORNER_M * wave.k } : {});

// Filet des buts, pelouse et lignes : immobiles, dessinés une seule fois.
const PitchGround = memo(function PitchGround() {
  const stripe = L / STRIPES;
  return (
    <>
      <defs>
        <radialGradient id="v2-vignette" cx="0.5" cy="0.5" r="0.5">
          <stop offset="0.6" stopColor="#000" stopOpacity={0} />
          <stop offset="1" stopColor="#000" stopOpacity={VIGNETTE} />
        </radialGradient>
        <linearGradient id="v2-depth" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#000" stopOpacity={DEPTH_SHADE} />
          <stop offset="1" stopColor="#000" stopOpacity={0} />
        </linearGradient>
        <ReliefDefs />
        <pattern id="v2-net" width={0.5} height={0.5} patternUnits="userSpaceOnUse">
          <rect width={0.5} height={0.5} fill="rgba(255,255,255,0.15)" />
          <path d="M 0 0 L 0.5 0 M 0 0 L 0 0.5" stroke="rgba(255,255,255,0.6)" strokeWidth={0.05} />
        </pattern>
      </defs>
      {/* 1. pelouse et lignes : à plat, écrasées par la même projection (z = 0) */}
      <g transform={GROUND_MATRIX}>
        <rect x={-MARGIN} y={-MARGIN} width={L + 2 * MARGIN} height={FLOOR_BOTTOM + MARGIN} fill={FLOOR} />
        <rect x={-MARGIN} y={-MARGIN} width={L + 2 * MARGIN} height={W + 2 * MARGIN} fill={PITCH_COLORS[0]} />
        {Array.from({ length: STRIPES }, (_, i) => (
          <rect key={i} x={i * stripe} y={-MARGIN} width={stripe} height={W + 2 * MARGIN} fill={i % 2 ? PITCH_COLORS[1] : PITCH_COLORS[0]} />
        ))}
        <rect x={-MARGIN} y={-MARGIN} width={L + 2 * MARGIN} height={W + 2 * MARGIN} fill="url(#v2-depth)" />
        <rect x={-MARGIN} y={-MARGIN} width={L + 2 * MARGIN} height={W + 2 * MARGIN} fill="url(#v2-vignette)" />

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

// `className` : taille de l'élément (l'écran de match lui donne toute sa case, ticket v2-ecran-match/04) ; le dessin garde
// ses proportions et se centre dans la boîte (preserveAspectRatio par défaut).
// `ballLook` : aspect du ballon (ticket v2-ecran-match/21a) : `dir` (direction du déplacement dans le repère de la vue),
// `speed` (m/s) et `playbackSpeed` (figement du motif), `trail` (longueur de la traînée, m) ; absent = motif figé, sans traînée.
// `wave` : ondulation du filet sur un but (ticket v2-ecran-match/21b, `utils/v2NetWave.js`) : `{ x, k }`, x = ligne de
// but du filet concerné dans le repère de la vue ; null le reste du temps.
export default function V2Pitch({ tick, seconds, warmUpFromS, numbers, lineups, selected, onSelect, ballLook = null, wave = null, className = "w-full max-w-4xl rounded-lg" }) {
  const height = (FLOOR_BOTTOM + MARGIN) * COS;
  // du fond (y petit) vers l'avant : le joueur le plus proche de la caméra recouvre le plus lointain
  const players = [...tick.players]
    .sort((a, b) => a.y - b.y)
    .map((p) => {
      // cap du corps (ticket v2-realisme/07a) : trait du bord du rond vers l'avant, posé au sol puis projeté
      const rad = ((p.facing ?? 0) * Math.PI) / 180;
      const reach = PLAYER_R + FACING_TICK;
      return {
        ...p,
        ground: project(p.x, p.y),
        body: project(p.x, p.y, PLAYER_LIFT),
        nose: project(p.x + Math.cos(rad) * reach, p.y + Math.sin(rad) * reach, PLAYER_LIFT),
      };
    });
  const holder = players.find((p) => p.name === tick.ball.holder);
  const air = tick.ball.mode === "aérien";
  const ballGround = project(tick.ball.x, tick.ball.y);
  const ballR = air ? BALL_AIR_R : BALL_R;
  // bancs : immobiles avant l'échauffement, inutile de leur passer le temps qui court
  const benchSeconds = seconds >= warmUpFromS ? seconds : 0;
  return (
    <svg
      viewBox={`${-MARGIN} ${-MARGIN * COS} ${L + 2 * MARGIN} ${height}`}
      className={className}
      style={{ aspectRatio: `${L + 2 * MARGIN} / ${height}` }}
    >
      <PitchGround />
      {lineups && <Bench lineup={lineups.home} side={-1} color="var(--team-home)" seconds={benchSeconds} warmUpFromS={warmUpFromS} />}
      {lineups && <Bench lineup={lineups.away} side={1} color="var(--team-away)" seconds={benchSeconds} warmUpFromS={warmUpFromS} />}

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

      {/* 3. joueurs, triés du fond vers l'avant : vrais cercles, avec le trait de leur cap (ticket v2-realisme/07a) */}
      {players.map((p) => (
        <PlayerMarker key={p.name} player={p} number={numbers[p.name]} selected={p.name === selected} onSelect={onSelect} />
      ))}

      {/* 4. buts en hauteur */}
      <GoalFrame x={0} out={-1} {...bulge(wave, 0)} />
      <GoalFrame x={L} out={1} {...bulge(wave, L)} />

      {/* 5. ballon : plus gros et remonté s'il est aérien (hauteur fixe d'un mètre, provisoire) ; atténué s'il est mort ;
          motif qui roule et traînée de vitesse (ticket v2-ecran-match/21a) */}
      <BallMarker
        ground={tick.ball}
        z={air ? BALL_AIR_Z : 0}
        r={ballR}
        dead={tick.ball.dead}
        dir={ballLook?.dir ?? null}
        speed={ballLook?.speed ?? Infinity}
        playbackSpeed={ballLook?.playbackSpeed ?? 1}
        trail={ballLook?.trail ?? 0}
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
