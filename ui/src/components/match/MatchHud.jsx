import { ArrowLeft, Pause, Play } from "lucide-react";
import { SPEED_OPTIONS } from "../../hooks/useMatchPlayback";
import ScoreBlock from "./ScoreBlock";

// HUD supérieur de l'écran Match (ticket v2-ecran-match/08, constantes et décisions du propriétaire du 19/11/2026) :
// identité du match (`ScoreBlock`), puis minute (Barlow Condensed 600, 24 px ; 18 px sous 960 px de large ou 500 px de
// haut), période et badge d'état. Lignes techniques retirées (situation tactique, minute de calcul) ; la ligne de
// hors-jeu reste jusqu'à la frise (EM-12). Commandes de vitesse inchangées (EM-09).
const BADGE_TONE = {
  live: "text-live border-live/40",
  gold: "text-gold border-gold/40",
  neutral: "text-gray-200 border-gray-500",
  muted: "text-gray-400 border-line",
};

export default function MatchHud({ trace, score, time, badge, offside, onBack, playback, finished }) {
  const { playing, setPlaying, speed, setSpeed, replaying, skipReplay } = playback;
  return (
    <div data-zone="hud" className="flex items-center justify-between gap-2 px-2.5 py-1 bg-surface border-b border-line">
      <button onClick={onBack} className="flex items-center gap-1 min-h-11 text-data text-gray-400 shrink-0">
        <ArrowLeft size={14} /> Retour
      </button>
      <div className="min-w-0 flex-1 flex flex-col items-stretch">
        <ScoreBlock home={trace.home} away={trace.away} score={score} />
        <div className="flex items-center justify-center gap-2 h-6 min-w-0 whitespace-nowrap">
          <span
            data-zone="minute"
            className="font-display font-semibold tabular-nums text-white text-[24px] leading-none max-[959.98px]:text-[18px] [@media(max-height:499.98px)]:text-[18px]"
          >
            {time.label}
          </span>
          {time.announced != null && <span className="text-data text-gray-400 tabular-nums">(+{time.announced})</span>}
          <span className="text-caption text-gray-400">{time.second ? "2e" : "1re"} période</span>
          <span
            data-zone="etat"
            className={`text-caption font-semibold tracking-wider rounded border px-1.5 leading-4 ${BADGE_TONE[badge.tone]}`}
          >
            {badge.label}
          </span>
          {offside && (
            <span className="min-w-0 truncate text-caption font-semibold text-gold">
              ⚑ Hors-jeu — {offside.player} ({offside.team === "home" ? trace.home : trace.away})
            </span>
          )}
        </div>
      </div>
      <div className="flex items-center gap-1.5 shrink-0">
        {replaying && (
          <button
            onClick={skipReplay}
            className="text-data px-2 py-1 rounded bg-red-600 text-white font-semibold"
            title="Passer le ralenti"
          >
            RALENTI ⏭
          </button>
        )}
        {SPEED_OPTIONS.map((s) => (
          <button
            key={s}
            onClick={() => setSpeed(s)}
            className={`text-data px-2 py-1 rounded ${speed === s ? "bg-accent text-white" : "bg-surface text-gray-400"}`}
          >
            x{s}
          </button>
        ))}
        <button
          onClick={() => setPlaying((p) => !p)}
          disabled={finished}
          className="h-9 w-9 rounded-full bg-accent text-white flex items-center justify-center disabled:opacity-40"
        >
          {playing ? <Pause size={16} /> : <Play size={16} />}
        </button>
      </div>
    </div>
  );
}
