import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ListOrdered, LoaderCircle } from "lucide-react";
import {
  getCompetition,
  getStandings,
  getLeaderboards,
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
  const [leaderboards, setLeaderboards] = useState(null);
  const [loading, setLoading] = useState(false);
  const [launching, setLaunching] = useState(false); // « Lancement du live… » (simulation de la journée avant le premier live)
  const [error, setError] = useState(null);

  // Charge le calendrier de la journée courante -- joué ou pas encore : les
  // matchs à venir doivent être visibles AVANT simulation (MatchRow affiche
  // "– –" pour un match non joué), pas seulement une fois le résultat connu.
  // Buteurs/passeurs (`leaderboards`) rechargés à CHAQUE action de simulation
  // (voir handleToggle/handleSimulateAll ci-dessous), pas seulement ici --
  // sans ça, le mini classement affiché à côté restait figé sur les buts de
  // la toute première journée jusqu'à la fin de la saison (anomalie
  // remontée le 28/09/2026 : meilleur buteur à 2 buts après une saison
  // complète).
  const load = useCallback(async () => {
    try {
      const s = await getCompetition(id);
      const [journeeMatches, standingsRows, boards] = await Promise.all([
        getMatches(id, s.current_journee),
        getStandings(id),
        getLeaderboards(id),
      ]);
      setStatus(s);
      setMatches(journeeMatches);
      setStandings(standingsRows);
      setLeaderboards(boards);
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
        setLeaderboards(await getLeaderboards(id)); // buts/passes de cette journée viennent de s'ajouter
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
      const [lastJournee, boards] = await Promise.all([
        getMatches(id, res.status.current_journee),
        getLeaderboards(id),
      ]);
      setStatus(res.status);
      setMatches(lastJournee);
      setStandings(res.standings);
      setLeaderboards(boards);
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

        <div className="flex-1 min-h-0 overflow-y-auto flex flex-col gap-1.5">
          {matches.map((m) => (
            <MatchRow key={`${m.home}-${m.away}`} match={m} onClick={() => openPitch(m)} onLive={() => openLive(m)} />
          ))}
        </div>

        {/* Boutons d'action sous la liste des matchs plutôt qu'en survol
            flottant -- retour terrain du 28/09/2026, pour que le geste
            "simuler" reste ancré au flux de la journée au lieu de flotter
            par-dessus le classement condensé à droite. Centrés, agrandis. */}
        {!status?.is_over && (
          <div className="shrink-0 pt-2 flex items-center justify-center gap-3">
            <button
              onClick={handleSimulateAll}
              disabled={loading}
              className="h-11 px-5 rounded-full bg-surface border border-white/10 text-sm font-medium text-gray-300
                         hover:bg-white/5 active:scale-95 transition-transform disabled:opacity-40"
            >
              Simuler tout
            </button>
            <button
              onClick={handleToggle}
              disabled={loading}
              className="h-14 px-8 rounded-full bg-accent text-white font-semibold text-base shadow-lg shadow-accent/30
                         hover:brightness-110 active:scale-95 transition-transform disabled:opacity-40"
            >
              {loading ? "…" : buttonLabel}
            </button>
          </div>
        )}
      </div>

      <MiniStandings standings={standings} leaderboards={leaderboards} className="hidden md:flex w-[39rem] shrink-0" />

      {launching && (
        <div role="status" className="fixed inset-0 z-50 flex flex-col items-center justify-center gap-3 bg-black/70 backdrop-blur-sm">
          <LoaderCircle size={36} className="animate-spin text-live" />
          <span className="text-sm font-semibold text-slate-100">Lancement du live...</span>
        </div>
      )}
    </div>
  );

  // Bouton LIVE d'une ligne, toujours actif. Match déjà joué : on ouvre directement son live (rejoué à l'horloge accélérée).
  // Match pas encore joué : le moteur simule la journée d'un bloc (les résultats des autres matchs alimentent les alertes buts du live),
  // puis on ouvre le live du match. `replay=1` : le live part de la minute 0.
  async function openLive(match) {
    if (match.played) {
      openPitch(match, "live");
      return;
    }
    setLaunching(true);
    setError(null);
    try {
      const res = await simulateCurrent(id);
      setStatus(res.status);
      setMatches(res.matches_played);
      setStandings(res.standings);
      setLeaderboards(await getLeaderboards(id));
      const played = res.matches_played.find((m) => m.home === match.home && m.away === match.away);
      openPitch(played ?? match, "live", res.status.current_journee);
    } catch {
      setError("Échec du lancement du live.");
    } finally {
      setLaunching(false);
    }
  }

  // `tab` : "live" ouvre l'écran match sur l'onglet commentaire en direct ; sinon onglet terrain (par défaut).
  function openPitch(match, tab, journee = status.current_journee) {
    if (!match.played) return;
    const qs = new URLSearchParams({ journee, home: match.home, away: match.away });
    if (tab) qs.set("tab", tab);
    if (tab === "live") qs.set("replay", "1");
    navigate(`/competition/${id}/pitch?${qs}`);
  }
}
