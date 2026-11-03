import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getRoster, getClubFixtures } from "../api/client";
import TeamHeader from "../components/team/TeamHeader";
import RosterTable from "../components/team/RosterTable";
import FixturesList from "../components/team/FixturesList";

// Page d'un club (refonte UI, lot 5) : en-tête compact (chiffres clés + forme), puis deux onglets -- Effectif (tableau par ligne) et
// Calendrier (championnat seulement : l'API répond 409 hors championnat, l'onglet est alors absent). Le retour se fait par les onglets
// de la compétition, plus de bouton « Retour ». Cliquer un joueur ouvre sa fiche (PlayerPage), écran indépendant de l'effectif.
export default function TeamRoster() {
  const { id, clubName } = useParams();
  const [roster, setRoster] = useState(null);
  const [fixtures, setFixtures] = useState(null);
  const [error, setError] = useState(null);
  const [tab, setTab] = useState("squad");

  useEffect(() => {
    setRoster(null);
    setFixtures(null);
    setError(null);
    setTab("squad");
    getRoster(id, clubName).catch(() => setError("Effectif indisponible pour ce club.")).then((r) => r && setRoster(r));
    getClubFixtures(id, clubName).then(setFixtures).catch(() => setFixtures(null));
  }, [id, clubName]);

  return (
    <div className="p-3 flex flex-col gap-3">
      <div className="mx-auto w-full max-w-4xl flex flex-col gap-3">
        {error && <p className="text-sm text-gray-400 px-1">{error}</p>}
        {!error && !roster && <p className="text-sm text-gray-400 px-1">Chargement…</p>}

        {roster && (
          <>
            <TeamHeader roster={roster} form={fixtures?.form} />
            {fixtures && (
              <div role="tablist" className="flex gap-1 border-b border-line">
                <TabButton active={tab === "squad"} onClick={() => setTab("squad")} label="Effectif" />
                <TabButton active={tab === "fixtures"} onClick={() => setTab("fixtures")} label="Calendrier" />
              </div>
            )}
            {tab === "fixtures" && fixtures ? <FixturesList fixtures={fixtures} /> : <RosterTable players={roster.players} club={clubName} />}
          </>
        )}
      </div>
    </div>
  );
}

function TabButton({ active, onClick, label }) {
  return (
    <button
      role="tab"
      aria-selected={active}
      onClick={onClick}
      className={`min-h-11 md:min-h-9 px-4 text-sm border-b-2 -mb-px ${
        active ? "border-accent text-white font-semibold" : "border-transparent text-gray-400 hover:text-gray-200"
      }`}
    >
      {label}
    </button>
  );
}
