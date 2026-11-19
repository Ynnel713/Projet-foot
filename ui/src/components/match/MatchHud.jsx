import { useLayoutEffect, useRef, useState } from "react";
import { ArrowLeft } from "lucide-react";
import ScoreBlock from "./ScoreBlock";
import SpeedControls from "./SpeedControls";

// HUD supérieur de l'écran Match (ticket v2-ecran-match/08, constantes et décisions du propriétaire du 19/11/2026) :
// identité du match (`ScoreBlock`), puis minute (Barlow Condensed 600, 24 px ; 18 px sous 960 px de large ou 500 px de
// haut), période et badge d'état. Lignes techniques retirées (situation tactique, minute de calcul) ; la ligne de
// hors-jeu reste jusqu'à la frise (EM-12). Commandes de lecture : `SpeedControls` (EM-09).
const BADGE_TONE = {
  live: "text-live border-live/40",
  gold: "text-gold border-gold/40",
  neutral: "text-gray-200 border-gray-500",
  muted: "text-gray-400 border-line",
};

// Score centré sur l'écran, donc sur la ligne médiane du terrain (ticket v2-ecran-match/08b) : trois colonnes, les deux
// latérales de la largeur du plus large de leurs contenus (retour à gauche, commandes à droite), mesurée par un
// `ResizeObserver` (premier relevé avant l'affichage, puis à chaque changement de taille, ralenti compris).
function useSideWidth() {
  const left = useRef(null);
  const right = useRef(null);
  const [width, setWidth] = useState(null);
  useLayoutEffect(() => {
    const observer = new ResizeObserver(() =>
      setWidth(Math.ceil(Math.max(left.current.offsetWidth, right.current.offsetWidth))),
    );
    observer.observe(left.current);
    observer.observe(right.current);
    return () => observer.disconnect();
  }, []);
  return [left, right, width];
}

export default function MatchHud({ trace, score, scorers, time, badge, offside, onBack, playback, finished }) {
  const [leftRef, rightRef, sideWidth] = useSideWidth();
  const columns = sideWidth == null ? "auto minmax(0,1fr) auto" : `${sideWidth}px minmax(0,1fr) ${sideWidth}px`;
  return (
    <div
      data-zone="hud"
      className="grid items-center gap-2 px-2.5 py-1 bg-surface border-b border-line"
      style={{ gridTemplateColumns: columns }}
    >
      <div className="flex justify-start">
        <button ref={leftRef} onClick={onBack} className="flex items-center gap-1 min-h-11 text-data text-gray-400 shrink-0">
          <ArrowLeft size={14} /> Retour
        </button>
      </div>
      <div className="min-w-0 flex flex-col items-stretch">
        <ScoreBlock home={trace.home} away={trace.away} score={score} scorers={scorers} />
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
      <div className="flex justify-end">
        <div ref={rightRef} className="shrink-0">
          <SpeedControls
            playing={playback.playing}
            setPlaying={playback.setPlaying}
            speed={playback.speed}
            setSpeed={playback.setSpeed}
            replaying={playback.replaying}
            skipReplay={playback.skipReplay}
            finished={finished}
          />
        </div>
      </div>
    </div>
  );
}
