import { useParams, useNavigate } from "react-router-dom";
import StandingsTable from "../standings/StandingsTable";
import ClubLogo from "../common/ClubLogo";

// Colonne de droite de l'écran Journée (bureau) : le classement unique (StandingsTable, lot 3) puis le top 5 des buteurs et passeurs.
//
// `leaderboards` vient du parent (Simulation.jsx), rechargé à chaque action de simulation -- PAS récupéré ici via un useEffect local
// sur `id` seul : `id` ne change jamais pendant une saison, un tel effet ne se redéclenche donc qu'une fois au montage et reste figé
// sur les buts de la toute première journée (anomalie remontée le 28/09/2026, meilleur buteur à 2 buts après une saison complète).
export default function MiniStandings({ standings, leaderboards, className = "" }) {
  const { id } = useParams();
  const navigate = useNavigate();

  return (
    <aside className={`flex-col border-l border-line bg-surface/40 p-3 overflow-y-auto ${className}`}>
      <h2 className="text-sm font-semibold text-gray-400 mb-2">Classement</h2>
      <StandingsTable rows={standings} />

      {leaderboards && (leaderboards.scorers.length > 0 || leaderboards.assists.length > 0) && (
        <div className="flex gap-3 mt-3 pt-3 border-t border-line">
          <MiniLeaderboard title="Buteurs" rows={leaderboards.scorers} onTitleClick={() => navigate(`/competition/${id}/leaderboards`)} />
          <MiniLeaderboard title="Passeurs" rows={leaderboards.assists} onTitleClick={() => navigate(`/competition/${id}/leaderboards`)} />
        </div>
      )}
    </aside>
  );
}

// Top 5 buteurs/passeurs sous le classement -- reprend les mêmes lignes que LeaderboardTable (écran Stats) mais tassées à 5 entrées
// et sans en-tête de colonnes. Le titre est cliquable -> classement complet sur /leaderboards.
function MiniLeaderboard({ title, rows, onTitleClick }) {
  if (rows.length === 0) return null;
  return (
    <div className="flex-1 min-w-0">
      <button onClick={onTitleClick} className="text-caption font-semibold text-gray-500 mb-1 hover:text-link hover:underline transition-colors">
        {title}
      </button>
      <div className="flex flex-col gap-0.5">
        {rows.slice(0, 5).map((row, i) => (
          <div key={`${row.player}-${row.club}`} className="flex items-center gap-1 text-caption px-1.5 py-1 rounded bg-white/[0.02]">
            <span className="w-3.5 text-gray-500 shrink-0">{i + 1}</span>
            <ClubLogo clubName={row.club} size={13} />
            <span className="flex-1 min-w-0 truncate px-1">{row.player}</span>
            <span className="tabular-nums font-semibold shrink-0">{row.count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
