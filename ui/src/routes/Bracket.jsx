import { useEffect, useState, useCallback } from "react";
import { useParams } from "react-router-dom";
import { getBracket, simulateBracketRound, advanceBracketRound } from "../api/client";

export default function Bracket() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    getBracket(id)
      .then(setData)
      .catch(() => setError("Phase à élimination pas encore commencée."));
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleToggle() {
    setLoading(true);
    try {
      const current = data.rounds[data.rounds.length - 1];
      setData(current.played ? await advanceBracketRound(id) : await simulateBracketRound(id));
    } finally {
      setLoading(false);
    }
  }

  if (error) return <div className="p-6 text-sm text-gray-400">{error}</div>;
  if (!data) return <div className="p-6 text-sm text-gray-400">Chargement…</div>;

  const currentRound = data.rounds[data.rounds.length - 1];
  const buttonLabel = currentRound.played ? "Tour suivant →" : "Simuler ce tour";

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 min-h-0 overflow-y-auto p-3">
        <h2 className="text-xs font-semibold text-gray-400 mb-2">Tour {currentRound.number}</h2>

        {data.is_complete && (
          <div className="rounded-lg bg-gold/10 border border-gold/30 text-gold text-sm px-3 py-2 text-center font-semibold mb-3">
            🏆 Champion : {data.champion}
          </div>
        )}

        <div className="flex flex-col gap-1.5">
          {currentRound.ties.map((t) => (
            <div
              key={`${t.home}-${t.away ?? "bye"}`}
              className="flex items-center justify-between bg-surface rounded-lg px-3 py-2 min-h-[44px] text-sm"
            >
              <span className={`flex-1 min-w-0 truncate ${t.winner === t.home ? "font-semibold text-gold" : ""}`}>
                {t.home}
              </span>
              <span className="font-bold tabular-nums px-3 shrink-0">
                {t.is_bye ? "exempt" : t.home_goals != null ? `${t.home_goals} - ${t.away_goals}` : "– –"}
              </span>
              <span
                className={`flex-1 min-w-0 truncate text-right ${t.winner === t.away ? "font-semibold text-gold" : ""}`}
              >
                {t.away ?? ""}
              </span>
            </div>
          ))}
        </div>
      </div>

      {!data.is_complete && (
        <div className="shrink-0 p-3 border-t border-white/5">
          <button
            onClick={handleToggle}
            disabled={loading}
            className="w-full h-12 rounded-xl bg-accent text-white font-semibold disabled:opacity-40"
          >
            {loading ? "…" : buttonLabel}
          </button>
        </div>
      )}
    </div>
  );
}
