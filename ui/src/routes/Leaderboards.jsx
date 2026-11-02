import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getLeaderboards } from "../api/client";
import LeaderboardTable from "../components/standings/LeaderboardTable";

// Onglet « Stats » de l'espace de compétition, tous formats (refonte UI,
// lot 2) : classements buteurs/passeurs COMPLETS (limit={Infinity}, pas le
// top 5/15 tronqué de MiniStandings et du Classement, dont les titres
// « Buteurs »/« Passeurs » cliquables pointent ici).
export default function Leaderboards() {
  const { id } = useParams();
  const [data, setData] = useState(null);

  useEffect(() => {
    getLeaderboards(id).then(setData);
  }, [id]);

  if (!data) return <div className="p-6 text-sm text-gray-400">Chargement…</div>;
  if (data.scorers.length === 0 && data.assists.length === 0) {
    return <p className="p-4 text-sm text-gray-400">Aucun but marqué pour l'instant.</p>;
  }

  return (
    <div className="p-3 flex gap-4">
      <LeaderboardTable title="Buteurs" rows={data.scorers} limit={Infinity} />
      <LeaderboardTable title="Passeurs" rows={data.assists} limit={Infinity} />
    </div>
  );
}
