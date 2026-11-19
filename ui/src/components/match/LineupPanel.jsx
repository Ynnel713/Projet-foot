import { memo } from "react";
import ClubBadge from "../team/ClubBadge";
import { BENCH_TEXT_OPACITY, DENSITIES, EDGE_PX, HEADER_GAP_PX, POSTE_PX, lineupSubtitle } from "../../utils/lineupCards";

// Composition d'une équipe en cartes (ticket v2-ecran-match/10a) : en-tête (écusson, club, formation · entraîneur),
// « Titulaires » puis « Remplaçants ». Carte : [numéro sur pastille d'équipe] [poste] [nom sur une ligne], liseré à la
// couleur d'équipe. L'extérieur est en miroir (liseré et numéro à droite). Aucune note ni statistique. La place
// (colonne ou tiroir) est donnée par l'écran (ticket v2-ecran-match/04) ; la densité aussi, d'après la hauteur de la
// colonne (ticket v2-ecran-match/10b : complet, compact, serré ; hauteurs lues dans `DENSITIES`).
// Icône de but (ticket v2-ecran-match/10c) : ballon de 12 px après le nom, « ×n » au-delà d'un but ; but contre son camp
// en rouge. Info-bulle et texte pour les lecteurs d'écran.
function BallIcon({ color }) {
  return (
    <svg width={12} height={12} viewBox="0 0 12 12" aria-hidden="true" className="shrink-0">
      <circle cx={6} cy={6} r={5.4} fill={color} stroke="#0b0f14" strokeWidth={0.8} />
      <path d="M6 3.4 8.4 5.1 7.5 7.9H4.5L3.6 5.1Z" fill="#0b0f14" />
    </svg>
  );
}

function GoalMarks({ stats }) {
  if (!stats) return null;
  const marks = [
    stats.goals > 0 && { kind: "but", n: stats.goals, color: "#ffffff", label: stats.goals > 1 ? `${stats.goals} buts` : "but" },
    stats.ownGoals > 0 && {
      kind: "csc",
      n: stats.ownGoals,
      color: "#ef4444",
      label: stats.ownGoals > 1 ? `${stats.ownGoals} buts contre son camp` : "but contre son camp",
    },
  ].filter(Boolean);
  return marks.map((m) => (
    <span key={m.kind} data-goal={m.kind} title={m.label} className="shrink-0 flex items-center gap-0.5 text-caption leading-none text-gray-200 tabular-nums">
      <BallIcon color={m.color} />
      {m.n > 1 && <span>×{m.n}</span>}
      <span className="sr-only">{m.label}</span>
    </span>
  ));
}

function PlayerCard({ player, side, bench, d, stats }) {
  const mirror = side === "away";
  const pastille = bench ? d.benchNumber : d.number;
  return (
    <li
      data-card={bench ? "remplacant" : "titulaire"}
      className={`flex items-center gap-1.5 px-1.5 bg-surface-2 ${mirror ? "flex-row-reverse" : ""}`}
      style={{
        height: bench ? d.bench : d.starter,
        [mirror ? "borderRight" : "borderLeft"]: `${EDGE_PX}px solid var(--team-${side}-ui)`,
        opacity: bench ? BENCH_TEXT_OPACITY : 1,
      }}
    >
      <span
        className="shrink-0 flex items-center justify-center rounded-sm text-caption font-bold tabular-nums"
        style={{
          width: pastille,
          height: pastille,
          background: `var(--team-${side})`,
          color: `var(--team-${side}-ink)`,
          lineHeight: 1,
        }}
      >
        {player.number}
      </span>
      <span className={`shrink-0 text-caption text-gray-500 ${mirror ? "text-right" : ""}`} style={{ width: POSTE_PX }}>
        {player.poste}
      </span>
      <span
        data-name
        title={player.name}
        className={`min-w-0 flex-1 truncate text-data leading-none text-gray-100 ${mirror ? "text-right" : ""}`}
      >
        {player.name}
      </span>
      <GoalMarks stats={stats} />
    </li>
  );
}

function Section({ title, players, side, bench, d, stats }) {
  return (
    <section aria-label={title}>
      <h3
        className={`h-4 text-caption leading-4 font-semibold uppercase tracking-wide text-gray-400 ${side === "away" ? "text-right" : ""}`}
      >
        {title}
      </h3>
      <ul className="flex flex-col">
        {players.map((p) => (
          <PlayerCard key={p.name} player={p} side={side} bench={bench} d={d} stats={stats?.[p.name]} />
        ))}
      </ul>
    </section>
  );
}

// `stats` : buts révélés par nom de joueur (`goalsByPlayer`, ticket v2-ecran-match/10c), objet stable entre deux buts.
function LineupPanel({ lineup, side, density = "complet", stats }) {
  if (!lineup) return null;
  const mirror = side === "away";
  const d = DENSITIES[density];
  const oneLine = density === "serre"; // en-tête sur une ligne : formation · entraîneur au survol et pour les lecteurs d'écran
  const subtitle = lineupSubtitle(lineup);
  return (
    <div data-density={density} className="flex flex-col w-full">
      <header
        className={`flex flex-col ${mirror ? "items-end" : ""}`}
        style={{ height: d.header, marginBottom: HEADER_GAP_PX }}
        title={oneLine ? subtitle : undefined}
      >
        <div className={`flex items-center gap-2 h-7 min-w-0 max-w-full ${mirror ? "flex-row-reverse" : ""}`}>
          <ClubBadge clubName={lineup.club} color={`var(--team-${side})`} size={d.crest} className="text-[10px]" />
          <h2
            title={lineup.club}
            className="min-w-0 truncate font-display text-lg leading-none font-bold uppercase tracking-wide"
            style={{ color: `var(--team-${side}-ui)` }}
          >
            {lineup.club}
          </h2>
        </div>
        <div
          title={subtitle}
          className={oneLine ? "sr-only" : "h-4 max-w-full truncate text-caption leading-4 text-gray-400"}
        >
          {subtitle}
        </div>
      </header>
      <Section title="Titulaires" players={lineup.starters} side={side} bench={false} d={d} stats={stats} />
      {lineup.bench.length > 0 && (
        <div className="mt-1">
          <Section title="Remplaçants" players={lineup.bench} side={side} bench d={d} stats={stats} />
        </div>
      )}
    </div>
  );
}

export default memo(LineupPanel);
