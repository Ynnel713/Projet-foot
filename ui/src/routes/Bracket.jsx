import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, LoaderCircle } from "lucide-react";
import { getBracket, simulateBracketRound, advanceBracketRound } from "../api/client";
import { shortScorerName } from "../utils/playerName";
import TeamLink from "../components/common/TeamLink";
import LiveButton from "../components/common/LiveButton";

// "Tour N" -> terminologie foot standard, calculée depuis le nombre de
// confrontations du tour (1 confrontation = finale, 2 = 1/2, 4 = 1/4, 8 =
// 1/8...) plutôt que depuis `round.number` -- une finale qui s'appelait
// "Tour 4" n'a pas de sens pour l'utilisateur (retour terrain du
// 29/09/2026).
function roundLabel(nbTies) {
  if (nbTies === 1) return "Finale";
  if (nbTies === 2) return "1/2 finale";
  return `1/${nbTies}e de finale`;
}

// Libellé d'un tour : celui imposé par le moteur (« Barrages » de la Ligue des Champions) sinon déduit du nombre de confrontations.
function roundTitle(round) {
  return round.label ?? roundLabel(round.ties.length);
}

export default function Bracket() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [launching, setLaunching] = useState(false); // « Lancement du live… » : simulation du tour avant le premier live
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

  // Live d'une manche d'une confrontation (toutes compétitions à élimination directe). Manche déjà jouée : on rouvre son live. Pas encore
  // jouée : on simule le tour (le moteur joue un tour d'un bloc), puis on ouvre le live de CETTE manche.
  async function openLive(round, tie, legIndex) {
    let source = data;
    if (tie.legs.length <= legIndex) {
      setLaunching(true);
      try {
        source = await simulateBracketRound(id);
        setData(source);
      } catch {
        setLaunching(false);
        return;
      }
      setLaunching(false);
    }
    const played = source.rounds.find((r) => r.number === round.number)?.ties.find((t) => t.home === tie.home && t.away === tie.away);
    const leg = played?.legs[legIndex];
    if (!leg) return;
    navigate(
      `/competition/${id}/pitch?${new URLSearchParams({
        home: leg.home,
        away: leg.away,
        round_number: round.number,
        leg: legIndex,
        tab: "live",
        replay: "1",
      })}`,
    );
  }

  if (error) return <div className="p-6 text-sm text-gray-400">{error}</div>;
  if (!data) return <div className="p-6 text-sm text-gray-400">Chargement…</div>;

  const currentRound = data.rounds[data.rounds.length - 1];
  const previousRounds = data.rounds.slice(0, -1);
  const buttonLabel = currentRound.played ? "Tour suivant →" : "Simuler ce tour";
  const currentHasByes = currentRound.ties.some((t) => t.is_bye);

  return (
    <div className="flex flex-col h-full">
      <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-xs text-gray-400 self-start px-3 pt-3 shrink-0">
        <ArrowLeft size={14} /> Retour
      </button>
      <div className="flex-1 min-h-0 overflow-y-auto p-3">
        {data.is_complete && (
          <div className="rounded-lg bg-gold/10 border border-gold/30 text-gold text-sm px-3 py-2 text-center font-semibold mb-3">
            🏆 Champion : {data.champion}
          </div>
        )}

        <h2 className="text-base font-bold text-white mb-2">{roundTitle(currentRound)}</h2>
        {currentHasByes && (
          <p className="text-[11px] text-gray-500 mb-2">
            Le nombre de qualifiés n'est pas une puissance de 2 : les mieux classés sont exemptés (qualifiés d'office)
            uniquement à ce tour, pour ramener le tableau à une puissance de 2. Aucun exempt aux tours suivants.
          </p>
        )}
        <div className="flex flex-col gap-2">
          {currentRound.ties.map((t) => (
            <TieCard
              key={`${t.home}-${t.away ?? "bye"}`}
              tie={t}
              id={id}
              navigate={navigate}
              roundNumber={currentRound.number}
              onLive={(legIndex) => openLive(currentRound, t, legIndex)}
            />
          ))}
        </div>

        {/* Tours précédents reléqués au second plan (police réduite, faible
            opacité) -- juste pour vérifier l'historique, pas pour rivaliser
            visuellement avec le tour en cours (retour terrain du
            29/09/2026). */}
        {previousRounds.length > 0 && (
          <div className="mt-5 pt-3 border-t border-white/5 opacity-60">
            {previousRounds.map((r) => (
              <div key={r.number} className="mb-3">
                <h3 className="text-[11px] font-semibold text-gray-500 mb-1">{roundTitle(r)}</h3>
                <div className="flex flex-col gap-1">
                  {r.ties.map((t) => (
                    <TieCard
                      key={`${t.home}-${t.away ?? "bye"}`}
                      tie={t}
                      id={id}
                      navigate={navigate}
                      roundNumber={r.number}
                      onLive={(legIndex) => openLive(r, t, legIndex)}
                      compact
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {launching && (
        <div role="status" className="fixed inset-0 z-50 flex flex-col items-center justify-center gap-3 bg-black/70 backdrop-blur-sm">
          <LoaderCircle size={36} className="animate-spin text-live" />
          <span className="text-sm font-semibold text-slate-100">Lancement du live...</span>
        </div>
      )}

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

function _scorersText(scorers, club) {
  if (!scorers) return "";
  return scorers
    .filter((s) => s.club === club)
    .map((s) => `${shortScorerName(s.player)} ${s.minute}'`)
    .join(", ");
}

function TieCard({ tie: t, id, navigate, roundNumber, onLive, compact = false }) {
  const singleLeg = t.legs.length <= 1;
  const scoreSize = compact ? "text-base" : "text-2xl";
  const teamSize = compact ? "text-[12px]" : "text-base";

  return (
    <div className={compact ? "bg-surface/50 rounded-lg px-3 py-2" : "bg-surface rounded-xl px-4 py-3"}>
      {/* Confrontation à manche unique (le cas le plus courant -- Coupe du
          Monde, la plupart des Compétitions Perso à élimination directe) :
          UNE seule ligne (score au centre, équipes de part et d'autre,
          buteurs aux extrémités), le vainqueur en surbrillance -- pas de
          doublon d'un résumé + d'une manche identique en dessous (retour
          terrain du 29/09/2026 : "on voit 2 fois les noms des équipes"). */}
      {singleLeg ? (
        <SingleLegRow
          tie={t}
          id={id}
          navigate={navigate}
          roundNumber={roundNumber}
          onLive={onLive}
          scoreSize={scoreSize}
          teamSize={teamSize}
          compact={compact}
        />
      ) : (
        <>
          <div className={`flex items-center min-h-[32px] ${teamSize}`}>
            <TeamLink
              name={t.home}
              className={`flex-1 min-w-0 ${t.winner === t.home ? "font-bold text-gold" : "text-gray-300"}`}
            />
            <span className={`font-extrabold tabular-nums px-3 shrink-0 ${scoreSize}`}>
              {t.is_bye ? "exempt" : t.home_goals != null ? `${t.home_goals} - ${t.away_goals}` : "– –"}
            </span>
            {t.away ? (
              <TeamLink
                name={t.away}
                align="end"
                className={`flex-1 min-w-0 ${t.winner === t.away ? "font-bold text-gold" : "text-gray-300"}`}
              />
            ) : (
              <span className="flex-1 min-w-0" />
            )}
          </div>
          {t.legs.length === 0 && !t.is_bye && (
            <div className="flex justify-center mt-1">
              <LiveButton played={false} onLive={() => onLive(0)} compact />
            </div>
          )}
          {t.decided_by_penalties && <PenaltyLine tie={t} />}

          {/* Résultat de chaque manche (aller/retour) -- agrégat ci-dessus
              différent d'une manche seule, donc pas un doublon ici. */}
          <div className="flex flex-col gap-1 mt-1.5 pt-1.5 border-t border-white/5">
            {t.legs.map((leg, i) => (
              // div + role="button" (pas <button>) : TeamLink à l'intérieur est
              // lui-même un bouton, un bouton dans un bouton est invalide.
              <div
                key={i}
                role="button"
                tabIndex={0}
                onClick={() =>
                  navigate(
                    `/competition/${id}/pitch?${new URLSearchParams({
                      home: leg.home,
                      away: leg.away,
                      round_number: roundNumber,
                      leg: i,
                    })}`
                  )
                }
                className="text-left cursor-pointer rounded px-1 py-0.5 hover:bg-white/5"
              >
                <div className="grid grid-cols-[1fr_1fr_2.5rem_1fr_1fr_auto] items-center gap-1">
                  <span className="text-[9px] text-gray-500 truncate justify-self-start">{_scorersText(leg.scorers, leg.home)}</span>
                  <TeamLink name={leg.home} stopPropagation align="end" className="justify-self-end text-[12px] text-gray-400" />
                  <span className="tabular-nums text-center text-[13px] font-semibold text-gray-300">
                    {leg.home_goals} - {leg.away_goals}
                  </span>
                  <TeamLink name={leg.away} stopPropagation className="justify-self-start text-[12px] text-gray-400" />
                  <span className="text-[9px] text-gray-500 truncate justify-self-end text-right">{_scorersText(leg.scorers, leg.away)}</span>
                  <LiveButton played onLive={() => onLive(i)} compact />
                </div>
                <div className="text-center text-[9px] text-gray-600 mt-0.5">{LEG_LABELS[i] ?? `Manche ${i + 1}`}</div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function PenaltyLine({ tie: t }) {
  if (!t.penalty_score) return <p className="text-[10px] text-gold text-center -mt-0.5">Tirs au but</p>;
  const [homePens, awayPens] = t.penalty_score;
  return (
    <p className="text-[11px] text-gold text-center font-semibold -mt-0.5">
      TAB : {homePens}-{awayPens}
    </p>
  );
}

function SingleLegRow({ tie: t, id, navigate, roundNumber, onLive, scoreSize, teamSize, compact }) {
  const leg = t.legs[0];
  const clickable = Boolean(leg) && !t.is_bye;

  return (
    <div
      role={clickable ? "button" : undefined}
      tabIndex={clickable ? 0 : undefined}
      onClick={
        clickable
          ? () =>
              navigate(
                `/competition/${id}/pitch?${new URLSearchParams({ home: leg.home, away: leg.away, round_number: roundNumber, leg: 0 })}`
              )
          : undefined
      }
      className={clickable ? "cursor-pointer rounded-lg -mx-1 px-1 py-0.5 hover:bg-white/5" : ""}
    >
      <div className={`grid items-center gap-2 ${compact ? "grid-cols-[1fr_1fr_2.75rem_1fr_1fr_auto]" : "grid-cols-[1fr_1fr_4rem_1fr_1fr_auto]"}`}>
        <span className={`text-gray-500 truncate justify-self-start ${compact ? "text-[9px]" : "text-[11px]"}`}>
          {leg ? _scorersText(leg.scorers, t.home) : ""}
        </span>
        <TeamLink
          name={t.home}
          className={`justify-self-end ${teamSize} ${t.winner === t.home ? "font-bold text-gold" : "text-gray-300"}`}
        />
        <span className={`font-extrabold tabular-nums text-center ${scoreSize} text-white`}>
          {t.is_bye ? "exempt" : t.home_goals != null ? `${t.home_goals} - ${t.away_goals}` : "– –"}
        </span>
        {t.away ? (
          <TeamLink
            name={t.away}
            align="end"
            className={`justify-self-start ${teamSize} ${t.winner === t.away ? "font-bold text-gold" : "text-gray-300"}`}
          />
        ) : (
          <span />
        )}
        <span className={`text-gray-500 truncate justify-self-end text-right ${compact ? "text-[9px]" : "text-[11px]"}`}>
          {leg ? _scorersText(leg.scorers, t.away) : ""}
        </span>
        {!t.is_bye ? <LiveButton played={Boolean(leg)} onLive={() => onLive(0)} compact={compact} /> : <span />}
      </div>
      {t.decided_by_penalties && <PenaltyLine tie={t} />}
    </div>
  );
}
