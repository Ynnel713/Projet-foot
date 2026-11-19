import { useEffect, useMemo } from "react";
import { X } from "lucide-react";
import { holderTeams, matchStats, possessionPrefix } from "../../utils/matchStats";

// Panneau de statistiques (ticket v2-ecran-match/14b, décision du propriétaire du 19/11/2026, spec « Statistiques ») :
// tiroir de 340 px à droite (recouvre la composition extérieure ; HUD, terrain et frise restent visibles), feuille depuis
// le bas sous 960 px de large en portrait ; en paysage bas (moins de 500 px de haut), tiroir latéral pleine hauteur pour
// garder le terrain visible (réserve A1 de l'expert, décision du propriétaire du 19/11/2026). Le match continue. Valeurs filtrées sur le temps lu (`utils/matchStats.js`, EM-14a) :
// recalculées une fois par seconde de match lue au plus ; possession calculée seulement panneau ouvert.
const ROWS = [
  ["possession", "Possession", (v) => `${v} %`],
  ["shots", "Tirs"],
  ["onTarget", "Tirs cadrés"],
  ["corners", "Corners"],
  ["fouls", "Fautes"],
  ["offsides", "Hors-jeu"],
  ["cards", "Cartons"], // « — » tant que le moteur n'en produit pas (ticket v2-attributs-restants/09a)
];

function StatRow({ id, label, value, format = (v) => v }) {
  const known = value != null;
  const total = known ? value.home + value.away : 0;
  const homeShare = known ? (total ? value.home / total : 0.5) : 0.5;
  return (
    <li data-stat={id} className="py-1.5">
      <div className="flex items-baseline justify-between text-data tabular-nums">
        <span data-side="home" className="w-14 font-semibold text-white">{known ? format(value.home) : "—"}</span>
        <span className="text-caption uppercase tracking-wide text-gray-400">{label}</span>
        <span data-side="away" className="w-14 text-right font-semibold text-white">{known ? format(value.away) : "—"}</span>
      </div>
      <div className="mt-1 flex h-1.5 gap-0.5 overflow-hidden rounded-full bg-surface-3" aria-hidden="true">
        {known && (
          <>
            <div style={{ width: `${homeShare * 100}%`, background: "var(--team-home-ui)" }} />
            <div style={{ width: `${(1 - homeShare) * 100}%`, background: "var(--team-away-ui)" }} />
          </>
        )}
      </div>
    </li>
  );
}

export default function StatsDrawer({ trace, shownS, onClose }) {
  const prefix = useMemo(() => possessionPrefix(holderTeams(trace.ticks)), [trace.ticks]);
  const second = Math.floor(shownS);
  const stats = useMemo(
    () => matchStats({ events: trace.events ?? [], prefix, minute: second / 60, tickSeconds: trace.tick_seconds }),
    [trace.events, prefix, second, trace.tick_seconds],
  );
  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <aside
      data-zone="statistiques"
      aria-label="Statistiques du match"
      className="absolute z-30 bg-surface border-line shadow-xl flex flex-col right-0 top-0 bottom-0 w-[340px] border-l [@media(max-width:959.98px)_and_(min-height:500px)]:fixed [@media(max-width:959.98px)_and_(min-height:500px)]:top-auto [@media(max-width:959.98px)_and_(min-height:500px)]:left-0 [@media(max-width:959.98px)_and_(min-height:500px)]:w-auto [@media(max-width:959.98px)_and_(min-height:500px)]:max-h-[60vh] [@media(max-width:959.98px)_and_(min-height:500px)]:border-l-0 [@media(max-width:959.98px)_and_(min-height:500px)]:border-t [@media(max-width:959.98px)_and_(min-height:500px)]:rounded-t-xl"
    >
      <header className="flex items-center gap-2 px-3 pt-2">
        <span className="min-w-0 flex-1 truncate text-data font-semibold" style={{ color: "var(--team-home-ui)" }}>
          {trace.home}
        </span>
        <h2 className="font-display text-sm font-bold uppercase tracking-widest text-gray-200">Stats</h2>
        <span className="min-w-0 flex-1 truncate text-right text-data font-semibold" style={{ color: "var(--team-away-ui)" }}>
          {trace.away}
        </span>
        <button
          onClick={onClose}
          aria-label="Fermer les statistiques"
          className="-mr-2 flex size-11 shrink-0 items-center justify-center text-gray-400 hover:text-white"
        >
          <X size={16} />
        </button>
      </header>
      <ul className="min-h-0 overflow-y-auto px-3 pb-3">
        {ROWS.map(([id, label, format]) => (
          <StatRow key={id} id={id} label={label} value={stats[id]} format={format} />
        ))}
      </ul>
    </aside>
  );
}
