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
import { LABEL, barHeight, completedMinutes, momentumByMinute } from "../../utils/momentum";

// Frise de pression territoriale (tickets v2-ecran-match/11a rendu, 11b données ; remplace `Momentum.jsx`) :
// histogramme symétrique, une barre par minute terminée, domicile au-dessus de l'axe, extérieur en dessous, pleine
// largeur de la zone basse, 72 px de haut. Domaine fixe de 105 minutes (les barres ne bougent pas quand le temps
// additionnel arrive). Échelle fixe (0,6 = pleine hauteur) : une barre affichée ne change plus jamais de hauteur. Zone
// future vide : la ligne de base seule. Curseur de lecture à l'instant lu. Calcul : `utils/momentum.js`.

// Partie fixe (barres, axe, repères, buts) : redessinée au changement de minute, de but, de largeur ou à la mi-temps,
// jamais à chaque image (ticket v2-ecran-match/01).
const Bars = memo(function Bars({ trace, complete, goalsShown, width, domain, halfReached }) {
  const lastMinute = trace.ticks.at(-1)?.minute;
  // minutes terminées seulement (images toutes vues) ; recalculé au changement de minute ou à l'arrivée de nouvelles
  // images (une fois par seconde au plus), jamais à chaque image affichée
  const values = useMemo(() => momentumByMinute(trace.ticks, complete, L), [trace.ticks, complete]);
  const { labels, halfLine } = ticks(trace.second_half_start_minute, halfReached);
  const goals = trace.goals.slice(0, goalsShown);
  if (!width) return null;
  return (
    <g>
      {values.map((v, m) => {
        if (v == null) return null;
        const { x, width: w } = barBox(m, width, domain, lastMinute);
        const h = barHeight(v, BAR_HALF_PX);
        return (
          <rect
            key={m}
            data-bar={m}
            x={x}
            width={w}
            y={v >= 0 ? AXIS_Y - h : AXIS_Y}
            height={h}
            style={{ fill: v >= 0 ? "var(--team-home-ui)" : "var(--team-away-ui)" }}
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
// `goalsShown` : buts déjà vus.
function MomentumTimeline({ trace, shownMin, goalsShown }) {
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
  const complete = completedMinutes(shownMin, trace.ticks.at(-1)?.minute, trace.done);
  const halfReached = trace.second_half_start_minute != null && shownMin >= trace.second_half_start_minute;
  const cursorX = Math.min(width, minuteX(shownMin, width, domain));
  return (
    <div ref={ref} data-zone="momentum" className="w-full" style={{ height: FRISE_PX }}>
      <svg width={width} height={FRISE_PX} className="block overflow-visible" role="img" aria-label={LABEL}>
        <title>{LABEL}</title>
        <Bars
          trace={trace}
          complete={complete}
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
