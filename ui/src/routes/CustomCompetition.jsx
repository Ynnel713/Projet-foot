import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { getPersoClubs, getNations, createCompetition } from "../api/client";
import { useGameStore } from "../store/useGameStore";
import { parseFlaggedName, flagUrl } from "../utils/flags";

const MAX_TEAM_COUNT = 50;

const LEGS_LABELS = { 1: "Aller simple", 2: "Aller-retour", 4: "Double aller-retour" };

export default function CustomCompetition() {
  const navigate = useNavigate();
  const setActiveCompetition = useGameStore((s) => s.setActiveCompetition);

  const [pool, setPool] = useState([]);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState([]);
  const [teamCount, setTeamCount] = useState(18);
  const [legs, setLegs] = useState(2);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    // Clubs ET sélections nationales mélangés, sans restriction (voir
    // api.routers.competitions.create_competition) -- même vivier "sans
    // limite" que la Compétition Perso d'origine.
    Promise.all([getPersoClubs(), getNations()]).then(([clubs, nations]) => {
      const combined = [
        ...clubs.map((c) => ({ name: c.name, category: c.championnat, strength: c.strength })),
        ...nations.map((n) => ({ name: n.name, category: n.confederation, strength: n.strength })),
      ];
      setPool(combined.sort((a, b) => b.strength - a.strength));
    });
  }, []);

  const filtered = useMemo(
    () => pool.filter((c) => c.name.toLowerCase().includes(search.toLowerCase())),
    [pool, search],
  );

  function toggle(name) {
    setSelected((prev) => (prev.includes(name) ? prev.filter((n) => n !== name) : [...prev, name]));
  }

  async function handleCreate() {
    setCreating(true);
    try {
      const status = await createCompetition({ format: "LEAGUE", legs, source: "custom", club_names: selected });
      setActiveCompetition(status.id, status.championnat, status.format);
      navigate(`/competition/${status.id}/simulate`);
    } finally {
      setCreating(false);
    }
  }

  const canCreate = selected.length === teamCount && selected.length >= 2 && selected.length % 2 === 0;

  return (
    // Deux colonnes plutôt qu'un empilement vertical : en paysage (ex.
    // 800x400), une seule colonne n'a pas la hauteur pour montrer le
    // formulaire ET une liste de clubs utilisable en même temps -- la
    // largeur disponible, elle, est abondante.
    <div className="flex h-full">
      <div className="w-64 shrink-0 p-4 flex flex-col gap-4 border-r border-white/5 overflow-y-auto">
        <button onClick={() => navigate("/")} className="flex items-center gap-1 text-xs text-gray-400">
          <ArrowLeft size={14} /> Accueil
        </button>
        <div>
          <label className="text-xs text-gray-400">Nombre d'équipes</label>
          <div className="flex items-center gap-3 mt-1">
            <input
              type="range"
              min={2}
              max={MAX_TEAM_COUNT}
              step={2}
              value={teamCount}
              onChange={(e) => setTeamCount(Number(e.target.value))}
              className="flex-1 accent-accent"
            />
            <span className="w-8 text-right font-semibold tabular-nums">{teamCount}</span>
          </div>
        </div>

        <div>
          <label className="text-xs text-gray-400">Confrontations</label>
          <div className="flex flex-col gap-1.5 mt-1">
            {Object.entries(LEGS_LABELS).map(([value, label]) => (
              <button
                key={value}
                onClick={() => setLegs(Number(value))}
                className={`h-10 rounded-lg text-xs font-medium border transition-colors ${
                  legs === Number(value)
                    ? "bg-accent border-accent text-white"
                    : "bg-surface border-white/10 text-gray-300"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        <button
          onClick={handleCreate}
          disabled={!canCreate || creating}
          className="mt-auto h-12 rounded-xl bg-accent text-white font-semibold disabled:opacity-30 active:scale-[0.98] transition-transform"
        >
          {creating ? "Création…" : "Créer et lancer"}
        </button>
      </div>

      <div className="flex-1 min-w-0 flex flex-col p-4 gap-2">
        <div className="flex items-center justify-between shrink-0">
          <label className="text-xs text-gray-400">
            Clubs ({selected.length} / {teamCount})
          </label>
        </div>
        <input
          type="text"
          placeholder="Rechercher un club…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="h-10 shrink-0 rounded-lg bg-surface border border-white/10 px-3 text-sm outline-none focus:border-accent"
        />

        {/* min-h-0 : indispensable pour qu'un enfant flex-1 overflow-y-auto
            se limite réellement à l'espace restant au lieu de pousser tout
            le parent à s'agrandir (voir AppShell pour le même besoin). */}
        <div className="flex-1 min-h-0 overflow-y-auto grid grid-cols-2 gap-1.5 content-start">
          {filtered.map((c) => {
            const isSelected = selected.includes(c.name);
            const { code, label } = parseFlaggedName(c.name);
            return (
              <button
                key={c.name}
                onClick={() => toggle(c.name)}
                disabled={!isSelected && selected.length >= teamCount}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm min-h-[44px] text-left ${
                  isSelected ? "bg-accent/20 border border-accent/50" : "bg-surface border border-transparent"
                } disabled:opacity-30`}
              >
                {code && <img src={flagUrl(code)} alt="" className="h-4 w-6 rounded-sm object-cover shrink-0" />}
                <span className="flex-1 min-w-0 truncate">{label}</span>
                <span className="text-[10px] text-gray-500 shrink-0 pl-2">{c.category}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
