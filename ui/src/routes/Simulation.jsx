import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate, useOutletContext } from "react-router-dom";
import { LoaderCircle } from "lucide-react";
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
import MatchRow from "../components/matches/MatchRow";
import MiniStandings from "../components/simulation/MiniStandings";
import ActionBar from "../components/common/ActionBar";
import AnimationDialog from "../components/pitch/AnimationDialog";

export default function Simulation() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { refresh } = useOutletContext();
  const [status, setStatus] = useState(null);
  const [matches, setMatches] = useState([]);
  const [standings, setStandings] = useState([]);
  const [leaderboards, setLeaderboards] = useState(null);
  const [loading, setLoading] = useState(false);
  const [launching, setLaunching] = useState(false); // « Lancement du live… » (simulation de la journée avant le premier live)
  const [error, setError] = useState(null);
  // Fenêtre « Voir l'animation » ouverte directement depuis la liste, sans passer par la fiche match qui révèle le
  // score (US-15/16, docs/PRD_PRODUIT.md) -- null = fermée, sinon le match concerné.
  const [animationMatch, setAnimationMatch] = useState(null);

  // Charge le calendrier de la journée courante -- joué ou pas encore : les
  // matchs à venir doivent être visibles AVANT simulation (MatchRow affiche
  // "– –" pour un match non joué), pas seulement une fois le résultat connu.
  // Buteurs/passeurs (`leaderboards`) rechargés à CHAQUE action de simulation
  // (voir handleToggle/handleSimulateAll ci-dessous), pas seulement ici --
  // sans ça, le classement affiché à côté restait figé sur les buts de
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
      refresh();
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
      const [lastJournee, boards] = await Promise.all([getMatches(id, res.status.current_journee), getLeaderboards(id)]);
      setStatus(res.status);
      setMatches(lastJournee);
      setStandings(res.standings);
      setLeaderboards(boards);
      refresh();
    } catch {
      setError("Échec de la simulation.");
    } finally {
      setLoading(false);
    }
  }

  // Bouton LIVE d'une ligne, toujours actif -- ouvre directement l'ANIMATION. Match déjà joué : animation immédiate, sans jamais
  // afficher le score au préalable (AnimationDialog/MatchAnimation n'affiche qu'un chronomètre de chargement, jamais le score ni le
  // commentaire). Match pas encore joué : le moteur simule la journée d'un bloc, puis l'animation du match s'ouvre automatiquement
  // -- aucune étape intermédiaire ne révèle quoi que ce soit sur CE match avant que l'animation ne commence.
  async function openLive(match) {
    if (match.played) {
      setAnimationMatch(match);
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
      setAnimationMatch(played ?? match);
      refresh();
    } catch {
      setError("Échec du lancement du live.");
    } finally {
      setLaunching(false);
    }
  }

  // Feuille de match d'un match joué (clic sur le score).
  function openSheet(match) {
    navigate(`/competition/${id}/pitch?${new URLSearchParams({ journee: status.current_journee, home: match.home, away: match.away })}`);
  }

  if (error) {
    return (
      <div className="p-6 text-sm text-gray-400 flex flex-col gap-3 items-start">
        <p>{error}</p>
        <button onClick={() => navigate("/")} className="text-link text-sm font-medium">
          ← Retour à l'accueil
        </button>
      </div>
    );
  }

  return (
    <div className="flex h-full">
      <div className="flex-1 min-w-0 flex flex-col">
        <div className="flex-1 min-h-0 overflow-y-auto p-3 flex flex-col gap-3">
          <ProgressBar current={status?.current_journee} total={status?.total_journees} />

          {status?.is_over && (
            <div className="rounded-lg bg-gold/10 border border-gold/30 text-gold text-sm px-3 py-2 text-center font-semibold">
              🏆 Champion : {status.champion}
            </div>
          )}

          <section className="rounded-xl bg-surface border border-line overflow-hidden">
            {matches.map((m) => (
              <MatchRow
                key={`${m.home}-${m.away}`}
                match={m}
                onOpenSheet={() => openSheet(m)}
                onLive={() => openLive(m)}
                onAnimation={() => setAnimationMatch(m)}
              />
            ))}
          </section>

          {animationMatch && (
            <AnimationDialog
              competitionId={id}
              matchParams={{ home: animationMatch.home, away: animationMatch.away, journee: status.current_journee }}
              onClose={() => setAnimationMatch(null)}
            />
          )}
        </div>

        {!status?.is_over && (
          <ActionBar
            primary={{
              label: status?.current_journee_played ? "Journée suivante →" : "Simuler la journée",
              onClick: handleToggle,
              loading,
            }}
            secondary={{ label: "Simuler tout", onClick: handleSimulateAll, disabled: loading }}
          />
        )}
      </div>

      <MiniStandings standings={standings} leaderboards={leaderboards} className="hidden lg:flex w-[26rem] shrink-0" />

      {launching && (
        <div role="status" className="fixed inset-0 z-50 flex flex-col items-center justify-center gap-3 bg-bg">
          <LoaderCircle size={36} className="animate-spin text-live" />
          <span className="text-sm font-semibold text-gray-100">Lancement du live...</span>
        </div>
      )}
    </div>
  );
}
