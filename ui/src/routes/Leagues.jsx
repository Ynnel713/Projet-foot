import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { getLeagues, createCompetition } from "../api/client";
import { useGameStore } from "../store/useGameStore";
import LeagueCard from "../components/league/LeagueCard";

// Nom affiché pour un pays qui regroupe plusieurs championnats (ex.
// Angleterre : Premier League + Championship) -- un seul pays a plusieurs
// championnats simulables aujourd'hui, mais la logique de groupement
// ci-dessous reste générique si ça change.
const COUNTRY_NAMES = { "gb-eng": "Angleterre" };

export default function Leagues() {
  const [leagues, setLeagues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [launching, setLaunching] = useState(null);
  const [drilldown, setDrilldown] = useState(null); // country_code en cours de détail, ou null
  const navigate = useNavigate();
  const setActiveCompetition = useGameStore((s) => s.setActiveCompetition);

  useEffect(() => {
    getLeagues()
      .then(setLeagues)
      .finally(() => setLoading(false));
  }, []);

  // Groupe par pays : un seul championnat -> carte normale ; plusieurs
  // (Angleterre) -> une carte pays unique qui ouvre un sous-choix.
  const groups = useMemo(() => {
    const byCountry = new Map();
    for (const l of leagues) {
      const key = l.country_code ?? l.championnat;
      if (!byCountry.has(key)) byCountry.set(key, []);
      byCountry.get(key).push(l);
    }
    return [...byCountry.entries()];
  }, [leagues]);

  async function launchLeague(championnat) {
    setLaunching(championnat);
    try {
      const status = await createCompetition({ format: "LEAGUE", legs: 2, source: "league", championnat });
      setActiveCompetition(status.id, status.championnat, status.format);
      navigate(`/competition/${status.id}/simulate`);
    } finally {
      setLaunching(null);
    }
  }

  const drilldownLeagues = drilldown ? groups.find(([code]) => code === drilldown)?.[1] : null;

  return (
    <div className="p-4">
      <button
        onClick={() => (drilldownLeagues ? setDrilldown(null) : navigate("/"))}
        className="flex items-center gap-1 text-xs text-gray-400 mb-3"
      >
        <ArrowLeft size={14} /> {drilldownLeagues ? "Tous les championnats" : "Accueil"}
      </button>

      {loading && <p className="text-sm text-gray-400">Chargement des championnats…</p>}

      {!loading && !drilldownLeagues && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {groups.map(([code, group]) =>
            group.length === 1 ? (
              <LeagueCard
                key={code}
                name={launching === group[0].championnat ? "Lancement…" : group[0].championnat}
                nbClubs={group[0].nb_clubs}
                countryCode={group[0].country_code}
                onLaunch={() => launchLeague(group[0].championnat)}
              />
            ) : (
              <LeagueCard
                key={code}
                name={COUNTRY_NAMES[code] ?? code}
                subtitle={`${group.length} championnats`}
                cta="Choisir →"
                countryCode={code}
                onLaunch={() => setDrilldown(code)}
              />
            ),
          )}
        </div>
      )}

      {!loading && drilldownLeagues && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {drilldownLeagues.map((l) => (
            <LeagueCard
              key={l.championnat}
              name={launching === l.championnat ? "Lancement…" : l.championnat}
              nbClubs={l.nb_clubs}
              countryCode={l.country_code}
              onLaunch={() => launchLeague(l.championnat)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
