import { useEffect, useState } from "react";
import { Trophy, Wand2, Star, Medal, Plus, Users, Zap, ArrowRight } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { createChampionsLeague, createWorldCup, getCompetition } from "../api/client";
import { useGameStore } from "../store/useGameStore";

// Nombre de joueurs de la base -- voir data/joueurs.xlsx (7 564 au
// 28/09/2026, PROJET_SIMULAFOOT.md §8.4). Statique : pas d'endpoint dédié
// pour l'interroger en direct depuis l'écran d'accueil aujourd'hui.
const PLAYER_COUNT = 7564;

// "Sélections nationales" retirée (28/09/2026) : les sélections restent
// jouables, mais uniquement via Compétition Perso (1er choix du nouvel
// assistant, voir CustomCompetition.jsx) -- plus de tuile dédiée qui faisait
// double emploi.
const OFFICIAL_COMPETITIONS = [
  {
    to: "/leagues",
    icon: Trophy,
    title: "Championnats nationaux",
    description: "Les 8 grands championnats européens, un par pays.",
  },
];

// Refonte de l'écran d'accueil (28/09/2026, audit UX collé par l'utilisateur) :
// hiérarchie visuelle (titre + compteur joueurs), un seul système de carte
// (le jaune redevient réservé aux compétitions "premium" CL/CDM plutôt que de
// coder une fausse sélection), contraste de texte relevé, grille responsive
// avec défilement horizontal à ancrage sur mobile plutôt qu'un overflow.
export default function Home() {
  const navigate = useNavigate();
  const setActiveCompetition = useGameStore((s) => s.setActiveCompetition);
  const [launching, setLaunching] = useState(null); // "cl" | "wc" | null

  async function launch(create, key) {
    setLaunching(key);
    try {
      const status = await create();
      setActiveCompetition(status.id, status.championnat);
      navigate(`/competition/${status.id}/groups`);
    } finally {
      setLaunching(null);
    }
  }

  return (
    <div className="p-4 sm:p-6 max-w-5xl mx-auto">
      <header className="mb-7">
        <h1 className="font-display text-2xl font-bold text-white">Choisis ta compétition</h1>
        <p className="mt-1.5 text-data leading-snug text-gray-400 max-w-md">
          Simule une saison complète dans un grand championnat, ou construis ta propre compétition avec les clubs et
          sélections de ton choix.
        </p>
        <div className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-accent/10 border border-accent/30 px-3 py-1 text-data font-medium text-link">
          <Users size={13} /> {PLAYER_COUNT.toLocaleString("fr-FR")} joueurs disponibles
        </div>
      </header>

      <ResumeCard />

      <section className="mb-7">
        <h2 className="text-data font-bold uppercase tracking-wide text-gray-500 mb-3">Compétitions officielles</h2>
        <CardRow>
          {OFFICIAL_COMPETITIONS.map(({ to, icon: Icon, title, description }) => (
            <Tile key={to} icon={Icon} title={title} description={description} onClick={() => navigate(to)} />
          ))}

          <Tile
            icon={Star}
            title="Ligue des Champions"
            description="36 clubs : phase de ligue à 8 matchs, barrages, 8es et finale sèche."
            premium
            loading={launching === "cl"}
            onClick={() => launch(createChampionsLeague, "cl")}
          />

          <Tile
            icon={Medal}
            title="Coupe du Monde"
            description="32 sélections, poules par chapeau puis élimination directe."
            premium
            loading={launching === "wc"}
            onClick={() => launch(createWorldCup, "wc")}
          />
        </CardRow>
      </section>

      <section className="mb-7">
        <h2 className="text-data font-bold uppercase tracking-wide text-gray-500 mb-3">Création</h2>
        <CardRow>
          <CreateTile
            icon={Wand2}
            title="Compétition perso"
            description="Clubs ou sélections, puis le format de ton choix : championnat, championnat + élimination, ou élimination directe."
            onClick={() => navigate("/custom")}
          />
        </CardRow>
      </section>

      <section>
        <h2 className="text-data font-bold uppercase tracking-wide text-gray-500 mb-3">Expérimental</h2>
        <CardRow>
          <Tile
            icon={Zap}
            title="Version 2 (bêta)"
            description="Moteur physique piloté par les attributs réels des joueurs : l'issue émerge de la simulation, aucun score décidé à l'avance."
            onClick={() => navigate("/v2")}
          />
        </CardRow>
      </section>
    </div>
  );
}

