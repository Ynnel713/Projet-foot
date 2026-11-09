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
    <svg viewBox={`-2 -6 ${width + 4} ${2 * H + 12}`} className="w-full" style={{ maxHeight: 110 }}>
      <title>Match momentum</title>
      <rect x={0} y={0} width={width} height={H} fill="rgba(79,142,247,0.12)" />
      <rect x={0} y={H} width={width} height={H} fill="rgba(224,184,74,0.12)" />
      {values.map((v, m) =>
        v == null || m >= played ? null : (
          <rect
            key={m}
            x={m * X + 0.4}
            width={X - 0.8}
            y={v > 0 ? H - v * scale : H}
            height={Math.abs(v) * scale}
            fill={v > 0 ? "#4f8ef7" : "#e0b84a"}
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
