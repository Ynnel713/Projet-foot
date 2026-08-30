import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { getNations, createCompetition } from "../api/client";
import { useGameStore } from "../store/useGameStore";

const LEGS_LABELS = { 1: "Aller simple", 2: "Aller-retour", 4: "Double aller-retour" };

export default function Nations() {
  const navigate = useNavigate();
  const setActiveCompetition = useGameStore((s) => s.setActiveCompetition);

  const [pool, setPool] = useState([]);
  const [confederation, setConfederation] = useState("Toutes");
  const [selected, setSelected] = useState([]);
  const [teamCount, setTeamCount] = useState(8);
  const [legs, setLegs] = useState(2);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    getNations().then((nations) => setPool([...nations].sort((a, b) => b.strength - a.strength)));
  }, []);

  const confederations = useMemo(() => ["Toutes", ...new Set(pool.map((n) => n.confederation))], [pool]);
  const filtered = useMemo(
    () => pool.filter((n) => confederation === "Toutes" || n.confederation === confederation),
    [pool, confederation],
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
    <div className="flex h-full">
      <div className="w-64 shrink-0 p-4 flex flex-col gap-4 border-r border-white/5 overflow-y-auto">
        <button onClick={() => navigate("/")} className="flex items-center gap-1 text-xs text-gray-400">
          <ArrowLeft size={14} /> Accueil
        </button>

        <div>
          <label className="text-xs text-gray-400">Nombre de sélections</label>
          <div className="flex items-center gap-3 mt-1">
            <input
              type="range"
              min={2}
              max={Math.max(2, pool.length)}
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
            Sélections ({selected.length} / {teamCount})
          </label>
        </div>

        <div className="flex gap-1.5 overflow-x-auto shrink-0 pb-1">
          {confederations.map((c) => (
            <button
              key={c}
              onClick={() => setConfederation(c)}
              className={`h-8 px-3 rounded-full text-xs font-medium whitespace-nowrap border ${
                confederation === c ? "bg-accent border-accent text-white" : "bg-surface border-white/10 text-gray-300"
              }`}
            >
              {c}
            </button>
          ))}
        </div>

        <div className="flex-1 min-h-0 overflow-y-auto grid grid-cols-2 gap-1.5 content-start">
          {filtered.map((n) => {
            const isSelected = selected.includes(n.name);
            return (
              <button
                key={n.name}
                onClick={() => toggle(n.name)}
                disabled={!isSelected && selected.length >= teamCount}
                className={`flex items-center justify-between px-3 py-2 rounded-lg text-sm min-h-[44px] text-left ${
                  isSelected ? "bg-accent/20 border border-accent/50" : "bg-surface border border-transparent"
                } disabled:opacity-30`}
              >
                <span className="truncate">{n.name}</span>
                <span className="text-[10px] text-gray-500 shrink-0 pl-2">{n.confederation}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