// Sur mobile : rangée à défilement horizontal avec ancrage (une carte à la
// fois, pas de grille qui déborderait). À partir de `sm` : grille normale,
// le défilement redevient un simple wrap.
function CardRow({ children }) {
  return (
    <div
      className="flex gap-3 overflow-x-auto snap-x snap-mandatory pb-1 -mx-4 px-4
                 sm:mx-0 sm:px-0 sm:grid sm:grid-cols-2 sm:overflow-visible lg:grid-cols-3"
    >
      {children}
    </div>
  );
}

function Tile({ icon: Icon, title, description, premium, loading, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={loading}
      className="rounded-xl p-5 flex flex-col items-start gap-2 text-left bg-surface border border-line
                 hover:bg-surface-2 hover:border-gray-700 transition-colors
                 min-h-[160px] w-[280px] shrink-0 snap-start sm:w-auto sm:shrink disabled:opacity-60"
    >
      <Icon size={28} className={premium ? "text-gold" : "text-link"} />
      <h3 className="font-semibold text-sm text-white">{title}</h3>
      <p className="text-data leading-snug text-gray-400">{loading ? "Tirage des poules…" : description}</p>
    </button>
  );
}

// Carte "Create" distincte des cartes de navigation (icône +, label "Nouveau")
// plutôt qu'une simple variante en pointillés -- évite la confusion avec le
// jaune "premium" (retour audit UX du 28/09/2026).
function CreateTile({ icon: Icon, title, description, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="rounded-xl p-5 flex items-center gap-4 text-left bg-surface border-2 border-dashed border-accent/40
                 hover:bg-surface-2 hover:border-accent/60 transition-colors
                 min-h-[100px] w-[280px] shrink-0 snap-start sm:w-auto sm:shrink"
    >
      <div className="h-11 w-11 rounded-full bg-accent/15 flex items-center justify-center shrink-0">
        <Plus size={22} className="text-link" />
      </div>
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <Icon size={16} className="text-link shrink-0" />
          <h3 className="font-semibold text-sm text-white">{title}</h3>
          <span className="text-caption font-bold uppercase tracking-wide text-link bg-accent/10 rounded-full px-1.5 py-0.5">
            Nouveau
          </span>
        </div>
        <p className="mt-1 text-data leading-snug text-gray-400">{description}</p>
      </div>
    </button>
  );
}

// « Reprendre » (refonte UI, lot 2) : la compétition en cours, mémorisée dans
// le store persistant. Vérifiée auprès de l'API à chaque affichage : elle vit en
// mémoire côté serveur, un 404 (API redémarrée) l'efface ; une erreur réseau
// la garde (l'API peut juste être en train de démarrer).
function ResumeCard() {
  const activeId = useGameStore((s) => s.activeCompetitionId);
  const clearActiveCompetition = useGameStore((s) => s.clearActiveCompetition);
  const [status, setStatus] = useState(null);

  useEffect(() => {
    if (!activeId) return;
    let alive = true;
    getCompetition(activeId)
      .then((s) => alive && setStatus(s))
      .catch((err) => alive && err.status === 404 && clearActiveCompetition());
    return () => {
      alive = false;
    };
  }, [activeId, clearActiveCompetition]);

  if (!activeId || status?.id !== activeId) return null;
  const progress = status.champion
    ? `Terminée · Champion : ${status.champion}`
    : status.total_journees
      ? `Journée ${status.current_journee} / ${status.total_journees}`
      : "En cours";

  return (
    <Link
      to={`/competition/${activeId}`}
      className="mb-7 flex items-center gap-4 rounded-xl bg-surface border border-line px-5 py-4 hover:bg-surface-2 transition-colors"
    >
      <div className="min-w-0 flex-1">
        <div className="text-caption font-bold uppercase tracking-wide text-link">Reprendre</div>
        <div className="font-display text-2xl font-bold text-white truncate">{status.championnat ?? "Compétition perso"}</div>
        <div className="text-data text-gray-400">{progress}</div>
      </div>
      <ArrowRight size={22} className="text-link shrink-0" />
    </Link>
  );
}
