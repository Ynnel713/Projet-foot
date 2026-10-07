import { useState } from "react";
import { Trophy, Wand2, Star, Medal, Plus, Users } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { createChampionsLeague, createWorldCup } from "../api/client";
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
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Choisis ta compétition</h1>
        <p className="mt-1.5 text-[13px] leading-snug text-[#9AA9C3] max-w-md">
          Simule une saison complète dans un grand championnat, ou construis ta propre compétition avec les clubs et
          sélections de ton choix.
        </p>
        <div className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-accent/10 border border-accent/30 px-3 py-1 text-xs font-medium text-accent">
          <Users size={13} /> {PLAYER_COUNT.toLocaleString("fr-FR")} joueurs disponibles
        </div>
      </header>

      <section className="mb-7">
        <h2 className="text-xs font-bold uppercase tracking-wide text-gray-500 mb-3">Compétitions officielles</h2>
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

      <section>
        <h2 className="text-xs font-bold uppercase tracking-wide text-gray-500 mb-3">Création</h2>
        <CardRow>
          <CreateTile
            icon={Wand2}
            title="Compétition perso"
            description="Clubs ou sélections, puis le format de ton choix : championnat, championnat + élimination, ou élimination directe."
            onClick={() => navigate("/custom")}
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
    <motion.button
      type="button"
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      transition={{ duration: 0.2 }}
      onClick={onClick}
      disabled={loading}
      className="rounded-2xl p-5 flex flex-col items-start gap-2 text-left bg-surface border border-white/10
                 hover:bg-white/[0.04] hover:border-white/20 transition-colors
                 min-h-[160px] w-[280px] shrink-0 snap-start sm:w-auto sm:shrink disabled:opacity-60"
    >
      <Icon size={28} className={premium ? "text-gold" : "text-accent"} />
      <h3 className="font-semibold text-sm text-white">{title}</h3>
      <p className="text-[13px] leading-snug text-[#9AA9C3]">{loading ? "Tirage des poules…" : description}</p>
    </motion.button>
  );
}

// Carte "Create" distincte des cartes de navigation (icône +, label "Nouveau")
// plutôt qu'une simple variante en pointillés -- évite la confusion avec le
// jaune "premium" (retour audit UX du 28/09/2026).
function CreateTile({ icon: Icon, title, description, onClick }) {
  return (
    <motion.button
      type="button"
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      transition={{ duration: 0.2 }}
      onClick={onClick}
      className="rounded-2xl p-5 flex items-center gap-4 text-left bg-surface border-2 border-dashed border-accent/40
                 hover:bg-white/[0.04] hover:border-accent/60 transition-colors
                 min-h-[100px] w-[280px] shrink-0 snap-start sm:w-auto sm:shrink"
    >
      <div className="h-11 w-11 rounded-full bg-accent/15 flex items-center justify-center shrink-0">
        <Plus size={22} className="text-accent" />
      </div>
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <Icon size={16} className="text-accent shrink-0" />
          <h3 className="font-semibold text-sm text-white">{title}</h3>
          <span className="text-[10px] font-bold uppercase tracking-wide text-accent bg-accent/10 rounded-full px-1.5 py-0.5">
            Nouveau
          </span>
        </div>
        <p className="mt-1 text-[13px] leading-snug text-[#9AA9C3]">{description}</p>
      </div>
    </motion.button>
  );
}
