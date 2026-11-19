import { memo, useLayoutEffect, useMemo, useRef, useState } from "react";
import { L } from "./trace";
import {
  AXIS_Y,
  BAR_HALF_PX,
  BARS_BOTTOM_Y,
  FRISE_PX,
  GOAL_ROW_PX,
  barBox,
  domainMinutes,
  minuteX,
  ticks,
} from "../../utils/momentumLayout";

// Frise de momentum (ticket v2-ecran-match/11a, remplace `Momentum.jsx`) : histogramme symétrique, une barre par minute,
// domicile au-dessus de l'axe, extérieur en dessous, pleine largeur de la zone basse, 72 px de haut. Domaine fixe de
// 105 minutes (les barres ne bougent pas quand le temps additionnel arrive). Zone future vide : la ligne de base seule.
// Curseur de lecture à l'instant lu. La formule et l'échelle verticale sont celles d'avant (inchangées en 11a ; échelle
// fixe et minute en cours : ticket 11b).
//
// Poussée d'un instant = position du ballon dans la longueur (repère moteur : domicile attaque vers x croissant tout le
// match), accentuée près des buts, plus un bonus à l'équipe qui a le ballon ; moyenne sur la minute.
const POSSESSION_BONUS = 0.15;

function momentumByMinute(trace, n) {
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

// Partie fixe (barres, axe, repères, buts) : redessinée au changement de minute, de but, de largeur ou à la mi-temps,
// jamais à chaque image (ticket v2-ecran-match/01).
const Bars = memo(function Bars({ trace, played, goalsShown, width, domain, halfReached }) {
  // recalculé quand de nouvelles images arrivent (une fois par seconde), pas à chaque image affichée
  const values = useMemo(() => momentumByMinute(trace, domain), [trace, domain]);
  // échelle sur les minutes déjà jouées seulement : la courbe ne trahit rien de la suite (inchangé, échelle fixe en 11b)
  const scale = BAR_HALF_PX / Math.max(0.2, ...values.map((v, m) => (m < played ? Math.abs(v ?? 0) : 0)));
  const { labels, halfLine } = ticks(trace.second_half_start_minute, halfReached);
  const goals = trace.goals.slice(0, goalsShown);
  if (!width) return null;
  return (
    <g>
      {values.map((v, m) => {
        if (v == null || m >= played) return null;
        const { x, width: w } = barBox(m, width, domain);
        const h = Math.min(BAR_HALF_PX, Math.abs(v) * scale);
        return (
          <rect
            key={m}
            data-bar={m}
            x={x}
            width={w}
            y={v > 0 ? AXIS_Y - h : AXIS_Y}
            height={h}
            style={{ fill: v > 0 ? "var(--team-home-ui)" : "var(--team-away-ui)" }}
          />
        );
      })}
      <line x1={0} y1={AXIS_Y} x2={width} y2={AXIS_Y} stroke="rgba(255,255,255,0.3)" strokeWidth={1} />
      {halfLine != null && (
        <line
          data-half-line
          x1={minuteX(halfLine, width, domain)}
          y1={GOAL_ROW_PX}
          x2={minuteX(halfLine, width, domain)}
          y2={BARS_BOTTOM_Y}
          stroke="white"
          strokeWidth={1}
        />
      )}
      {labels.map(({ minute, label }) => (
        <text
          key={label}
          data-tick={label}
          x={minuteX(minute, width, domain)}
          y={FRISE_PX - 2}
          textAnchor={minute === 0 ? "start" : "middle"}
          className="fill-gray-500 text-caption"
        >
          {label}
        </text>
      ))}
      {goals.map((g, i) => (
        <text
          key={i}
          x={minuteX(g.minute, width, domain)}
          y={g.team === "home" ? GOAL_ROW_PX / 2 : BARS_BOTTOM_Y + GOAL_ROW_PX / 2}
          textAnchor="middle"
          dominantBaseline="central"
          fontSize={7}
        >
          ⚽
        </text>
      ))}
    </g>
  );
});

// `shownMin` : instant lu (minutes, fractionnaire) pour le curseur, seule partie redessinée à chaque image ;
// `played` : minutes entamées (barres affichées : m < played) ; `goalsShown` : buts déjà vus.
function MomentumTimeline({ trace, shownMin, played, goalsShown }) {
  const ref = useRef(null);
  const [width, setWidth] = useState(0);
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return undefined;
    const update = () => setWidth(el.clientWidth);
    update();
    const observer = new ResizeObserver(update);
    observer.observe(el);
    return () => observer.disconnect();
  }, []);
  const domain = domainMinutes(trace.ticks.at(-1)?.minute);
  const halfReached = trace.second_half_start_minute != null && shownMin >= trace.second_half_start_minute;
  const cursorX = Math.min(width, minuteX(shownMin, width, domain));
  return (
    <div ref={ref} data-zone="momentum" className="w-full" style={{ height: FRISE_PX }}>
      <svg width={width} height={FRISE_PX} className="block overflow-visible" role="img" aria-label="Match momentum">
        <Bars
          trace={trace}
          played={played}
          goalsShown={goalsShown}
          width={width}
          domain={domain}
          halfReached={halfReached}
        />
        {width > 0 && (
          <line data-cursor x1={cursorX} y1={0} x2={cursorX} y2={BARS_BOTTOM_Y + GOAL_ROW_PX} stroke="white" strokeWidth={1.5} />
        )}
      </svg>
    </div>
  );
}

export default MomentumTimeline;
