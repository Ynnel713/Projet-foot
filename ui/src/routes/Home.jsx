import { useState } from "react";
import { Trophy, Globe2, Wand2, Star } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { createChampionsLeague } from "../api/client";
import { useGameStore } from "../store/useGameStore";

const NAV_TILES = [
  {
    to: "/leagues",
    icon: Trophy,
    title: "Championnats nationaux",
    description: "Les 8 grands championnats européens, un par pays.",
  },
  {
    to: "/nations",
    icon: Globe2,
    title: "Sélections nationales",
    description: "Les équipes nationales complètes, groupées par confédération.",
  },
];

export default function Home() {
  const navigate = useNavigate();
  const setActiveCompetition = useGameStore((s) => s.setActiveCompetition);
  const [launchingCL, setLaunchingCL] = useState(false);

  async function launchChampionsLeague() {
    setLaunchingCL(true);
    try {
      const status = await createChampionsLeague();
      setActiveCompetition(status.id, status.championnat, status.format);
      navigate(`/competition/${status.id}/groups`);
    } finally {
      setLaunchingCL(false);
    }
  }

  return (
    <div className="h-full flex flex-col items-center justify-center gap-4 p-4">
      <div className="grid grid-cols-4 gap-4 w-full max-w-4xl">
        {NAV_TILES.map(({ to, icon: Icon, title, description }) => (
          <Tile key={to} icon={Icon} title={title} description={description} onClick={() => navigate(to)} />
        ))}

        <Tile
          icon={Star}
          title="Ligue des Champions"
          description="36 clubs, poules par chapeau puis élimination directe."
          gold
          loading={launchingCL}
          onClick={launchChampionsLeague}
        />

        <Tile
          icon={Wand2}
          title="Compétition perso"
          description="Choisis le format et les équipes toi-même : clubs, sélections, ou un mélange des deux."
          dashed
          onClick={() => navigate("/custom")}
        />
      </div>
    </div>
  );
}

function Tile({ icon: Icon, title, description, dashed, gold, loading, onClick }) {
  return (
    <motion.button
      type="button"
      whileHover={{ scale: 1.03 }}
      whileTap={{ scale: 0.98 }}
      transition={{ duration: 0.2 }}
      onClick={onClick}
      disabled={loading}
      className={`rounded-2xl p-5 flex flex-col items-start gap-2 text-left bg-surface min-h-[160px] disabled:opacity-60 ${
        dashed ? "border-2 border-dashed border-gold/60" : gold ? "border border-gold/40" : "border border-white/5"
      }`}
    >
      <Icon size={28} className={dashed || gold ? "text-gold" : "text-accent"} />
      <h2 className="font-semibold text-sm">{title}</h2>
      <p className="text-xs text-gray-400 leading-snug">{loading ? "Tirage des poules…" : description}</p>
    </motion.button>
  );
}
