import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getGroups, simulateGroupsMatchday, startKnockout } from "../api/client";

export default function Groups() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    getGroups(id)
      .then(setData)
      .catch(() => setError("Compétition introuvable."));
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleSimulate() {
    setLoading(true);
    try {
      setData(await simulateGroupsMatchday(id));
    } finally {
      setLoading(false);
    }
  }

  async function handleStartKnockout() {
    setLoading(true);
    try {
      await startKnockout(id);
      navigate(`/competition/${id}/bracket`);
    } finally {
      setLoading(false);
    }
  }

  if (error) return <div className="p-6 text-sm text-gray-400">{error}</div>;
  if (!data) return <div className="p-6 text-sm text-gray-400">Chargement…</div>;

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 min-h-0 overflow-y-auto p-3 grid grid-cols-3 gap-2">
        {data.groups.map((g) => (
          <div key={g.name} className="bg-surface rounded-lg p-2">
            <div className="flex items-center justify-between mb-1">
              <h3 className="text-xs font-semibold text-gray-300">{g.name}</h3>
              {g.is_complete && <span className="text-[10px] text-emerald-400">Terminée</span>}
            </div>
            {g.standings.map((row) => (
              <div key={row.club} className="flex items-center justify-between text-[11px] text-gray-300 py-0.5">
                <span className="w-3 text-gray-500">{row.rank}</span>
                <span className="flex-1 min-w-0 truncate px-1">{row.club}</span>
                <span className="tabular-nums font-semibold">{row.points}</span>
              </div>
            ))}

            {/* Résultats de la dernière journée jouée -- pas tout
                l'historique (trop dense sur 9 poules à la fois), juste ce
                qui vient de se jouer. */}
            {g.current_matches.length > 0 && (
              <div className="flex flex-col gap-0.5 mt-1.5 pt-1.5 border-t border-white/5">
                {g.current_matches.map((m) => (
                  <div key={`${m.home}-${m.away}`} className="flex items-center justify-between text-[10px] text-gray-400">
                    <span className="flex-1 min-w-0 truncate">{m.home}</span>
                    <span className="tabular-nums font-semibold text-gray-200 px-1.5 shrink-0">
                      {m.home_goals} - {m.away_goals}
                    </span>
                    <span className="flex-1 min-w-0 truncate text-right">{m.away}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="shrink-0 p-3 border-t border-white/5">
        {data.groups_complete ? (
          <button
            onClick={handleStartKnockout}
            disabled={loading}
            className="w-full h-12 rounded-xl bg-gold text-bg font-semibold disabled:opacity-40"
          >
            {loading ? "…" : "🏆 Lancer les phases finales →"}
          </button>
        ) : (
          <button
            onClick={handleSimulate}
            disabled={loading}
            className="w-full h-12 rounded-xl bg-accent text-white font-semibold disabled:opacity-40"
          >
            {loading ? "…" : "Simuler la journée des poules"}
          </button>
        )}
      </div>
    </div>
  );
}
