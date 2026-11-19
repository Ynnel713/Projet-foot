import { memo, useLayoutEffect, useMemo, useRef, useState } from "react";
import { L } from "./trace";
import {
  AXIS_Y,
  BAR_HALF_PX,
  BARS_BOTTOM_Y,
  FRISE_PX,
  GOAL_ROW_PX,
  barBox,
  GOAL_DOT_PX,
  domainMinutes,
  goalMarkers,
  minuteX,
  ticks,
} from "../../utils/momentumLayout";
import { clock } from "../../utils/matchClock";
import { hudName } from "../../utils/matchHud";
import { LABEL, barHeight, completedMinutes, momentumByMinute } from "../../utils/momentum";

// Frise de pression territoriale (tickets v2-ecran-match/11a rendu, 11b données ; remplace `Momentum.jsx`) :
// histogramme symétrique, une barre par minute terminée, domicile au-dessus de l'axe, extérieur en dessous, pleine
// largeur de la zone basse, 72 px de haut. Domaine fixe de 105 minutes (les barres ne bougent pas quand le temps
// additionnel arrive). Échelle fixe (0,6 = pleine hauteur) : une barre affichée ne change plus jamais de hauteur. Zone
// future vide : la ligne de base seule. Curseur de lecture à l'instant lu. Calcul : `utils/momentum.js`.

// Texte d'un but : « 23' · Kvaratskhelia », « 52' · Mata (csc) » (minute de l'horloge du HUD, nom du HUD).
function goalLabel(trace, g) {
  const name = g.scorer ? hudName(g.scorer) : "But";
  return `${clock(trace, g.minute).label} · ${name}${g.own_goal ? " (csc)" : ""}`;
}

// Partie fixe (barres, axe, repères, buts) : redessinée au changement de minute, de but, de largeur ou à la mi-temps,
// jamais à chaque image (ticket v2-ecran-match/01).
const Bars = memo(function Bars({ trace, complete, goalsShown, width, domain, halfReached, onTip }) {
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
      {goalMarkers(goals, width, domain).map((m) => (
        // marqueur de but (ticket v2-ecran-match/12) : pastille de 8 px à la couleur de l'équipe, zone de toucher de
        // 16 px ; info-bulle au survol (souris) ou au toucher (un second toucher la referme)
        <g
          key={m.i}
          data-goal-marker={m.i}
          data-team={m.team}
          role="button"
          tabIndex={0}
          aria-label={goalLabel(trace, goals[m.i])}
          className="cursor-pointer outline-none"
          onPointerEnter={(e) => e.pointerType === "mouse" && onTip(m.i)}
          onPointerLeave={(e) => e.pointerType === "mouse" && onTip(null)}
          onPointerUp={(e) => e.pointerType !== "mouse" && onTip((t) => (t === m.i ? null : m.i))}
          onFocus={() => onTip(m.i)}
          onBlur={() => onTip(null)}
        >
          <circle cx={m.x} cy={m.y} r={GOAL_DOT_PX} fill="transparent" />
          <circle
            cx={m.x}
            cy={m.y}
            r={GOAL_DOT_PX / 2}
            style={{ fill: `var(--team-${m.team}-ui)` }}
            stroke="rgba(0,0,0,0.6)"
            strokeWidth={1}
          />
        </g>
      ))}
    </g>
  );
});

// Info-bulle d'un but, dans la frise : sous la rangée du domicile ou au-dessus de celle de l'extérieur, ancrée à gauche
// ou à droite près des bords pour ne pas sortir de la zone basse.
function GoalTip({ trace, index, width, domain }) {
  const goals = trace.goals;
  const m = goalMarkers(goals.slice(0, index + 1), width, domain)[index];
  const shift = m.x < width * 0.15 ? "0" : m.x > width * 0.85 ? "-100%" : "-50%";
  const vertical = m.team === "home" ? { top: GOAL_ROW_PX + 2 } : { bottom: FRISE_PX - BARS_BOTTOM_Y + 2 };
  return (
    <div
      data-goal-tip={index}
      role="tooltip"
      className="absolute z-10 pointer-events-none whitespace-nowrap rounded border border-line bg-surface-2 px-1.5 py-0.5 text-caption text-gray-100 tabular-nums"
      style={{ left: m.x, transform: `translateX(${shift})`, borderColor: `var(--team-${m.team}-ui)`, ...vertical }}
    >
      {goalLabel(trace, goals[index])}
    </div>
  );
}

// `shownMin` : instant lu (minutes, fractionnaire) pour le curseur, seule partie redessinée à chaque image ;
// `goalsShown` : buts déjà vus.
function MomentumTimeline({ trace, shownMin, goalsShown }) {
  const ref = useRef(null);
  const [width, setWidth] = useState(0);
  const [tip, setTip] = useState(null); // but dont l'info-bulle est ouverte (indice dans trace.goals)
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
    <div ref={ref} data-zone="momentum" className="relative w-full" style={{ height: FRISE_PX }}>
      <svg width={width} height={FRISE_PX} className="block overflow-visible" role="img" aria-label={LABEL}>
        <title>{LABEL}</title>
        <Bars
          trace={trace}
          complete={complete}
          goalsShown={goalsShown}
          width={width}
          domain={domain}
          halfReached={halfReached}
          onTip={setTip}
        />
        {width > 0 && (
          <line data-cursor pointerEvents="none" x1={cursorX} y1={0} x2={cursorX} y2={BARS_BOTTOM_Y + GOAL_ROW_PX} stroke="white" strokeWidth={1.5} />
        )}
      </svg>
      {tip != null && tip < goalsShown && width > 0 && <GoalTip trace={trace} index={tip} width={width} domain={domain} />}
    </div>
  );
}

export default MomentumTimeline;
