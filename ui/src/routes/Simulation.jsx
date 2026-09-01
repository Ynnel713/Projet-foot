import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ListOrdered } from "lucide-react";
import {
  getCompetition,
  getStandings,
  getMatches,
  simulateCurrent,
  advanceJournee,
  simulateAll,
} from "../api/client";
import ProgressBar from "../components/simulation/ProgressBar";
import MatchRow from "../components/simulation/MatchRow";
import MiniStandings from "../components/simulation/MiniStandings";

export default function Simulation() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState(null);
  const [matches, setMatches] = useState([]);
  const [standings, setStandings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Charge le calendrier de la journée courante -- joué ou pas encore : les
  // matchs à venir doivent être visibles AVANT simulation (MatchRow affiche
  // "– –" pour un match non joué), pas seulement une fois le résultat connu.
  const load = useCallback(async () => {
    try {
      const s = await getCompetition(id);
      const [journeeMatches, standingsRows] = await Promise.all([
        getMatches(id, s.current_journee),
        getStandings(id),
      ]);
      setStatus(s);
      setMatches(journeeMatches);
      setStandings(standingsRows);
    } catch {
      setError("Compétition introuvable.");
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  // Bouton unique qui alterne, comme sur l'écran Streamlit d'origine :
  // "Simuler la journée" tant que la journée courante n'a pas été jouée,
  // puis "Journée suivante" une fois jouée -- deux actions distinctes
  // (simuler / avancer) plutôt qu'un seul clic qui faisait les deux.
  async function handleToggle() {
    setLoading(true);
    setError(null);
    try {
      if (status?.current_journee_played) {
        const res = await advanceJournee(id);
        setStatus(res.status);
        setMatches(res.matches_played); // calendrier à venir de la nouvelle journée, pas encore joué
        setStandings(res.standings);
      } else {
        const res = await simulateCurrent(id);
        setStatus(res.status);
        setMatches(res.matches_played); // désormais joués, avec les scores -- tous affichés d'un coup
        setStandings(res.standings);
      }
    } catch {
      setError("Échec de l'opération.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSimulateAll() {
    setLoading(true);
    setError(null);
    try {
      const res = await simulateAll(id);
      const lastJournee = await getMatches(id, res.status.current_journee);
      setStatus(res.status);
      setMatches(lastJournee);
      setStandings(res.standings);
    } catch {
      setError("Échec de la simulation.");
    } finally {
      setLoading(false);
    }
  }

  if (error) {
    return (
      <div className="p-6 text-sm text-gray-400 flex flex-col gap-3 items-start">
        <p>{error}</p>
        <button onClick={() => navigate("/")} className="text-accent text-sm font-medium">
          ← Retour à l'accueil
        </button>
      </div>
    );
  }

  const buttonLabel = status?.current_journee_played ? "Journée suivante →" : "Simuler la journée";

  return (
    <div className="flex h-full">
      <div className="flex-1 min-w-0 flex flex-col p-3 gap-2">
        <div className="flex items-center gap-2 shrink-0">
          <div className="flex-1">
            <ProgressBar current={status?.current_journee} total={status?.total_journees} />
          </div>
          <button
            onClick={() => navigate(`/competition/${id}/standings`)}
            className="h-9 px-3 rounded-lg bg-surface border border-white/10 text-xs font-medium text-gray-200 flex items-center gap-1.5 shrink-0"
          >
            <ListOrdered size={14} /> Classement
          </button>
        </div>

        {status?.is_over && (
          <div className="shrink-0 rounded-lg bg-gold/10 border border-gold/30 text-gold text-sm px-3 py-2 text-center font-semibold">
            🏆 Champion : {status.champion}
          </div>
        )}

        <div className="flex-1 min-h-0 overflow-y-auto flex flex-col gap-1.5 pb-16">
          {matches.map((m) => (
            <MatchRow key={`${m.home}-${m.away}`} match={m} onClick={() => openPitch(m)} />
          ))}
        </div>
      </div>

      <MiniStandings standings={standings} className="hidden md:flex w-56 shrink-0" />

      {!status?.is_over && (
        <div className="fixed bottom-20 right-3 flex flex-col items-end gap-2">
          <button
            onClick={handleSimulateAll}
            disabled={loading}
            className="h-9 px-4 rounded-full bg-surface border border-white/10 text-xs font-medium text-gray-300
                       active:scale-95 transition-transform disabled:opacity-40"
          >
            Simuler tout
          </button>
          <button
            onClick={handleToggle}
            disabled={loading}
            className="h-12 px-5 rounded-full bg-accent text-white font-medium shadow-lg shadow-accent/30
                       active:scale-95 transition-transform disabled:opacity-40"
          >
            {loading ? "…" : buttonLabel}
          </button>
        </div>
      )}
    </div>
  );

  function openPitch(match) {
    if (!match.played) return;
    const qs = new URLSearchParams({ journee: status.current_journee, home: match.home, away: match.away });
    navigate(`/competition/${id}/pitch?${qs}`);
  }
}
