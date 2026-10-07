import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { ArrowLeftRight, ArrowUp, Crosshair, Flag, Goal, Hand, Pause, Play, RectangleVertical, RotateCcw, Shield, SkipForward } from "lucide-react";
import { MATCH_END, SPEEDS } from "../../utils/liveReplay";

// Type d'événement -> icône, couleur du titre, couleur du filet de la carte. BUT vert, JAUNE, ROUGE, REMPLACEMENT bleu, TIR orange,
// ARRÊT violet ; DÉFENSE et coup d'envoi / fin en neutre. Les clés sont celles de `kind` côté API (api.live_commentary / api.nlg_live).
const KINDS = {
  goal: { Icon: Goal, text: "text-ev-goal", border: "border-l-ev-goal" },
  yellow: { Icon: RectangleVertical, text: "text-ev-yellow", border: "border-l-ev-yellow", fill: true },
  second_yellow: { Icon: RectangleVertical, text: "text-ev-red", border: "border-l-ev-red", fill: true },
  red: { Icon: RectangleVertical, text: "text-ev-red", border: "border-l-ev-red", fill: true },
  sub: { Icon: ArrowLeftRight, text: "text-ev-sub", border: "border-l-ev-sub" },
  shot_off: { Icon: Crosshair, text: "text-orange-500", border: "border-l-orange-500" },
  penalty_missed: { Icon: Crosshair, text: "text-orange-500", border: "border-l-orange-500" },
  save: { Icon: Hand, text: "text-violet-400", border: "border-l-violet-400" },
  defense: { Icon: Shield, text: "text-ev-neutral", border: "border-l-ev-neutral" },
  start: { Icon: Flag, text: "text-ev-neutral", border: "border-l-ev-neutral" },
  end: { Icon: Flag, text: "text-ev-neutral", border: "border-l-ev-neutral" },
};

// Marge (px) sous laquelle on considère le fil « au direct » (dernier événement, en haut, visible).
const AT_LIVE_MARGIN = 28;

