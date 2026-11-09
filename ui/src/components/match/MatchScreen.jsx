import { useMemo } from "react";
import { ArrowLeft, Pause, Play } from "lucide-react";
import { SPEED_OPTIONS } from "../../hooks/useMatchPlayback";
import IntentionPanel from "./IntentionPanel";
import LineupPanel from "./LineupPanel";
import Momentum from "./Momentum";
import V2Pitch from "./V2Pitch";
import { clock, halfStart, interpolatedTick, rotated, situationAt } from "./trace";

// Écran de lecture de la V2 (ticket v2-ecran-match/01 : déplacé depuis routes/V2Match.jsx). Le score n'est révélé
// qu'au fil des buts horodatés dans la trace, jamais avant que la lecture ne les atteigne (US-29).
export default function MatchScreen({ playback, lineups, selected, onSelect, onBack }) {
  const { trace, seconds, seen, playing, setPlaying, speed, setSpeed, replaying, halfBanner, skipReplay } = playback;
  const numbers = useMemo(
    () =>
      Object.fromEntries(
        ["home", "away"].flatMap((t) => (lineups?.[t]?.starters || []).map((p) => [p.name, p.number])),
      ),
    [lineups],
  );
  const tick = interpolatedTick(trace, seconds);
  // Changement de camp à la mi-temps : le moteur garde « domicile attaque vers x croissant » tout le match (terrain
  // symétrique, rien n'y dépend du côté) ; l'écran tourne la scène d'un demi-tour en 2e période.
  const time = clock(trace, tick.minute);
  const secondHalf = time.second;
  const view = secondHalf ? rotated(tick) : tick;
  // score : jusqu'à l'instant le plus avancé déjà vu, pour qu'il ne recule pas pendant un ralenti
  const shownS = Math.max(seen, seconds);
  const revealedGoals = trace.goals.filter((g) => g.minute * 60 <= shownS);
  const homeGoals = revealedGoals.filter((g) => g.team === "home").length;
  const awayGoals = revealedGoals.filter((g) => g.team === "away").length;
  const available = (trace.ticks.length - 1) * trace.tick_seconds; // images déjà calculées
  const finished = trace.done && seconds >= available;
  const waiting = !trace.done && seconds >= available; // le rejeu a rattrapé le calcul
  // Coup de sifflet du hors-jeu (ticket v2-collectif/23) : affiché 15 secondes de match après l'événement, pour
  // rester lisible aux vitesses de lecture (x8 par défaut, soit un peu moins de 2 s réelles).
  const recentOffside = (trace.offsides || [])
    .filter((o) => o.minute <= tick.minute && tick.minute - o.minute < 15 / 60)
    .at(-1);

  return (
    <div className="flex flex-col h-full p-2.5 gap-2">
      <div className="flex items-center justify-between gap-2">
        <button onClick={onBack} className="flex items-center gap-1 min-h-11 text-data text-gray-400 shrink-0">
          <ArrowLeft size={14} /> Retour
        </button>
        <div className="text-center">
          <div className="font-bold text-white tabular-nums">
            {trace.home} {homeGoals} - {awayGoals} {trace.away}
          </div>
          <div className="text-caption text-gray-500 tabular-nums">
            {time.label}
            {time.announced != null && ` (+${time.announced})`} · {secondHalf ? "2e" : "1re"} période
            {!trace.done && ` · calcul ${Math.floor(available / 60)}'${waiting ? " (en attente…)" : ""}`}
          </div>
          <div className="text-caption text-gray-400">
            <span className="text-[#4f8ef7]">{situationAt(trace, "home", tick.minute)}</span>
            {" · "}
            <span className="text-[#e0b84a]">{situationAt(trace, "away", tick.minute)}</span>
          </div>
          <div className="text-caption h-[14px] font-semibold text-gold tabular-nums">
            {recentOffside &&
              `⚑ Hors-jeu — ${recentOffside.player} (${recentOffside.team === "home" ? trace.home : trace.away})`}
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

      <div className="flex-1 min-h-0 flex items-center justify-center gap-3">
        <LineupPanel lineup={lineups?.home} color="#4f8ef7" />
        <div className="relative flex flex-col items-center gap-1 w-full max-w-4xl">
          <Momentum trace={trace} played={Math.ceil(shownS / 60)} goalsShown={trace.goals.filter((g) => g.minute <= shownS / 60).length} />
          <V2Pitch
            tick={view}
            seconds={seconds}
            warmUpFromS={halfStart(trace) * 60}
            numbers={numbers}
            lineups={lineups}
            selected={selected}
            onSelect={onSelect}
          />
          {halfBanner && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/60 rounded-lg pointer-events-none">
              <div className="text-center">
                <div className="text-3xl font-extrabold text-white tracking-widest">MI-TEMPS</div>
                <div className="text-lg text-gray-200 tabular-nums">
                  {trace.home} {homeGoals} - {awayGoals} {trace.away}
                </div>
              </div>
            </div>
          )}
        </div>
        <LineupPanel lineup={lineups?.away} color="#e0b84a" />
      </div>

      <IntentionPanel trace={trace} tick={selected ? tick : null} selected={selected} />

      {finished && (
        <p className="text-center text-sm text-gold font-semibold">
          Match terminé : {trace.home} {homeGoals} - {awayGoals} {trace.away}
        </p>
      )}
    </div>
  );
}
