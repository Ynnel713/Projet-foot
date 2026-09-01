export default function LeaderboardTable({ title, rows }) {
  if (rows.length === 0) return null;
  return (
    <div className="flex-1 min-w-0">
      <h3 className="text-xs font-semibold text-gray-400 mb-1.5">{title}</h3>
      <div className="flex flex-col gap-0.5">
        {rows.slice(0, 15).map((row, i) => (
          <div key={`${row.player}-${row.club}`} className="flex items-center justify-between text-xs px-2 py-1 rounded bg-white/[0.02]">
            <span className="w-4 text-gray-500 shrink-0">{i + 1}</span>
            <span className="flex-1 min-w-0 truncate px-1">{row.player}</span>
            <span className="text-[10px] text-gray-500 truncate max-w-[30%] px-1">{row.club}</span>
            <span className="tabular-nums font-semibold shrink-0">{row.count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
