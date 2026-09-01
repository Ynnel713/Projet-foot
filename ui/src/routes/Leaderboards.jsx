import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getLeaderboards } from "../api/client";
import LeaderboardTable from "../components/standings/LeaderboardTable";

// Écran dédié pour les compétitions HYBRID (Ligue des Champions, Coupe du
// Monde) : elles n'ont pas de `season` donc pas d'onglet "Classement"
// classique (voir BottomNav) -- seuls les buteurs/passeurs ont un sens ici,
// le classement des poules est déjà visible dans l'onglet "Poules".
export default function Leaderboards() {
  const { id } = useParams();
  const [data, setData] = useState(null);

  useEffect(() => {
    getLeaderboards(id).then(setData);
  }, [id]);

  if (!data) return <div className="p-6 text-sm text-gray-400">Chargement…</div>;
  if (data.scorers.length === 0 && data.assists.length === 0) {
    return <div className="p-6 text-sm text-gray-400">Aucun but marqué pour l'instant.</div>;
  }

  return (
    <div className="p-3 flex gap-4">
      <LeaderboardTable title="Buteurs" rows={data.scorers} />
      <LeaderboardTable title="Passeurs" rows={data.assists} />
    </div>
  );
}
