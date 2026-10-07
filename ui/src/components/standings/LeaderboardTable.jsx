import ClubLink from "../common/ClubLink";

// `limit` : nombre de lignes affichées -- 15 par défaut (aperçu sur l'écran
// Classement), `Infinity` pour le classement complet (voir Leaderboards.jsx,
// le seul écran qui donne accès à TOUT le classement buteurs/passeurs,
// pas seulement un top tronqué).
// `onTitleClick` : si fourni, le titre devient cliquable (typiquement vers
// l'écran Leaderboards ci-dessus, quand cet aperçu est déjà tronqué).
export default function LeaderboardTable({ title, rows, limit = 15, onTitleClick }) {
  if (rows.length === 0) return null;
  return (
    <div className="flex-1 min-w-0">
      {onTitleClick ? (
        <button
          onClick={onTitleClick}
          className="text-xs font-semibold text-gray-400 mb-1.5 hover:text-accent hover:underline transition-colors"
        >
          {title}
        </button>
      ) : (
        <h3 className="text-xs font-semibold text-gray-400 mb-1.5">{title}</h3>
      )}
      <div className="flex flex-col gap-0.5">
        {rows.slice(0, limit).map((row, i) => (
          <div key={`${row.player}-${row.club}`} className="flex items-center justify-between text-xs px-2 py-1 rounded bg-white/[0.02]">
            <span className="w-4 text-gray-500 shrink-0">{i + 1}</span>
            <span className="flex-1 min-w-0 truncate px-1">{row.player}</span>
            <ClubLink name={row.club} logoSize={13} className="text-[10px] text-gray-500 max-w-[30%] px-1" />
            <span className="tabular-nums font-semibold shrink-0">{row.count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
