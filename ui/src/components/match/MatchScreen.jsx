import { useCallback, useLayoutEffect, useMemo, useRef, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import IntentionPanel from "./IntentionPanel";
import LineupPanel from "./LineupPanel";
import MatchHud from "./MatchHud";
import StatsDrawer from "./StatsDrawer";
import { FullTimeCard, HalfTimeBanner, TopBanner } from "./MatchBanner";
import MomentumTimeline from "./MomentumTimeline";
import V2Pitch from "./V2Pitch";
import { teamColors, teamColorVars } from "../../utils/teamColors";
import { goalsByPlayer, lineupDensity } from "../../utils/lineupCards";
import { L, clock, halfStart, interpolatedTick, rotated } from "./trace";
import { goalBannerText, matchBadge, revealedScore, revealedScorers } from "../../utils/matchHud";
import { netWave } from "../../utils/v2NetWave";
import { ballMotion, ballSpeed, trailLength } from "../../utils/v2BallLook";

// Écran de lecture de la V2 (ticket v2-ecran-match/01 : déplacé depuis routes/V2Match.jsx). Le score n'est révélé
// qu'au fil des buts horodatés dans la trace, jamais avant que la lecture ne les atteigne (US-29).
//
// Mise en page en trois zones (ticket v2-ecran-match/04, constantes validées par le propriétaire le 18/11/2026) :
// HUD en haut, centre (compositions + terrain), zone basse (momentum + intention, 110 px au plus, frise de 72 px ;
// sous 500 px de haut, repliée sur la ligne d'intention, sans la frise : décisions du 18/11/2026 ; un panneau d'intention
// plus haut que la zone y défile, la page jamais, en attendant son tiroir d'EM-15). Compositions en
// colonnes de 220 px dès 1280 px de large, 200 px de 960 à 1279 px ; sous 960 px, tiroirs de 260 px ouverts par une
// languette de 28 px, fermés par défaut, terrain pleine largeur. Compositions en cartes : EM-10a (`LineupPanel`), densité choisie selon la hauteur : EM-10b.
const DRAWER_PX = 260;
const TAB_PX = 28;

// Densité des cartes d'après la hauteur réelle de la colonne ou du tiroir (ticket v2-ecran-match/10b). Elle ne dépend
// que de la taille du conteneur (défilant, de hauteur fixée par la grille) : changer de densité ne la modifie pas, donc
// pas d'aller-retour. Mesure avant affichage (pas de clignotement au premier rendu).
function useColumnDensity(lineup) {
  const ref = useRef(null);
  const [density, setDensity] = useState("complet");
  const starters = lineup?.starters.length ?? 0;
  const bench = lineup?.bench.length ?? 0;
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return undefined;
    const update = () => setDensity(lineupDensity(el.clientHeight, starters, bench));
    update();
    const observer = new ResizeObserver(update);
    observer.observe(el);
    return () => observer.disconnect();
  }, [starters, bench]);
  return [ref, density];
}

// Composition d'un côté : colonne à partir de 960 px, tiroir en dessous (les deux sont dans le DOM, un seul s'affiche).
// `color` (couleur d'équipe pour l'interface) ne sert plus qu'au liseré de la languette : les cartes lisent les jetons
// `--team-<side>` elles-mêmes (ticket v2-ecran-match/10a).
function LineupSide({ side, lineup, color, stats }) {
  const [open, setOpen] = useState(false);
  const [columnRef, columnDensity] = useColumnDensity(lineup);
  const [drawerRef, drawerDensity] = useColumnDensity(lineup);
  if (!lineup) return null;
  const left = side === "home";
  const label = `Composition ${left ? "domicile" : "extérieur"} : ${lineup.club}`;
  const Icon = left === open ? ChevronLeft : ChevronRight;
  return (
    <>
      <aside
        ref={columnRef}
        data-zone={`composition-${side}`}
        aria-label={label}
        className={`hidden min-[960px]:block min-h-0 overflow-y-auto bg-surface px-2 py-1.5 ${left ? "border-r" : "border-l"} border-line`}
      >
        <LineupPanel lineup={lineup} side={side} density={columnDensity} stats={stats} />
      </aside>
      <div
        className={`min-[960px]:hidden absolute inset-y-0 z-20 flex items-center transition-transform duration-200 ease-out motion-reduce:transition-none ${left ? "left-0" : "right-0 flex-row-reverse"}`}
        style={{ transform: open ? "none" : `translateX(${left ? -DRAWER_PX : DRAWER_PX}px)` }}
      >
        <aside
          ref={drawerRef}
          data-zone={`tiroir-${side}`}
          aria-label={label}
          aria-hidden={!open}
          inert={!open}
          className={`h-full overflow-y-auto bg-surface px-2 py-1.5 ${left ? "border-r" : "border-l"} border-line`}
          style={{ width: DRAWER_PX }}
        >
          <LineupPanel lineup={lineup} side={side} density={drawerDensity} stats={stats} />
        </aside>
        <button
          data-zone={`languette-${side}`}
          onClick={() => setOpen((o) => !o)}
          aria-expanded={open}
          aria-label={`${open ? "Fermer" : "Ouvrir"} la composition ${left ? "domicile" : "extérieur"}`}
          className={`h-16 flex items-center justify-center bg-surface border-line text-gray-300 ${left ? "rounded-r-md border-y border-r" : "rounded-l-md border-y border-l"}`}
          style={{ width: TAB_PX, boxShadow: `inset ${left ? 3 : -3}px 0 0 ${color}` }}
        >
          <Icon size={16} />
        </button>
      </div>
    </>
  );
}
// Préférence « moins d'animations » du système, lue une fois (ticket v2-ecran-match/21b : pas d'ondulation du filet).
const reducedMotion = () => typeof window !== "undefined" && !!window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

