import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { getStandings, getLeaderboards } from "../api/client";
import StandingsTable from "../components/standings/StandingsTable";
import LeaderboardTable from "../components/standings/LeaderboardTable";

export default function Standings() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [rows, setRows] = useState([]);
  const [leaderboards, setLeaderboards] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getStandings(id), getLeaderboards(id)])
      .then(([standingsRows, boards]) => {
        setRows(standingsRows);
        setLeaderboards(boards);
      })
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="p-6 text-sm text-gray-400">Chargement…</div>;
  if (rows.length === 0) return <div className="p-6 text-sm text-gray-400">Aucun classement disponible.</div>;

  return (
    <div className="p-3 flex flex-col gap-4">
      <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-xs text-gray-400 self-start">
        <ArrowLeft size={14} /> Retour
      </button>
      <StandingsTable rows={rows} competitionId={id} />
      {leaderboards && (leaderboards.scorers.length > 0 || leaderboards.assists.length > 0) && (
        <div className="flex gap-4">
          <LeaderboardTable
            title="Buteurs"
            rows={leaderboards.scorers}
            onTitleClick={() => navigate(`/competition/${id}/leaderboards`)}
          />
          <LeaderboardTable
            title="Passeurs"
            rows={leaderboards.assists}
            onTitleClick={() => navigate(`/competition/${id}/leaderboards`)}
          />
        </div>
      )}
    </div>
  );
}
