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
  const previousRounds = data.rounds.slice(0, -1);
  const buttonLabel = currentRound.played ? "Tour suivant →" : "Simuler ce tour";
  const currentHasByes = currentRound.ties.some((t) => t.is_bye);

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 min-h-0 overflow-y-auto p-3">
        {data.is_complete && (
          <div className="rounded-lg bg-gold/10 border border-gold/30 text-gold text-sm px-3 py-2 text-center font-semibold mb-3">
            🏆 Champion : {data.champion}
          </div>
        )}

        <h2 className="text-xs font-semibold text-gray-400 mb-2">Tour {currentRound.number}</h2>
        {currentHasByes && (
          <p className="text-[11px] text-gray-500 mb-2">
            Le nombre de qualifiés n'est pas une puissance de 2 : les mieux classés sont exemptés (qualifiés d'office)
            uniquement à ce tour, pour ramener le tableau à une puissance de 2. Aucun exempt aux tours suivants.
          </p>
        )}
        <div className="flex flex-col gap-1.5">
          {currentRound.ties.map((t) => (
            <TieCard key={`${t.home}-${t.away ?? "bye"}`} tie={t} />
          ))}
        </div>

        {/* Historique des tours déjà joués -- pour vérifier que les exempts
            du tour 1 ne se reproduisent pas aux tours suivants. */}
        {previousRounds.length > 0 && (
          <div className="mt-4 pt-3 border-t border-white/5">
            <h2 className="text-xs font-semibold text-gray-500 mb-2">Tours précédents</h2>
            <div className="flex flex-col gap-3">
              {previousRounds.map((r) => (
                <div key={r.number}>
                  <h3 className="text-[11px] text-gray-600 mb-1">Tour {r.number}</h3>
                  <div className="flex flex-col gap-1">
                    {r.ties.map((t) => (
                      <div
                        key={`${t.home}-${t.away ?? "bye"}`}
                        className="flex items-center justify-between bg-surface/50 rounded-lg px-3 py-1.5 text-xs"
                      >
                        <span className={`flex-1 min-w-0 truncate ${t.winner === t.home ? "text-gold" : "text-gray-500"}`}>
                          {t.home}
                        </span>
                        <span className="font-semibold tabular-nums px-3 shrink-0 text-gray-400">
                          {t.is_bye ? "exempt" : `${t.home_goals} - ${t.away_goals}`}
                        </span>
                        <span
                          className={`flex-1 min-w-0 truncate text-right ${t.winner === t.away ? "text-gold" : "text-gray-500"}`}
                        >
                          {t.away ?? ""}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
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

const LEG_LABELS = ["Aller", "Retour", "Manche 3"];

function TieCard({ tie: t }) {
  return (
    <div className="bg-surface rounded-lg px-3 py-2">
      <div className="flex items-center justify-between min-h-[28px] text-sm">
        <span className={`flex-1 min-w-0 truncate ${t.winner === t.home ? "font-semibold text-gold" : ""}`}>
          {t.home}
        </span>
        <span className="font-bold tabular-nums px-3 shrink-0">
          {t.is_bye ? "exempt" : t.home_goals != null ? `${t.home_goals} - ${t.away_goals}` : "– –"}
        </span>
        <span className={`flex-1 min-w-0 truncate text-right ${t.winner === t.away ? "font-semibold text-gold" : ""}`}>
          {t.away ?? ""}
        </span>
      </div>

      {/* Résultat de chaque manche (aller/retour) -- pas seulement l'agrégat,
          pour les confrontations sur plusieurs matchs. */}
      {t.legs.length > 0 && (
        <div className="flex flex-col gap-0.5 mt-1 pt-1 border-t border-white/5">
          {t.legs.map((leg, i) => (
            <div key={i} className="flex items-center justify-between text-[11px] text-gray-500">
              <span className="w-12 shrink-0">{LEG_LABELS[i] ?? `Manche ${i + 1}`}</span>
              <span className="flex-1 min-w-0 truncate text-right">{leg.home}</span>
              <span className="tabular-nums px-2 shrink-0">
                {leg.home_goals} - {leg.away_goals}
              </span>
              <span className="flex-1 min-w-0 truncate">{leg.away}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