export default function MatchScreen({ playback, lineups, selected, onSelect, onBack }) {
  const [reduceMotion] = useState(reducedMotion);
  const { trace, seconds, seen, speed, halfBanner, goalBanner, kickoffBanner, replaying } = playback;
  const [endClosed, setEndClosed] = useState(false); // carte de fin refermée (ticket v2-ecran-match/13)
  const [statsOpen, setStatsOpen] = useState(false); // panneau de statistiques (ticket v2-ecran-match/14b)
  const closeStats = useCallback(() => setStatsOpen(false), []);
  const numbers = useMemo(
    () =>
      Object.fromEntries(
        ["home", "away"].flatMap((t) => (lineups?.[t]?.starters || []).map((p) => [p.name, p.number])),
      ),
    [lineups],
  );
  // couleurs d'équipe (ticket v2-ecran-match/03) : variables CSS posées une fois ici, lues par tous les composants
  const colorVars = useMemo(() => teamColorVars(teamColors(lineups)), [lineups]);
  const tick = interpolatedTick(trace, seconds);
  // Changement de camp à la mi-temps : le moteur garde « domicile attaque vers x croissant » tout le match (terrain
  // symétrique, rien n'y dépend du côté) ; l'écran tourne la scène d'un demi-tour en 2e période.
  const time = clock(trace, tick.minute);
  const secondHalf = time.second;
  const view = secondHalf ? rotated(tick) : tick;
  // aspect du ballon (ticket v2-ecran-match/21a) : mouvement lu dans la piste (repère du moteur), direction retournée
  // avec la scène en 2e période ; traînée seulement pour un ballon libre ; vitesse aussi pour un ballon tenu (figement
  // du motif, qui roule avec le dribble)
  const motion = tick.ball.dead ? null : ballMotion(trace.ball_track, tick.minute, halfStart(trace));
  const ballLook = {
    dir: motion && (secondHalf ? { x: -motion.dir.x, y: -motion.dir.y } : motion.dir),
    speed: tick.ball.dead ? 0 : ballSpeed(trace.ball_track, tick.minute, halfStart(trace)),
    playbackSpeed: speed,
    trail: trailLength(motion),
  };
  // filet qui ondule sur un but (ticket v2-ecran-match/21b) : temps de match lu, filet de la vue. Période décidée comme
  // la rotation de la scène (`clock`) : début de 2e période donné par le moteur, sans repli sur 45 (en direct, le champ
  // reste vide jusqu'au coup d'envoi de la 2e période ; réserve A1 de l'expert, 18/11/2026)
  const wave = reduceMotion ? null : netWave(trace.goals, tick.minute, trace.second_half_start_minute ?? Infinity, L);
  // score : jusqu'à l'instant le plus avancé déjà vu, pour qu'il ne recule pas pendant un ralenti
  const shownS = Math.max(seen, seconds);
  const score = revealedScore(trace.goals, shownS);
  const { home: homeGoals, away: awayGoals } = score;
  // buteurs du HUD (ticket v2-ecran-match/08c) : mêmes buts révélés que le score (buts rangés dans l'ordre du match),
  // minute au libellé de l'horloge ; recalculés à chaque but révélé seulement, pas à chaque image
  const revealedGoals = homeGoals + awayGoals;
  const scorers = useMemo(
    () => revealedScorers(trace.goals.slice(0, revealedGoals), Infinity, (minute) => clock(trace, minute).label),
    [trace, revealedGoals],
  );
  // buts par joueur dans la composition (ticket v2-ecran-match/10c) : mêmes buts révélés, recalculés à chaque but
  const playerGoals = useMemo(() => goalsByPlayer(trace.goals.slice(0, revealedGoals)), [trace.goals, revealedGoals]);
  const available = (trace.ticks.length - 1) * trace.tick_seconds; // images déjà calculées
  const finished = trace.done && seconds >= available;
  const waiting = !trace.done && seconds >= available; // le rejeu a rattrapé le calcul
  // Coup de sifflet du hors-jeu (ticket v2-collectif/23) : affiché 15 secondes de match après l'événement, pour
  // rester lisible aux vitesses de lecture (x8 par défaut, soit un peu moins de 2 s réelles).
  const recentOffside = (trace.offsides || [])
    .filter((o) => o.minute <= tick.minute && tick.minute - o.minute < 15 / 60)
    .at(-1);

  return (
    <div className="grid h-full grid-cols-[minmax(0,1fr)] grid-rows-[auto_minmax(0,1fr)_auto]" style={colorVars}>
      <MatchHud
        trace={trace}
        score={score}
        scorers={scorers}
        time={time}
        badge={matchBadge({ finished, halfBanner, replaying, waiting })}
        offside={recentOffside}
        onBack={onBack}
        statsOpen={statsOpen}
        onStats={() => setStatsOpen((o) => !o)}
        playback={playback}
        finished={finished}
      />

      <div
        data-zone="centre"
        className="relative min-h-0 grid grid-cols-[minmax(0,1fr)] min-[960px]:grid-cols-[200px_minmax(0,1fr)_200px] min-[1280px]:grid-cols-[220px_minmax(0,1fr)_220px]"
      >
        <LineupSide side="home" lineup={lineups?.home} color="var(--team-home-ui)" stats={playerGoals} />
        <div data-zone="terrain" className="relative min-h-0 min-w-0 flex items-center justify-center p-2">
          <V2Pitch
            tick={view}
            seconds={seconds}
            warmUpFromS={halfStart(trace) * 60}
            numbers={numbers}
            lineups={lineups}
            selected={selected}
            onSelect={onSelect}
            ballLook={ballLook}
            wave={wave}
            className="w-full h-full"
          />
          {/* états du match (ticket v2-ecran-match/13) : bandeaux sans pointeur, carte de fin refermable */}
          {kickoffBanner && !halfBanner && <TopBanner kind="coup-envoi">COUP D'ENVOI</TopBanner>}
          {goalBanner != null && trace.goals[goalBanner] && (
            <TopBanner kind="but" side={trace.goals[goalBanner].team}>
              {goalBannerText(
                trace.goals[goalBanner],
                clock(trace, trace.goals[goalBanner].minute).label,
                trace.goals[goalBanner].team === "home" ? trace.home : trace.away,
              )}
            </TopBanner>
          )}
          {halfBanner && <HalfTimeBanner home={trace.home} away={trace.away} score={score} />}
          {finished && !endClosed && (
            <FullTimeCard
              home={trace.home}
              away={trace.away}
              score={score}
              scorers={scorers}
              onBack={onBack}
              onClose={() => setEndClosed(true)}
              onStats={() => {
                setEndClosed(true);
                setStatsOpen(true);
              }}
            />
          )}
        </div>
        <LineupSide side="away" lineup={lineups?.away} color="var(--team-away-ui)" stats={playerGoals} />
        {statsOpen && <StatsDrawer trace={trace} shownS={shownS} onClose={closeStats} />}
      </div>

      <div data-zone="bas" className="flex flex-col gap-1 max-h-[110px] min-h-0 overflow-y-auto px-2.5 py-1.5 bg-surface border-t border-line">
        <div className="shrink-0 [@media(max-height:499.98px)]:hidden">
          <MomentumTimeline
            trace={trace}
            shownMin={shownS / 60}
            goalsShown={trace.goals.filter((g) => g.minute <= shownS / 60).length}
          />
        </div>
        <IntentionPanel trace={trace} tick={selected ? tick : null} selected={selected} />
      </div>
    </div>
  );
}
