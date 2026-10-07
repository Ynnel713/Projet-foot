import { useParams, useNavigate } from "react-router-dom";
import { useGameStore } from "../../store/useGameStore";
import ClubLogo from "../common/ClubLogo";

// Mêmes teintes que le radar/les attributs FM (voir fmTier.js) -- vert/gris/
// rouge, réutilisées ici comme code couleur "bon/neutre/mauvais" pour les
// résultats et buts du classement condensé, plutôt qu'une nouvelle palette.
const GOOD = "#3ddc70";
const NEUTRAL = "#9ca3af"; // gray-400
const BAD = "#e0645a";

// Classement condensé affiché à côté de la journée -- élargi le 28/09/2026
// (retour terrain) pour reprendre les colonnes V/N/D/BP/BC/Diff de
// StandingsTable (classement plein écran), pas seulement les points, puis
// encore une fois (+colonne J, police plus grande, code couleur) une fois
// la place gagnée par la réduction de la colonne du score de MatchRow.
//
// `leaderboards` vient du parent (Simulation.jsx), rechargé à chaque action
// de simulation -- PAS récupéré ici via un useEffect local sur `id` seul :
// `id` ne change jamais pendant une saison, un tel effet ne se redéclenche
// donc qu'une fois au montage et reste figé sur les buts de la toute
// première journée jusqu'à la fin (anomalie remontée le 28/09/2026,
// meilleur buteur à 2 buts après une saison complète).
export default function MiniStandings({ standings, leaderboards, className = "" }) {
  const followedClub = useGameStore((s) => s.followedClub);
  const { id } = useParams();
  const navigate = useNavigate();

  return (
    <aside className={`flex-col border-l border-white/5 bg-surface/40 p-3 overflow-y-auto ${className}`}>
      <h3 className="text-sm font-semibold text-gray-400 mb-2">Classement</h3>
      <table className="w-full text-[13px] border-collapse table-fixed">
        <thead>
          <tr className="text-gray-500 text-xs">
            <th className="text-left font-medium pb-1.5 w-5">#</th>
            <th className="text-left font-medium pb-1.5">Club</th>
            <th className="text-center font-medium pb-1.5 w-6">J</th>
            <th className="text-center font-medium pb-1.5 w-6">V</th>
            <th className="text-center font-medium pb-1.5 w-6">N</th>
            <th className="text-center font-medium pb-1.5 w-6">D</th>
            <th className="text-center font-medium pb-1.5 w-7">BP</th>
            <th className="text-center font-medium pb-1.5 w-7">BC</th>
            <th className="text-center font-medium pb-1.5 w-8">Diff</th>
            <th className="text-center font-semibold pb-1.5 w-7">Pts</th>
          </tr>
        </thead>
        <tbody>
          {standings.map((row) => (
            <StandingLine
              key={row.club}
              row={row}
              highlighted={row.club === followedClub}
              onClick={() => navigate(`/competition/${id}/clubs/${encodeURIComponent(row.club)}`)}
            />
          ))}
        </tbody>
      </table>

      {leaderboards && (leaderboards.scorers.length > 0 || leaderboards.assists.length > 0) && (
        <div className="flex gap-3 mt-3 pt-3 border-t border-white/5">
          <MiniLeaderboard
            title="Buteurs"
            rows={leaderboards.scorers}
            onTitleClick={() => navigate(`/competition/${id}/leaderboards`)}
          />
          <MiniLeaderboard
            title="Passeurs"
            rows={leaderboards.assists}
            onTitleClick={() => navigate(`/competition/${id}/leaderboards`)}
          />
        </div>
      )}
    </aside>
  );
}

// Top 5 buteurs/passeurs sous le classement -- reprend les mêmes lignes que
// LeaderboardTable (écran Classement plein écran) mais tassées à 5 entrées et
// sans en-tête de colonnes, pour tenir dans la colonne "Classement" existante
// plutôt que d'ouvrir un nouvel écran. Le titre est cliquable -> classement
// complet (toutes les entrées, pas seulement le top 5) sur /leaderboards.
function MiniLeaderboard({ title, rows, onTitleClick }) {
  if (rows.length === 0) return null;
  return (
    <div className="flex-1 min-w-0">
      <button
        onClick={onTitleClick}
        className="text-[11px] font-semibold text-gray-500 mb-1 hover:text-accent hover:underline transition-colors"
      >
        {title}
      </button>
      <div className="flex flex-col gap-0.5">
        {rows.slice(0, 5).map((row, i) => (
          <div
            key={`${row.player}-${row.club}`}
            className="flex items-center gap-1 text-[11px] px-1.5 py-1 rounded bg-white/[0.02]"
          >
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

function StandingLine({ row, highlighted, onClick }) {
  // Quand la ligne est déjà surlignée (club suivi, en doré), le code
  // couleur par colonne s'efface pour ne pas lutter avec le doré -- un seul
  // signal de couleur dominant par ligne.
  const color = (hex) => (highlighted ? undefined : { color: hex });

  return (
    <tr
      onClick={onClick}
      className={`cursor-pointer hover:bg-white/5 ${highlighted ? "bg-gold/15 text-gold font-semibold" : "text-gray-300"}`}
    >
      <td className="py-1.5 text-gray-500">{row.rank}</td>
      <td className="py-1.5 max-w-0">
        <span className="flex items-center gap-1.5 min-w-0">
          <ClubLogo clubName={row.club} size={18} />
          <span className="truncate">{row.club}</span>
        </span>
      </td>
      <td className="text-center tabular-nums text-gray-500">{row.played}</td>
      <td className="text-center tabular-nums" style={color(GOOD)}>
        {row.won}
      </td>
      <td className="text-center tabular-nums" style={color(NEUTRAL)}>
        {row.drawn}
      </td>
      <td className="text-center tabular-nums" style={color(BAD)}>
        {row.lost}
      </td>
      <td className="text-center tabular-nums" style={color(GOOD)}>
        {row.goals_for}
      </td>
      <td className="text-center tabular-nums" style={color(BAD)}>
        {row.goals_against}
      </td>
      <td className="text-center tabular-nums" style={color(row.goal_diff > 0 ? GOOD : row.goal_diff < 0 ? BAD : NEUTRAL)}>
        {row.goal_diff > 0 ? `+${row.goal_diff}` : row.goal_diff}
      </td>
      <td className="text-center tabular-nums font-bold">{row.points}</td>
    </tr>
  );
}
