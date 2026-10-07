import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { getLeaderboards } from "../api/client";
import LeaderboardTable from "../components/standings/LeaderboardTable";

// Écran dédié pour les compétitions HYBRID (Ligue des Champions, Coupe du
// Monde) : elles n'ont pas de `season` donc pas de classement classique --
// seuls les buteurs/passeurs ont un sens ici, le classement des poules est
// déjà visible dans l'écran "Poules". Réutilisé aussi comme classement
// buteurs/passeurs COMPLET (limit={Infinity}, pas le top 5/15 tronqué) pour
// les compétitions LEAGUE -- voir le titre "Buteurs"/"Passeurs" cliquable
// dans MiniStandings et LeaderboardTable, qui pointent ici.
export default function Leaderboards() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);

  useEffect(() => {
    getLeaderboards(id).then(setData);
  }, [id]);

  const backButton = (
    <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-xs text-gray-400 self-start">
      <ArrowLeft size={14} /> Retour
    </button>
  );

  if (!data) return <div className="p-6 text-sm text-gray-400">Chargement…</div>;
  if (data.scorers.length === 0 && data.assists.length === 0) {
    return (
      <div className="p-3 flex flex-col gap-3 items-start">
        {backButton}
        <p className="text-sm text-gray-400 px-1">Aucun but marqué pour l'instant.</p>
      </div>
    );
  }

  return (
    <div className="p-3 flex flex-col gap-3">
      {backButton}
      <div className="flex gap-4">
        <LeaderboardTable title="Buteurs" rows={data.scorers} limit={Infinity} />
        <LeaderboardTable title="Passeurs" rows={data.assists} limit={Infinity} />
      </div>
    </div>
  );
}
