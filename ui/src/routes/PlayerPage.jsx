import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getRoster } from "../api/client";
import PlayerProfile from "../components/team/PlayerProfile";

// Fiche joueur en écran indépendant (28/09/2026, retour terrain : "les 2 doivent être indépendantes, actuellement elles sont liées").
// Recharge l'effectif du club pour retrouver ce joueur par son nom -- pas encore d'endpoint "un seul joueur" côté API. Refonte UI,
// lot 5 : plus de bouton « Retour » (les onglets de la compétition et le retour du navigateur le remplacent).
export default function PlayerPage() {
  const { id, clubName, playerName } = useParams();
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
      <div className="mx-auto w-full max-w-6xl flex flex-col gap-3">
        {error && <p className="text-sm text-gray-400 px-1">{error}</p>}
        {!error && !player && <p className="text-sm text-gray-400 px-1">Chargement…</p>}
        {player && <PlayerProfile player={player} />}
      </div>
    </div>
  );
}
