import { memo } from "react";

// Composition d'une équipe, à côté du terrain : numéro, poste, nom ; banc et entraîneur dessous.
function LineupPanel({ lineup, color }) {
  if (!lineup) return null;
  const row = (p) => (
    <li key={p.name} className="flex gap-1.5 leading-tight">
      <span className="w-5 text-right font-bold tabular-nums" style={{ color }}>
        {p.number}
      </span>
      <span className="w-9 text-gray-500">{p.poste}</span>
      <span className="truncate text-gray-200">{p.name}</span>
    </li>
  );
  return (
    <div className="hidden lg:flex flex-col gap-1 w-52 shrink-0 text-caption self-stretch overflow-y-auto">
      <div className="font-bold text-sm truncate" style={{ color }}>
        {lineup.club}
      </div>
      <div className="text-gray-500">{lineup.formation}</div>
      <ul className="flex flex-col gap-0.5">{lineup.starters.map(row)}</ul>
      <div className="mt-2 text-gray-400 font-semibold">Remplaçants</div>
      <ul className="flex flex-col gap-0.5">{lineup.bench.map(row)}</ul>
      {lineup.coach && (
        <div className="mt-2 text-gray-400">
          Entraîneur : <span className="text-gray-200">{lineup.coach}</span>
        </div>
      )}
    </div>
  );
}

export default memo(LineupPanel);
