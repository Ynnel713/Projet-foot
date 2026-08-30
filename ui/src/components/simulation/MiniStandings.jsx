import { useGameStore } from "../../store/useGameStore";

export default function MiniStandings({ standings, className = "" }) {
  const followedClub = useGameStore((s) => s.followedClub);
  const top5 = standings.slice(0, 5);
  const followedRow = followedClub ? standings.find((r) => r.club === followedClub) : null;
  const showFollowedSeparately = followedRow && followedRow.rank > 5;

  return (
    <aside className={`flex-col border-l border-white/5 bg-surface/40 p-3 gap-1 overflow-y-auto ${className}`}>
      <h3 className="text-xs font-semibold text-gray-400 mb-1">Classement</h3>
      {top5.map((row) => (
        <StandingLine key={row.club} row={row} highlighted={row.club === followedClub} />
      ))}
      {showFollowedSeparately && (
        <>
          <div className="text-center text-gray-600 text-xs">···</div>
          <StandingLine row={followedRow} highlighted />
        </>
      )}
    </aside>
  );
}

function StandingLine({ row, highlighted }) {
  return (
    <div
      className={`flex items-center justify-between text-xs px-2 py-1 rounded ${
        highlighted ? "bg-gold/15 text-gold font-semibold" : "text-gray-300"
      }`}
    >
      <span className="w-4 text-gray-500">{row.rank}</span>
      <span className="flex-1 min-w-0 truncate px-1">{row.club}</span>
      <span className="tabular-nums">{row.points}</span>
    </div>
  );
}
