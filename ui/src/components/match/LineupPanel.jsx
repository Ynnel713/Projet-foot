import { memo } from "react";
import ClubBadge from "../team/ClubBadge";
import { BENCH_TEXT_OPACITY, DENSITIES, EDGE_PX, HEADER_GAP_PX, POSTE_PX, lineupSubtitle } from "../../utils/lineupCards";

// Composition d'une équipe en cartes (ticket v2-ecran-match/10a) : en-tête (écusson, club, formation · entraîneur),
// « Titulaires » puis « Remplaçants ». Carte : [numéro sur pastille d'équipe] [poste] [nom sur une ligne], liseré à la
// couleur d'équipe. L'extérieur est en miroir (liseré et numéro à droite). Aucune note ni statistique. La place
// (colonne ou tiroir) est donnée par l'écran (ticket v2-ecran-match/04) ; la densité aussi, d'après la hauteur de la
// colonne (ticket v2-ecran-match/10b : complet, compact, serré ; hauteurs lues dans `DENSITIES`).
function PlayerCard({ player, side, bench, d }) {
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
    </li>
  );
}

function Section({ title, players, side, bench, d }) {
  return (
    <section aria-label={title}>
      <h3
        className={`h-4 text-caption leading-4 font-semibold uppercase tracking-wide text-gray-400 ${side === "away" ? "text-right" : ""}`}
      >
        {title}
      </h3>
      <ul className="flex flex-col">
        {players.map((p) => (
          <PlayerCard key={p.name} player={p} side={side} bench={bench} d={d} />
        ))}
      </ul>
    </section>
  );
}

function LineupPanel({ lineup, side, density = "complet" }) {
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
      <Section title="Titulaires" players={lineup.starters} side={side} bench={false} d={d} />
      {lineup.bench.length > 0 && (
        <div className="mt-1">
          <Section title="Remplaçants" players={lineup.bench} side={side} bench d={d} />
        </div>
      )}
    </div>
  );
}

export default memo(LineupPanel);
