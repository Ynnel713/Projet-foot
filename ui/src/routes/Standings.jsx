import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
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
    <div className="p-3 flex flex-col gap-4 mx-auto w-full max-w-[1280px]">
      <section className="rounded-xl bg-surface border border-line overflow-hidden">
        <StandingsTable rows={rows} showRankChange followable />
      </section>
      {leaderboards && (leaderboards.scorers.length > 0 || leaderboards.assists.length > 0) && (
        <div className="flex gap-4">
          <LeaderboardTable title="Buteurs" rows={leaderboards.scorers} onTitleClick={() => navigate(`/competition/${id}/leaderboards`)} />
          <LeaderboardTable title="Passeurs" rows={leaderboards.assists} onTitleClick={() => navigate(`/competition/${id}/leaderboards`)} />
        </div>
      )}
    </div>
  );
}
