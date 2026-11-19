import { useEffect } from "react";
import { Pause, Play, SkipForward } from "lucide-react";
import { SPEED_OPTIONS } from "../../hooks/useMatchPlayback";
import { playbackKey, speedLabel } from "../../utils/playbackKeys";

// Commandes de lecture du HUD (ticket v2-ecran-match/09, constantes validées par le propriétaire le 19/11/2026).
// Groupe segmenté des vitesses : segments de 40 px de haut (36 px sous 960 px de large ou 500 px de haut), filet
// `line` dessiné sans prendre de place, vitesse active pleine en `accent`. Bouton lecture/pause rond de 44 px (40 px).
// Pendant le ralenti d'un but, le bouton rond devient « Passer le ralenti » (décision du propriétaire du 19/11/2026,
// réserve A2 de l'expert : cible de 44 px au lieu d'un badge de 20 px) et la barre d'espace aussi ; le ralenti est signalé
// par le badge d'état du HUD (EM-13), plus par une pastille ici (EM-13b, décision du propriétaire du 19/11/2026). La
// largeur des commandes ne change pas (score centré, EM-08b). Clavier : espace = lecture/pause (ou passer le ralenti), 1 à 5 = vitesses.
// Le comportement de la lecture est celui du hook, inchangé.
const SMALL_H = "max-[959.98px]:h-9 [@media(max-height:499.98px)]:h-9";

export default function SpeedControls({ playing, setPlaying, speed, setSpeed, replaying, skipReplay, finished }) {
  useEffect(() => {
    const onKeyDown = (event) => {
      // touche maintenue : interceptée (pas de défilement ni de clic répété) mais sans nouvelle commande ; les champs
      // d'un KeyboardEvent sont des accesseurs de son prototype, d'où la copie explicite
      const { key, code, target, ctrlKey, metaKey, altKey } = event;
      if (event.repeat && playbackKey({ key, code, target, ctrlKey, metaKey, altKey }, SPEED_OPTIONS)) {
        event.preventDefault();
        return;
      }
      const action = playbackKey(event, SPEED_OPTIONS);
      if (!action) return;
      event.preventDefault(); // pas de défilement de la page, ni de clic du bouton qui a le focus
      if (action.type === "speed") setSpeed(action.speed);
      else if (replaying) skipReplay();
      else if (!finished) setPlaying((p) => !p);
    };
    // la barre d'espace active un bouton au relâchement : on l'empêche aussi, sinon elle double la commande
    const onKeyUp = (event) => {
      if (playbackKey(event, SPEED_OPTIONS)?.type === "toggle") event.preventDefault();
    };
    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("keyup", onKeyUp);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("keyup", onKeyUp);
    };
  }, [finished, replaying, skipReplay, setPlaying, setSpeed]);

  return (
    <div className="flex flex-col items-end gap-1">
      <div className="flex items-center gap-2">
        <div
          role="radiogroup"
          aria-label="Vitesse de lecture"
          className="flex overflow-hidden rounded-lg bg-surface-2 ring-1 ring-inset ring-line"
        >
          {SPEED_OPTIONS.map((s) => {
            const active = speed === s;
            return (
              <button
                key={s}
                role="radio"
                aria-checked={active}
                aria-label={`Vitesse ${speedLabel(s)}`}
                onClick={() => setSpeed(s)}
                className={`h-10 ${SMALL_H} min-w-10 max-[959.98px]:min-w-9 [@media(max-height:499.98px)]:min-w-9 px-2 font-display font-semibold tabular-nums text-[16px] max-[959.98px]:text-[14px] [@media(max-height:499.98px)]:text-[14px] transition-colors duration-150 ease-out motion-reduce:transition-none ${
                  active ? "bg-accent text-white" : "text-gray-400 hover:text-gray-100"
                }`}
              >
                {speedLabel(s)}
              </button>
            );
          })}
        </div>
        <button
          onClick={replaying ? skipReplay : () => setPlaying((p) => !p)}
          disabled={finished && !replaying}
          aria-label={replaying ? "Passer le ralenti" : playing ? "Pause" : "Lecture"}
          title={replaying ? "Passer le ralenti" : undefined}
          className="size-11 max-[959.98px]:size-10 [@media(max-height:499.98px)]:size-10 shrink-0 rounded-full bg-accent text-white flex items-center justify-center disabled:opacity-40"
        >
          {replaying ? <SkipForward size={18} /> : playing ? <Pause size={18} /> : <Play size={18} />}
        </button>
      </div>
    </div>
  );
}
