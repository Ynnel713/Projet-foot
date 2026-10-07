import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { getRoster } from "../api/client";
import TeamHeader from "../components/team/TeamHeader";
import PlayerCard from "../components/team/PlayerCard";

// Ordre d'affichage des effectifs : défense -> milieu -> attaque -- même
// ordre que app._POSTE_DISPLAY_ORDER côté Streamlit.
const POSTE_DISPLAY_ORDER = ["GK", "DC", "LB", "RB", "MDC", "MC", "MOC", "AG", "AD", "SA", "BU", "ATT"];

function groupByPoste(players) {
  const groups = new Map();
  for (const p of players) {
    if (!groups.has(p.poste)) groups.set(p.poste, []);
    groups.get(p.poste).push(p);
  }
  const known = POSTE_DISPLAY_ORDER.filter((poste) => groups.has(poste));
  const unknown = [...groups.keys()].filter((poste) => !POSTE_DISPLAY_ORDER.includes(poste)).sort();
  return [...known, ...unknown].map((poste) => [poste, [...groups.get(poste)].sort((a, b) => b.note - a.note)]);
}

// Fiche équipe : liste l'effectif, ne montre plus jamais la fiche d'un
// joueur en interne (retour du 28/09/2026 : "les 2 doivent être
// indépendantes, actuellement elles sont liées") -- cliquer un joueur
// navigue vers sa propre page (PlayerPage), effectif et fiche joueur sont
// désormais deux écrans complètement séparés.
export default function TeamRoster() {
  const { id, clubName } = useParams();
  const navigate = useNavigate();
  const [roster, setRoster] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setRoster(null);
    setError(null);
    getRoster(id, clubName).catch(() => setError("Effectif indisponible pour ce club.")).then((r) => r && setRoster(r));
  }, [id, clubName]);

  return (
    <div className="p-3 flex flex-col gap-3">
      <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-xs text-gray-400 self-start">
        <ArrowLeft size={14} /> Retour
      </button>

      {error && <p className="text-sm text-gray-400 px-1">{error}</p>}
      {!error && !roster && <p className="text-sm text-gray-400 px-1">Chargement…</p>}

      {roster && (
        <>
          <TeamHeader roster={roster} />
          {groupByPoste(roster.players).map(([poste, players]) => (
            <div key={poste}>
              <div className="text-xs font-bold uppercase tracking-wide text-gray-400 mb-1.5">
                {poste} · {players.length} joueur{players.length > 1 ? "s" : ""}
              </div>
              <div className="grid gap-2" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(96px, 1fr))" }}>
                {players.map((player) => (
                  <PlayerCard
                    key={player.id ?? player.name}
                    player={player}
                    onSelect={() =>
                      navigate(`/competition/${id}/clubs/${encodeURIComponent(clubName)}/players/${encodeURIComponent(player.name)}`)
                    }
                  />
                ))}
              </div>
            </div>
          ))}
        </>
      )}
    </div>
  );
}
