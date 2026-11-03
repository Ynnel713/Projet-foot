import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate, useOutletContext } from "react-router-dom";
import { LoaderCircle } from "lucide-react";
import { getBracket, simulateBracketRound, simulateBracketLeg, advanceBracketRound } from "../api/client";
import TeamLink from "../components/common/TeamLink";
import MatchRow from "../components/matches/MatchRow";
import ActionBar from "../components/common/ActionBar";
import AnimationDialog from "../components/pitch/AnimationDialog";

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
  const { refresh } = useOutletContext();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [launching, setLaunching] = useState(false); // « Lancement du live… » : simulation du tour avant le premier live
  const [error, setError] = useState(null);
  // Fenêtre « Voir l'animation », sans jamais révéler le score avant (US-15/16, docs/PRD_PRODUIT.md) -- matchParams ou null.
  const [animationMatch, setAnimationMatch] = useState(null);

  const load = useCallback(() => {
    getBracket(id)
      .then(setData)
      .catch(() => setError("Phase à élimination pas encore commencée."));
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  // `action` : "leg" (une manche de tout le tour), "round" (toutes les manches restantes) ou "advance" (tour suivant).
  async function handleAction(action) {
    setLoading(true);
    try {
      const call = { leg: simulateBracketLeg, round: simulateBracketRound, advance: advanceBracketRound }[action];
      setData(await call(id));
      refresh();
    } finally {
      setLoading(false);
    }
  }

  // Live d'une manche d'une confrontation (toutes compétitions à élimination directe) -- ouvre directement l'ANIMATION. Manche déjà
  // jouée : animation immédiate, sans jamais afficher le score au préalable. Prochaine manche à jouer : on simule cette manche du tour,
  // puis son animation s'ouvre automatiquement. Une manche plus lointaine (retour avant l'aller) n'est pas proposée (voir TieCard).
  async function openLive(round, tie, legIndex) {
    let source = data;
    if (tie.legs.length <= legIndex) {
      setLaunching(true);
      try {
        source = await simulateBracketLeg(id);
        setData(source);
        refresh();
      } catch {
        setLaunching(false);
        return;
      }
      setLaunching(false);
    }
    const played = source.rounds.find((r) => r.number === round.number)?.ties.find((t) => t.home === tie.home && t.away === tie.away);
    const leg = played?.legs[legIndex];
    if (!leg) return;
    setAnimationMatch({ home: leg.home, away: leg.away, round_number: round.number, leg: legIndex });
  }

  if (error) return <div className="p-6 text-sm text-gray-400">{error}</div>;
  if (!data) return <div className="p-6 text-sm text-gray-400">Chargement…</div>;

  const currentRound = data.rounds[data.rounds.length - 1];
  const previousRounds = data.rounds.slice(0, -1);
  const legsLeft = data.current_legs - data.current_legs_played;
  const legName = data.current_legs === 2 ? (data.current_legs_played === 0 ? "l'aller" : "le retour") : `la manche ${data.current_legs_played + 1}`;
  const currentHasByes = currentRound.ties.some((t) => t.is_bye);

  const tieCard = (round, t) => (
    <TieCard
      key={`${t.home}-${t.away ?? "bye"}`}
      tie={t}
      totalLegs={round === currentRound ? data.current_legs : 1}
      onOpenSheet={(leg, i) =>
        navigate(`/competition/${id}/pitch?${new URLSearchParams({ home: leg.home, away: leg.away, round_number: round.number, leg: i })}`)
      }
      onLive={(legIndex) => openLive(round, t, legIndex)}
    />
  );

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 min-h-0 overflow-y-auto p-3">
        <div className="mx-auto w-full max-w-4xl">
          {data.is_complete && (
            <div className="rounded-lg bg-gold/10 border border-gold/30 text-gold text-sm px-3 py-2 text-center font-semibold mb-3">
              🏆 Champion : {data.champion}
            </div>
          )}

          <h2 className="font-display text-2xl font-semibold text-white mb-2">{roundTitle(currentRound)}</h2>
          {currentHasByes && (
            <p className="text-caption text-gray-500 mb-2">
              Le nombre de qualifiés n'est pas une puissance de 2 : les mieux classés sont exemptés (qualifiés d'office)
              uniquement à ce tour, pour ramener le tableau à une puissance de 2. Aucun exempt aux tours suivants.
            </p>
          )}
          <div className="flex flex-col gap-2">{currentRound.ties.map((t) => tieCard(currentRound, t))}</div>

          {/* Tours précédents, sous le tour en cours (l'arbre complet arrive au lot 6). */}
          {previousRounds.length > 0 && (
            <div className="mt-6 pt-4 border-t border-line">
              {previousRounds.map((r) => (
                <div key={r.number} className="mb-4">
                  <h3 className="text-sm font-semibold text-gray-400 mb-1.5">{roundTitle(r)}</h3>
                  <div className="flex flex-col gap-2">{r.ties.map((t) => tieCard(r, t))}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {animationMatch && <AnimationDialog competitionId={id} matchParams={animationMatch} onClose={() => setAnimationMatch(null)} />}

      {!data.is_complete && (
        <ActionBar
          primary={
            currentRound.played
              ? { label: "Tour suivant →", onClick: () => handleAction("advance"), loading }
              : { label: data.current_legs === 1 ? "Simuler ce tour" : `Simuler ${legName}`, onClick: () => handleAction("leg"), loading }
          }
          secondary={!currentRound.played && legsLeft > 1 ? { label: "Simuler tout le tour", onClick: () => handleAction("round"), disabled: loading } : undefined}
        />
      )}

      {launching && (
        <div role="status" className="fixed inset-0 z-50 flex flex-col items-center justify-center gap-3 bg-bg">
          <LoaderCircle size={36} className="animate-spin text-live" />
          <span className="text-sm font-semibold text-gray-100">Lancement du live...</span>
        </div>
      )}
    </div>
  );
}

const LEG_LABELS = ["Aller", "Retour", "Manche 3"];

// Confrontation : manche unique = une ligne de match ; aller-retour = score cumulé puis chaque manche. Le vainqueur est en blanc
// et en gras. Le score de chaque manche ouvre sa feuille de match (`leg.home` / `leg.away` : l'ordre de la manche, inversé au retour).
function TieCard({ tie: t, totalLegs, onOpenSheet, onLive }) {
  const tone = (club) => (t.winner ? (t.winner === club ? "text-white font-semibold" : "text-gray-400") : "text-gray-100");

  if (t.is_bye) {
    return (
      <div className="rounded-xl bg-surface border border-line px-3 py-2 flex items-center justify-between gap-3">
        <TeamLink name={t.home} className="text-data text-gray-100" />
        <span className="text-caption text-gray-500">Exempt (qualifié d'office)</span>
      </div>
    );
  }

  const nbLegs = Math.max(t.legs.length, totalLegs);

  if (nbLegs <= 1) {
    const leg = t.legs[0];
    return (
      <div className="rounded-xl bg-surface border border-line overflow-hidden">
        <MatchRow
          match={leg ?? { home: t.home, away: t.away, played: false }}
          winner={t.winner}
          onOpenSheet={leg ? () => onOpenSheet(leg, 0) : undefined}
          onLive={() => onLive(0)}
        />
        {t.decided_by_penalties && <PenaltyLine tie={t} />}
      </div>
    );
  }

  return (
    <div className="rounded-xl bg-surface border border-line overflow-hidden">
      <div className="px-3 pt-3 pb-2 grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-2">
        <TeamLink name={t.home} align="end" className={`justify-self-end text-data ${tone(t.home)}`} />
        <span className="px-2 font-display font-bold text-2xl tabular-nums text-white">
          {t.home_goals != null ? `${t.home_goals} - ${t.away_goals}` : "– –"}
        </span>
        <TeamLink name={t.away} className={`justify-self-start text-data ${tone(t.away)}`} />
      </div>
      {t.decided_by_penalties && <PenaltyLine tie={t} />}
      {Array.from({ length: nbLegs }, (_, i) => {
        const leg = t.legs[i];
        const host = i % 2 === 0 ? [t.home, t.away] : [t.away, t.home];
        return (
          <div key={i} className="border-t border-line">
            <p className="px-3 pt-1.5 text-caption text-gray-500">{LEG_LABELS[i] ?? `Manche ${i + 1}`}</p>
            <MatchRow
              match={leg ?? { home: host[0], away: host[1], played: false }}
              onOpenSheet={leg ? () => onOpenSheet(leg, i) : undefined}
              onLive={i <= t.legs.length ? () => onLive(i) : undefined} // une manche n'est proposée qu'après la précédente
            />
          </div>
        );
      })}
    </div>
  );
}

function PenaltyLine({ tie: t }) {
  if (!t.penalty_score) return <p className="px-3 pb-2 text-caption text-gray-300 text-center">Tirs au but</p>;
  const [homePens, awayPens] = t.penalty_score;
  return (
    <p className="px-3 pb-2 text-caption text-gray-300 text-center font-semibold">
      Tirs au but : {homePens}-{awayPens}
    </p>
  );
}
