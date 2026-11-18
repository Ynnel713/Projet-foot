import { memo, useMemo } from "react";
import { L, halfStart } from "./trace";

// Match momentum : une barre par minute, vers le haut quand domicile pousse, vers le bas quand l'extérieur pousse.
// Poussée d'un instant = position du ballon dans la longueur (repère moteur : domicile attaque vers x croissant tout le
// match), accentuée près des buts, plus un bonus à l'équipe qui a le ballon ; moyenne sur la minute.
// ponytail : heuristique territoire + possession, sans les tirs (journal des décisions envoyé seulement en fin de
// calcul) ; à enrichir avec tirs et occasions si la courbe paraît trop plate.
const MOMENTUM_MINUTES = 90; // minimum : le temps additionnel allonge la frise (ticket v2-coach-et-gestion-de-match/03)
const POSSESSION_BONUS = 0.15;

function momentumByMinute(trace) {
  const n = Math.max(MOMENTUM_MINUTES, Math.ceil(trace.ticks.at(-1)?.minute ?? 0));
  const sums = new Array(n).fill(0);
  const counts = new Array(n).fill(0);
  for (const t of trace.ticks) {
    const m = Math.min(n - 1, Math.floor(t.minute));
    const dx = (t.ball.x - L / 2) / (L / 2);
    const holderTeam = t.ball.holder && t.players.find((p) => p.name === t.ball.holder)?.team;
    sums[m] += dx * Math.abs(dx) + (holderTeam === "home" ? POSSESSION_BONUS : holderTeam === "away" ? -POSSESSION_BONUS : 0);
    counts[m] += 1;
  }
  return sums.map((v, m) => (counts[m] ? v / counts[m] : null));
}

// `played` : minutes entamées (barres affichées : m < played) ; `goalsShown` : buts déjà vus (la trace les range par
// minute). Deux entiers plutôt que l'instant lu : le composant ne se redessine qu'au changement de minute ou à un but
// (ticket v2-ecran-match/01).
function Momentum({ trace, played, goalsShown }) {
  // recalculé quand de nouvelles images arrivent (une fois par seconde), pas à chaque image affichée
  const values = useMemo(() => momentumByMinute(trace), [trace]);
  const X = 4; // largeur d'une minute (unités du viewBox)
  const H = 14; // demi-hauteur
  // échelle sur les minutes déjà jouées seulement : la courbe ne trahit rien de la suite
  const scale = H / Math.max(0.2, ...values.map((v, m) => (m < played ? Math.abs(v ?? 0) : 0)));
  const goals = trace.goals.slice(0, goalsShown);
  const width = values.length * X;
  return (
    // h-full : la frise se contracte avec la zone basse de l'écran ; 72 px au plus (ticket v2-ecran-match/04, décision du
    // propriétaire du 18/11/2026 : zone basse compacte, le terrain ne doit rien perdre à 1280 et 1366 px)
    <svg viewBox={`-2 -6 ${width + 4} ${2 * H + 12}`} className="w-full h-full" style={{ maxHeight: 72 }}>
      <title>Match momentum</title>
      <rect x={0} y={0} width={width} height={H} style={{ fill: "var(--team-home-ui)" }} fillOpacity={0.12} />
      <rect x={0} y={H} width={width} height={H} style={{ fill: "var(--team-away-ui)" }} fillOpacity={0.12} />
      {values.map((v, m) =>
        v == null || m >= played ? null : (
          <rect
            key={m}
            x={m * X + 0.4}
            width={X - 0.8}
            y={v > 0 ? H - v * scale : H}
            height={Math.abs(v) * scale}
            style={{ fill: v > 0 ? "var(--team-home-ui)" : "var(--team-away-ui)" }}
          />
        ),
      )}
      <line x1={0} y1={H} x2={width} y2={H} stroke="rgba(255,255,255,0.3)" strokeWidth={0.2} />
      <line x1={halfStart(trace) * X} y1={0} x2={halfStart(trace) * X} y2={2 * H} stroke="white" strokeWidth={0.6} />
      {goals.map((g, i) => (
        <text
          key={i}
          x={g.minute * X}
          y={g.team === "home" ? -3 : 2 * H + 3}
          textAnchor="middle"
          dominantBaseline="central"
          fontSize={5}
        >
          ⚽
        </text>
      ))}
    </svg>
  );
}

export default memo(Momentum);