// Colonne « COMMENTAIRE EN DIRECT » (jamais un calque : le terrain reste entièrement visible à côté). Chronologique INVERSE comme sur la
// maquette : le plus récent en haut. Défilement automatique vers le dernier événement tant qu'on n'est pas redescendu dans le fil ;
// une fois redescendu, « Revenir au direct » ramène en haut. Défilement indépendant de la page. Les événements viennent de l'API
// (`live` du pitch view : texte du NLG) -- les mêmes buts, cartons et remplacements que la liste des remplaçants.
export default function LivePanel({ events, finished, playback, alerts, footer }) {
  const scrollRef = useRef(null);
  const [atLive, setAtLive] = useState(true);
  const ordered = [...events].reverse(); // récent en haut

  function scrollToLatest(behavior = "smooth") {
    scrollRef.current?.scrollTo({ top: 0, behavior });
  }

  useEffect(() => {
    if (atLive) scrollToLatest("auto");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [events.length]);

  return (
    <aside
      aria-label="Commentaire en direct"
      className="absolute inset-0 flex flex-col rounded-2xl bg-live-card border border-live-border overflow-hidden"
    >
      <header className="shrink-0 flex items-center gap-2.5 px-4 py-3 border-b border-live-border">
        <div className="min-w-0 flex-1 leading-tight">
          <h2 className="text-[15px] font-extrabold uppercase tracking-wide text-slate-100">Commentaire en direct</h2>
        </div>
        <span className="flex items-center gap-1.5 text-[11px] font-extrabold uppercase tracking-wider shrink-0">
          {finished ? (
            <span className="text-slate-400">Terminé</span>
          ) : (
            <>
              <span className="relative flex h-2.5 w-2.5" aria-hidden="true">
                <span className="absolute inline-flex h-full w-full rounded-full bg-red-500 opacity-60 animate-ping" />
                <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-red-500" />
              </span>
              <span className="text-red-400">En direct</span>
            </>
          )}
        </span>
      </header>

      {playback && <PlaybackBar {...playback} />}
      {alerts}

      <div className="relative flex-1 min-h-0">
        <div
          ref={scrollRef}
          onScroll={(e) => setAtLive(e.currentTarget.scrollTop < AT_LIVE_MARGIN)}
          className="h-full overflow-y-auto overscroll-contain px-3 py-3"
        >
          {ordered.length === 0 ? (
            <p className="text-sm text-slate-400 italic">Aucun événement pour ce match.</p>
          ) : (
            <ol className="relative flex flex-col gap-3">
              {/* ligne verticale cyan derrière les pastilles de minute (centre d'une pastille de 40 px : 20 px) */}
              <span className="absolute left-5 top-5 bottom-5 w-0.5 bg-live/30" aria-hidden="true" />
              {ordered.map((e) => {
                const kind = KINDS[e.kind] ?? KINDS.defense;
                const { Icon } = kind;
                return (
                  <motion.li
                    key={`${e.minute}-${e.kind}-${e.parts.map((p) => p.text).join("").slice(0, 24)}`}
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.25 }}
                    className="relative grid grid-cols-[40px_1fr] gap-2.5 items-start"
                  >
                    <span
                      className="relative z-10 h-10 w-10 rounded-full bg-live text-[#0f1419] text-[18px] font-extrabold tabular-nums
                                 flex items-center justify-center shadow-md shadow-black/40"
                    >
                      {e.minute}'
                    </span>
                    <div className={`min-w-0 rounded-xl bg-white/[0.04] border border-white/5 border-l-4 ${kind.border} px-3 py-2`}>
                      <div className={`flex items-center gap-1.5 text-[13px] font-extrabold uppercase tracking-wide ${kind.text}`}>
                        <Icon size={15} fill={kind.fill ? "currentColor" : "none"} aria-hidden="true" />
                        {e.title}
                      </div>
                      <p className="mt-0.5 text-[14px] leading-snug text-[#e2e8f0] break-words">
                        {e.parts.map((p, k) =>
                          p.player ? (
                            <strong key={k} className="font-bold text-live">
                              {p.text}
                            </strong>
                          ) : (
                            <span key={k}>{p.text}</span>
                          ),
                        )}
                      </p>
                    </div>
                  </motion.li>
                );
              })}
            </ol>
          )}
        </div>

        {!atLive && (
          <button
            type="button"
            onClick={() => {
              scrollToLatest();
              setAtLive(true);
            }}
            className="absolute top-3 left-1/2 -translate-x-1/2 h-8 px-3.5 rounded-full bg-live text-[#0f1419] text-xs font-bold
                       shadow-lg shadow-black/40 flex items-center gap-1.5 hover:brightness-110 active:scale-95 transition-transform"
          >
            <ArrowUp size={14} /> Revenir au direct
          </button>
        )}
      </div>
      {footer && <div className="shrink-0 border-t border-live-border px-3 py-1.5 max-h-20 overflow-y-auto">{footer}</div>}
    </aside>
  );
}

// Barre de lecture du live rejoué : pause/lecture (ou « rejouer » une fois fini), vitesse x1/x2/x4, passer à la fin, minute courante.
function PlaybackBar({ clock, playing, speed, onTogglePlay, onSpeed, onSkip, onRestart }) {
  const finished = clock >= MATCH_END;
  const btn = "h-7 min-w-7 px-1.5 rounded-lg flex items-center justify-center gap-1 text-[11px] font-bold text-slate-200 bg-white/5 hover:bg-white/10 transition-colors";
  return (
    <div className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 border-b border-live-border">
      {finished ? (
        <button type="button" onClick={onRestart} aria-label="Rejouer le live depuis le début" className={btn}>
          <RotateCcw size={13} />
        </button>
      ) : (
        <button type="button" onClick={onTogglePlay} aria-label={playing ? "Mettre en pause" : "Reprendre le live"} className={btn}>
          {playing ? <Pause size={13} /> : <Play size={13} />}
        </button>
      )}
      <button
        type="button"
        onClick={() => onSpeed(SPEEDS[(SPEEDS.indexOf(speed) + 1) % SPEEDS.length])}
        aria-label={`Vitesse x${speed}, changer`}
        className={btn}
      >
        x{speed}
      </button>
      {!finished && (
        <button type="button" onClick={onSkip} aria-label="Passer à la fin du match" className={btn}>
          <SkipForward size={13} />
        </button>
      )}
      <span className="ml-auto text-[13px] font-bold tabular-nums text-live">{Math.floor(clock)}'</span>
    </div>
  );
}
