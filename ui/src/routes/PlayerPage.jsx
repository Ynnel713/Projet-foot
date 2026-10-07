import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { getRoster } from "../api/client";
import PlayerProfile from "../components/team/PlayerProfile";

// Fiche joueur en écran indépendant (28/09/2026, retour terrain : "les 2
// doivent être indépendantes, actuellement elles sont liées") -- avant,
// cliquer un joueur (depuis le terrain ou l'effectif) affichait sa fiche
// coincée à l'intérieur de la fiche équipe. Recharge l'effectif du club pour
// retrouver ce joueur par son nom -- pas encore d'endpoint "un seul joueur"
// côté API, donc même mécanisme que l'ancien `?player=` de TeamRoster, mais
// sur un écran à lui seul plutôt qu'imbriqué dans l'effectif.
export default function PlayerPage() {
  const { id, clubName, playerName } = useParams();
  const navigate = useNavigate();
  const [player, setPlayer] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setPlayer(null);
    setError(null);
    getRoster(id, clubName)
      .then((roster) => {
        const match = roster.players.find((p) => p.name === playerName);
        if (match) setPlayer(match);
        else setError("Joueur introuvable.");
      })
      .catch(() => setError("Joueur introuvable."));
  }, [id, clubName, playerName]);

  return (
    <div className="p-3 flex flex-col gap-3">
      <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-xs text-gray-400 self-start">
        <ArrowLeft size={14} /> Retour
      </button>

      {error && <p className="text-sm text-gray-400 px-1">{error}</p>}
      {!error && !player && <p className="text-sm text-gray-400 px-1">Chargement…</p>}
      {player && <PlayerProfile player={player} />}
    </div>
  );
}
