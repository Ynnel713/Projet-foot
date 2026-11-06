import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, LoaderCircle, Pause, Play } from "lucide-react";
import { getPersoClubs, getV2Lineup, getV2Match, startV2Match } from "../api/client";
import dims from "../utils/pitchGeometry.json";
import { goalBall } from "../utils/v2GoalBall";
import { COS, GROUND_MATRIX, project } from "../utils/v2Projection";

// Vitesses en multiples du TEMPS RÉEL (demande du propriétaire, 03/11/2026) : x1 par défaut, jusqu'à x8. Entre
// deux positions enregistrées (~1 s de match d'écart, voir api/routers/v2.py), joueurs et ballon glissent en ligne
// droite au lieu de sauter (voir `interpolatedTick`).
const SPEED_OPTIONS = [1, 1.5, 2, 4, 8];
const DEFAULT_SPEED = 1;
// Ralenti de chaque but : une fois le but vu (et REPLAY_AFTER_S de plus), on revient REPLAY_BEFORE_S avant et on
// rejoue l'action à REPLAY_SPEED, puis la lecture reprend là où elle était.
const REPLAY_BEFORE_S = 8;
const REPLAY_AFTER_S = 2;
const REPLAY_SPEED = 0.4;
const HALF_TIME_MIN = 45; // repli tant que le moteur n'a pas encore donné le début de la 2e période
const HALF_TIME_BANNER_MS = 3000; // bandeau « MI-TEMPS », en temps réel quelle que soit la vitesse (ticket 07)

// Début de la 2e période selon le moteur (ticket v2-coach-et-gestion-de-match/07).
const halfStart = (trace) => trace.second_half_start_minute ?? HALF_TIME_MIN;
// Minute affichée, temps additionnel compris (ticket v2-coach-et-gestion-de-match/03, même règle que
// `v2engine.added_time.display_minute`) : 12', 45+2', 67', 90+4'. Renvoie aussi la période et, en temps additionnel,
// les minutes annoncées.
function clock(trace, minute) {
  const second = trace.second_half_start_minute != null && minute >= trace.second_half_start_minute;
  const elapsed = second ? minute - trace.second_half_start_minute : minute;
  const base = second ? HALF_TIME_MIN : 0;
  const added = elapsed >= HALF_TIME_MIN;
  return {
    second,
    label: added ? `${base + HALF_TIME_MIN}+${Math.floor(elapsed - HALF_TIME_MIN) + 1}'` : `${Math.floor(base + elapsed)}'`,
    announced: added ? trace.added_minutes?.[second ? 1 : 0] : null,
  };
}
// Le rejeu démarre quand ce nombre d'images (~1 s de match chacune) est calculé ; le reste arrive pendant qu'on regarde.
const START_BUFFER_TICKS = 60;
const POLL_MS = 1000;

// Position à `seconds` de match, interpolée entre les deux ticks enregistrés qui l'encadrent. Les joueurs gardent
// le même ordre d'un tick à l'autre (liste construite une fois côté moteur).
function interpolatedTick(trace, seconds) {
  const last = trace.ticks.length - 1;
  const exact = Math.min(last, Math.max(0, seconds / trace.tick_seconds));
  const i = Math.min(last, Math.floor(exact));
  const a = trace.ticks[i];
  const b = trace.ticks[Math.min(last, i + 1)];
  // la mi-temps replace tout le monde d'un coup : pas de glissade entre la dernière image de la 1re période et la
  // première de la 2e (elle est cachée par le bandeau)
  const half = halfStart(trace);
  const f = a.minute < half && b.minute >= half ? 0 : exact - i;
  const mix = (u, v) => u + (v - u) * f;
  const minute = mix(a.minute, b.minute);
  // but entre les deux images : le ballon entre dans le but au lieu de glisser vers le rond central
  const scored = goalBall(a, b, minute, trace.goals, dims.pitch_length_m, dims.pitch_width_m);
  // mode (« sol » / « aérien ») et ballon mort : ceux de l'image de départ (ticket v2-hauteur-ballon/01)
  const state = { mode: a.ball.mode, dead: a.ball.dead };
  return {
    minute,
    players: a.players.map((p, k) => ({ ...p, x: mix(p.x, b.players[k].x), y: mix(p.y, b.players[k].y) })),
    ball: scored
      ? { ...scored, holder: null, ...state }
      : { x: mix(a.ball.x, b.ball.x), y: mix(a.ball.y, b.ball.y), holder: a.ball.holder, ...state },
  };
}

// Écran V2 (docs/PRD_PRODUIT.md US-27 à 29, docs/PLAN_V2.md Phase 4) : lance un match isolé, puis
// rejoue sa trace déjà calculée (voir v2engine/match.py) -- le score n'est révélé qu'au fil des
// buts horodatés dans la trace, jamais affiché avant que la lecture ne les atteigne (US-29).
export default function V2Match() {
  const navigate = useNavigate();
  const [clubs, setClubs] = useState([]);
  const [home, setHome] = useState("");
  const [away, setAway] = useState("");
  const [launching, setLaunching] = useState(false);
  const [error, setError] = useState(null);
  const [trace, setTrace] = useState(null);
  const [seconds, setSeconds] = useState(0); // temps de match lu (s)
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(DEFAULT_SPEED);
  const [selected, setSelected] = useState(null); // joueur dont on lit l'intention (ADR 0001)
  const [computed, setComputed] = useState(0); // images déjà calculées, pendant l'attente avant le démarrage
  const [lineups, setLineups] = useState(null); // { home, away } : feuilles de match numérotées
  const [replaying, setReplaying] = useState(false);
  const secondsRef = useRef(0);
  const [seen, setSeen] = useState(0); // instant le plus avancé déjà vu : le score ne recule pas pendant un ralenti
  const replayRef = useRef(null); // { end } : instant où le ralenti en cours s'arrête
  const replayedRef = useRef(0); // buts déjà rejoués au ralenti
  const [halfBanner, setHalfBanner] = useState(false);
  const halfRef = useRef({ shown: false, until: 0 }); // bandeau de mi-temps : déjà montré, fin (horloge réelle)
  const traceRef = useRef(null); // dernière trace reçue, lue par la boucle de lecture sans la relancer à chaque lecture
  const runRef = useRef(0); // numéro du lancement en cours : un lancement périmé ou un démontage arrête sa lecture
  useEffect(() => () => { runRef.current += 1; }, []);

  useEffect(() => {
    getPersoClubs()
      .then((list) => {
        setClubs(list);
        if (list.length >= 2) {
          setHome(list[0].name);
          setAway(list[1].name);
        }
      })
      .catch(() => setError("Impossible de charger les clubs."));
  }, []);

  useEffect(() => {
    if (!playing || !traceRef.current) return undefined;
    let frame;
    let previous = performance.now();
    const loop = (now) => {
      const elapsed = (now - previous) / 1000;
      previous = now;
      const live = traceRef.current;
      const end = (live.ticks.length - 1) * live.tick_seconds;
      const replay = replayRef.current;
      let next = Math.min(end, secondsRef.current + elapsed * (replay ? REPLAY_SPEED : speed));
      const half = halfRef.current;
      const halfS = live.second_half_start_minute != null ? live.second_half_start_minute * 60 : null;
      if (half.until) {
        next = secondsRef.current; // bandeau en cours : le match attend
        if (now >= half.until) {
          half.until = 0;
          setHalfBanner(false);
        }
      } else if (!half.shown && !replay && halfS != null && next >= halfS) {
        half.shown = true;
        half.until = now + HALF_TIME_BANNER_MS;
        setHalfBanner(true);
        next = halfS;
      } else if (replay && next >= replay.end) {
        replayRef.current = null;
        setReplaying(false);
      } else if (!replay) {
        const goal = live.goals[replayedRef.current];
        if (goal && next >= goal.minute * 60 + REPLAY_AFTER_S) {
          replayedRef.current += 1;
          replayRef.current = { end: next };
          setReplaying(true);
          next = Math.max(0, goal.minute * 60 - REPLAY_BEFORE_S);
        }
      }
      secondsRef.current = next;
      setSeen((s) => Math.max(s, next));
      setSeconds(next);
      // fin de la lecture seulement si le calcul est fini ; sinon on attend les images suivantes
      if (next >= end && live.done && !replayRef.current) setPlaying(false);
      frame = requestAnimationFrame(loop);
    };
    frame = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(frame);
  }, [playing, speed, trace]);

  async function handleLaunch() {
    if (!home || !away || home === away) {
      setError("Choisis deux clubs différents.");
      return;
    }
    setLaunching(true);
    setError(null);
    setComputed(0);
    const run = ++runRef.current;
    try {
      const [{ id }, homeLineup, awayLineup] = await Promise.all([
        startV2Match({ home, away }),
        getV2Lineup(home),
        getV2Lineup(away),
      ]);
      setLineups({ home: homeLineup, away: awayLineup });
      let ticks = [];
      let started = false;
      for (;;) {
        const res = await getV2Match(id, ticks.length);
        if (run !== runRef.current) return;
        if (res.error) throw new Error(res.error);
        ticks = ticks.concat(res.ticks);
        const live = { ...res, ticks };
        traceRef.current = live;
        setComputed(ticks.length);
        if (started) {
          setTrace(live);
        } else if (ticks.length >= START_BUFFER_TICKS || (res.done && ticks.length > 1)) {
          started = true;
          setTrace(live);
          setSelected(null); // le joueur sélectionné n'est peut-être pas de ce match
          secondsRef.current = 0;
          setSeen(0);
          replayRef.current = null;
          replayedRef.current = 0;
          halfRef.current = { shown: false, until: 0 };
          setHalfBanner(false);
          setReplaying(false);
          setSeconds(0);
          setPlaying(true);
          setLaunching(false);
        }
        if (res.done) break;
        await new Promise((resolve) => setTimeout(resolve, POLL_MS));
      }
    } catch {
      if (run === runRef.current) setError("Échec de la simulation.");
    } finally {
      if (run === runRef.current) setLaunching(false);
    }
  }

  if (!trace) {
    return (
      <div className="p-4 sm:p-6 max-w-xl mx-auto flex flex-col gap-4">
        <button onClick={() => navigate("/")} className="flex items-center gap-1 min-h-11 text-data text-gray-400 self-start">
          <ArrowLeft size={14} /> Retour
        </button>
        <h1 className="text-2xl font-extrabold text-white">⚽ Version 2 (bêta)</h1>
        <p className="text-sm text-gray-400">
          Moteur physique piloté par les attributs réels des joueurs : l'issue n'est pas décidée à l'avance, elle
          émerge de la simulation. Le match se calcule pendant que tu le regardes : il démarre après quelques secondes.
        </p>

        {clubs.length === 0 && !error ? (
          // Premier appel après démarrage de l'API : lecture du fichier joueurs, ~15 s mesurées (24/10/2026).
          <p className="flex items-center gap-2 text-sm text-gray-400">
            <LoaderCircle size={16} className="animate-spin" /> Chargement des clubs…
          </p>
        ) : (
          <>
            <ClubSelect label="Domicile" value={home} onChange={setHome} clubs={clubs} />
            <ClubSelect label="Extérieur" value={away} onChange={setAway} clubs={clubs} />
          </>
        )}

        {error && <p className="text-sm text-red-400">{error}</p>}

        <button
          onClick={handleLaunch}
          disabled={launching || clubs.length === 0}
          className="h-12 rounded-xl bg-accent text-white font-semibold disabled:opacity-40 flex items-center justify-center gap-2"
        >
          {launching ? (
            <>
              <LoaderCircle size={18} className="animate-spin" /> Préparation du match…{" "}
              {computed > 0 && `${Math.floor((computed * 100) / START_BUFFER_TICKS)} %`}
            </>
          ) : (
            "Lancer le match"
          )}
        </button>
      </div>
    );
  }

  const tick = interpolatedTick(trace, seconds);
  // Changement de camp à la mi-temps : le moteur garde « domicile attaque vers x croissant » tout le match (terrain
  // symétrique, rien n'y dépend du côté) ; l'écran tourne la scène d'un demi-tour en 2e période.
  const time = clock(trace, tick.minute);
  const secondHalf = time.second;
  const view = secondHalf ? rotated(tick) : tick;
  const numbers = Object.fromEntries(
    ["home", "away"].flatMap((t) => (lineups?.[t]?.starters || []).map((p) => [p.name, p.number])),
  );
  // score : jusqu'à l'instant le plus avancé déjà vu, pour qu'il ne recule pas pendant un ralenti
  const revealedGoals = trace.goals.filter((g) => g.minute * 60 <= Math.max(seen, seconds));
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
        <button onClick={() => navigate("/")} className="flex items-center gap-1 min-h-11 text-data text-gray-400 shrink-0">
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
              onClick={() => {
                secondsRef.current = replayRef.current?.end ?? secondsRef.current;
                replayRef.current = null;
                setReplaying(false);
              }}
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
          <Momentum trace={trace} seen={Math.max(seen, seconds)} />
          <V2Pitch
            tick={view}
            seconds={seconds}
            warmUpFromS={halfStart(trace) * 60}
            numbers={numbers}
            lineups={lineups}
            selected={selected}
            onSelect={setSelected}
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

      <IntentionPanel trace={trace} tick={tick} selected={selected} />

      {finished && (
        <p className="text-center text-sm text-gold font-semibold">
          Match terminé : {trace.home} {homeGoals} - {awayGoals} {trace.away}
        </p>
      )}
    </div>
  );
}

// Match momentum : une barre par minute, vers le haut quand domicile pousse, vers le bas quand l'extérieur pousse.
// Poussée d'un instant = position du ballon dans la longueur (repère moteur : domicile attaque vers x croissant tout le
// match), accentuée près des buts, plus un bonus à l'équipe qui a le ballon ; moyenne sur la minute.
// ponytail : heuristique territoire + possession, sans les tirs (journal des décisions envoyé seulement en fin de
// calcul) ; à enrichir avec tirs et occasions si la courbe paraît trop plate.
const MOMENTUM_MINUTES = 90; // minimum : le temps additionnel allonge la frise (ticket v2-coach-et-gestion-de-match/03)
const POSSESSION_BONUS = 0.15;

function momentumByMinute(trace) {
  const n = Math.max(MOMENTUM_MINUTES, Math.ceil(trace.ticks.at(-1)?.minute ?? 0));
  const sums = new Array(n).fill(0);
  const counts = new Array(n).fill(0);
  for (const t of trace.ticks) {
    const m = Math.min(n - 1, Math.floor(t.minute));
    const dx = (t.ball.x - L / 2) / (L / 2);
    const holderTeam = t.ball.holder && t.players.find((p) => p.name === t.ball.holder)?.team;
    sums[m] += dx * Math.abs(dx) + (holderTeam === "home" ? POSSESSION_BONUS : holderTeam === "away" ? -POSSESSION_BONUS : 0);
    counts[m] += 1;
  }
  return sums.map((v, m) => (counts[m] ? v / counts[m] : null));
}

function Momentum({ trace, seen }) {
  // recalculé quand de nouvelles images arrivent (une fois par seconde), pas à chaque image affichée
  const values = useMemo(() => momentumByMinute(trace), [trace]);
  const now = seen / 60;
  const X = 4; // largeur d'une minute (unités du viewBox)
  const H = 14; // demi-hauteur
  // échelle sur les minutes déjà jouées seulement : la courbe ne trahit rien de la suite
  const scale = H / Math.max(0.2, ...values.map((v, m) => (m < now ? Math.abs(v ?? 0) : 0)));
  const goals = trace.goals.filter((g) => g.minute <= now);
  const width = values.length * X;
  return (
    <svg viewBox={`-2 -6 ${width + 4} ${2 * H + 12}`} className="w-full" style={{ maxHeight: 110 }}>
      <title>Match momentum</title>
      <rect x={0} y={0} width={width} height={H} fill="rgba(79,142,247,0.12)" />
      <rect x={0} y={H} width={width} height={H} fill="rgba(224,184,74,0.12)" />
      {values.map((v, m) =>
        v == null || m >= now ? null : (
          <rect
            key={m}
            x={m * X + 0.4}
            width={X - 0.8}
            y={v > 0 ? H - v * scale : H}
            height={Math.abs(v) * scale}
            fill={v > 0 ? "#4f8ef7" : "#e0b84a"}
          />
        ),
      )}
      <line x1={0} y1={H} x2={width} y2={H} stroke="rgba(255,255,255,0.3)" strokeWidth={0.2} />
      <line x1={halfStart(trace) * X} y1={0} x2={halfStart(trace) * X} y2={2 * H} stroke="white" strokeWidth={0.6} />
      {goals.map((g, i) => (
        <text
          key={i}
          x={g.minute * X}
          y={g.team === "home" ? -3 : 2 * H + 3}
          textAnchor="middle"
          dominantBaseline="central"
          fontSize={5}
        >
          ⚽
        </text>
      ))}
    </svg>
  );
}

// Demi-tour de la scène autour du rond central (2e période) : chaque équipe attaque l'autre but.
function rotated(tick) {
  const turn = (o) => ({ ...o, x: L - o.x, y: W - o.y });
  return { ...tick, players: tick.players.map(turn), ball: turn(tick.ball) };
}

// Composition d'une équipe, à côté du terrain : numéro, poste, nom ; banc et entraîneur dessous.
function LineupPanel({ lineup, color }) {
  if (!lineup) return null;
  const row = (p) => (
    <li key={p.name} className="flex gap-1.5 leading-tight">
      <span className="w-5 text-right font-bold tabular-nums" style={{ color }}>
        {p.number}
      </span>
      <span className="w-9 text-gray-500">{p.poste}</span>
      <span className="truncate text-gray-200">{p.name}</span>
    </li>
  );
  return (
    <div className="hidden lg:flex flex-col gap-1 w-52 shrink-0 text-caption self-stretch overflow-y-auto">
      <div className="font-bold text-sm truncate" style={{ color }}>
        {lineup.club}
      </div>
      <div className="text-gray-500">{lineup.formation}</div>
      <ul className="flex flex-col gap-0.5">{lineup.starters.map(row)}</ul>
      <div className="mt-2 text-gray-400 font-semibold">Remplaçants</div>
      <ul className="flex flex-col gap-0.5">{lineup.bench.map(row)}</ul>
      {lineup.coach && (
        <div className="mt-2 text-gray-400">
          Entraîneur : <span className="text-gray-200">{lineup.coach}</span>
        </div>
      )}
    </div>
  );
}

// Situation de jeu d'une équipe à `minute` : dernier changement enregistré avant cet instant (ticket v2-collectif/03).
function situationAt(trace, team, minute) {
  return (trace.situations || []).filter((s) => s.team === team && s.minute <= minute).at(-1)?.situation || "";
}

// Situation perçue : celle de son équipe, mais l'ancienne tant que son délai de réaction n'est pas écoulé.
function perceivedSituation(trace, team, minute, delayS) {
  const changes = (trace.situations || []).filter((s) => s.team === team && s.minute <= minute);
  const last = changes.at(-1);
  if (last && (minute - last.minute) * 60 < delayS && changes.length > 1) return changes.at(-2).situation;
  return last?.situation || "";
}

// Intention du joueur sélectionné à l'instant lu : dernier segment commencé avant `tick.minute` (la trace n'envoie
// un segment qu'au changement de rôle ou d'action), et dernière décision prise s'il a eu le ballon.
function IntentionPanel({ trace, tick, selected }) {
  if (!selected) {
    return <p className="text-center text-data text-gray-500">Touchez un joueur pour voir ce qu'il cherche à faire.</p>;
  }
  // intentions et décisions n'arrivent qu'une fois le calcul fini
  const player = tick.players.find((p) => p.name === selected);
  const intentions = (trace.intentions || []).find((i) => i.player === selected);
  const segments = intentions?.segments || [];
  const current = segments.filter((s) => s.minute <= tick.minute).at(-1);
  const decision = (trace.decisions || []).filter((d) => d.player === selected && d.minute <= tick.minute).at(-1);
  const ACTIONS = { pass: "passe", dribble: "conduite", shot: "tir" };
  return (
    <div className="rounded-lg bg-surface px-3 py-2 text-sm text-gray-200">
      <div className="font-semibold text-white">
        {selected} {player && <span className="text-data text-gray-400">({player.poste})</span>}
      </div>
      {player && (
        <div className="text-data text-gray-400">
          Situation perçue : {perceivedSituation(trace, player.team, tick.minute, intentions?.reaction_delay_s || 0)}
        </div>
      )}
      {current ? (
        <div>
          <span className="text-accent">{current.role}</span> : {current.action}
          {current.mate ? ` (${current.mate})` : ""} — {current.reason}
        </div>
      ) : (
        <div className="text-gray-500">
          {trace.done ? "Pas encore d'intention enregistrée." : "Intentions disponibles à la fin du calcul du match."}
        </div>
      )}
      {decision && (
        <div className="text-data text-gray-400">
          Dernière décision ({clock(trace, decision.minute).label}) : {ACTIONS[decision.action] || decision.action}
          {decision.target ? ` vers ${decision.target}` : ""}, {decision.considered} option(s) envisagée(s)
          {decision.best_kind ? "" : decision.best ? ", la meilleure" : ", pas la meilleure"}
          {decision.best_kind && (
            <div>
              Meilleur choix : {ACTIONS[decision.best_kind] || decision.best_kind}. Choisi :{" "}
              {ACTIONS[decision.action] || decision.action}
              {decision.gap > 0 ? ` (${errorLabel(decision.gap)})` : ""}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Écart de valeur avec le meilleur choix factuel, en part de celui-ci (ticket v2-collectif/33).
function errorLabel(gap) {
  // sous 10 % : erreur légère, comptée comme le meilleur choix (BEST_CHOICE_TOLERANCE, texte du ticket)
  if (gap < 0.1) return "erreur légère";
  return gap < 0.4 ? "erreur nette" : "erreur lourde";
}

function ClubSelect({ label, value, onChange, clubs }) {
  return (
    <label className="flex flex-col gap-1 text-sm text-gray-300">
      {label}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-10 rounded-lg bg-surface border border-line px-2 text-white"
      >
        {clubs.map((c) => (
          <option key={c.name} value={c.name}>
            {c.name}
          </option>
        ))}
      </select>
    </label>
  );
}

// Terrain simple, réutilise seulement les COTES réelles de la V1 (pitchGeometry.json, dérivé de
// ligue1sim.pitch_geometry) -- pas le composant PitchField.jsx lui-même, dont l'orientation est
// couplée à l'historique spécifique de l'écran PitchView (voir docs/TRD_V2.md, D-V01 : module V2
// séparé). viewBox en mètres réels : les positions de la trace (mêmes mètres) s'y posent sans
// conversion.
const L = dims.pitch_length_m;
const W = dims.pitch_width_m;
const GOAL_WIDTH = dims.goal_width_m;
const CENTER_CIRCLE_R = dims.center_circle_radius_m;
const PA_DEPTH = dims.penalty_area_depth_m;
const PA_WIDTH = dims.penalty_area_width_m;
const GA_DEPTH = dims.goal_area_depth_m;
const GA_WIDTH = dims.goal_area_width_m;
const SPOT = dims.penalty_spot_distance_m;
const ARC_R = dims.penalty_arc_radius_m;
const NET = dims.goal_net_depth_m;
const CORNER_R = dims.corner_arc_radius_m;

// Habillage inspiré d'une vue aérienne de stade (retour du propriétaire, 24/10/2026) : pelouse tondue en bandes,
// marquages complets, buts avec filets, bord de terrain et piste. Dessiné en SVG plutôt qu'en photo : la photo est
// prise en légère perspective, les joueurs (positions en mètres) ne tomberaient pas sur ses lignes.
const MARGIN = 6; // bord de pelouse autour des lignes (m)
const TRACK = 2; // piste autour du bord (m)
const STRIPES = 18; // bandes de tonte sur la longueur
const LINE = { fill: "none", stroke: "rgba(255,255,255,0.9)", strokeWidth: 0.15 };

const BENCH_ZONE = 7; // bande sous la piste, côté tribune principale, où sont les bancs (m)
const BENCH_Y = W + MARGIN + TRACK + 3; // axe des bancs
const BENCH_GAP = 4; // des bancs à la ligne médiane (m)
const SEAT = 1.6; // largeur d'un siège (m)
const WARMING_UP = 3; // remplaçants de champ qui s'échauffent en 2e période

function PlayerNumber({ x, y, value, size = 1.4 }) {
  if (value == null) return null;
  return (
    <text
      x={x}
      y={y}
      textAnchor="middle"
      dominantBaseline="central"
      fontSize={size}
      fontWeight="bold"
      fill="white"
      stroke="rgba(0,0,0,0.6)"
      strokeWidth={0.2}
      paintOrder="stroke"
      style={{ pointerEvents: "none" }}
    >
      {value}
    </text>
  );
}

// Banc d'une équipe sous le terrain (`side` -1 : à gauche de la ligne médiane, 1 : à droite) : entraîneur et
// remplaçants assis ; en 2e période, quelques remplaçants de champ trottinent le long de la ligne de touche, de leur
// côté du terrain (mouvement de va-et-vient purement décoratif, fonction du temps de match lu).
// échauffement à partir du coup d'envoi de la 2e période, après le temps additionnel de la 1re (ticket coach/03)
function Bench({ lineup, side, color, seconds, warmUpFromS }) {
  const warmers = seconds >= warmUpFromS ? lineup.bench.filter((p) => p.poste !== "GK").slice(0, WARMING_UP) : [];
  const seated = lineup.bench.filter((p) => !warmers.includes(p));
  const seats = seated.length + 1; // + l'entraîneur, au bout côté ligne médiane
  const length = seats * SEAT + 1;
  const x0 = side < 0 ? L / 2 - BENCH_GAP - length : L / 2 + BENCH_GAP;
  const seatX = (i) => (side < 0 ? x0 + length - 0.5 - SEAT * (i + 0.5) : x0 + 0.5 + SEAT * (i + 0.5));
  // sièges et remplaçants : ronds et chiffres projetés (jamais écrasés) ; les bancs eux-mêmes sont à plat
  const seat = project(seatX(0), BENCH_Y);
  return (
    <g>
      <g transform={GROUND_MATRIX}>
        <rect x={x0} y={BENCH_Y - 1.6} width={length} height={3.2} rx={0.6} fill="rgba(20,24,30,0.85)" stroke="rgba(255,255,255,0.5)" strokeWidth={0.12} />
      </g>
      <g>
        <rect x={seat.x - 0.8} y={seat.y - 0.8} width={1.6} height={1.6} rx={0.3} fill="#222" stroke="white" strokeWidth={0.12} />
        <text x={seat.x} y={seat.y} textAnchor="middle" dominantBaseline="central" fontSize={1} fill="white" fontWeight="bold">
          E
        </text>
        <title>{`Entraîneur${lineup.coach ? ` : ${lineup.coach}` : ""}`}</title>
      </g>
      {seated.map((p, i) => {
        const c = project(seatX(i + 1), BENCH_Y);
        return (
          <g key={p.name}>
            <circle cx={c.x} cy={c.y} r={0.75} fill={color} opacity={0.85} stroke="rgba(0,0,0,0.4)" strokeWidth={0.08} />
            <PlayerNumber x={c.x} y={c.y} value={p.number} size={0.9} />
            <title>{`${p.number} ${p.name} (${p.poste})`}</title>
          </g>
        );
      })}
      {warmers.map((p, i) => {
        // va-et-vient sur 12 m, chacun décalé, entre la ligne de touche et la piste
        const phase = seconds * 0.35 + i * 2.1;
        const c = project(L / 2 + side * (24 + 6 + 6 * Math.sin(phase)), W + 1.5 + i * 1.4);
        return (
          <g key={p.name}>
            <circle cx={c.x} cy={c.y} r={0.9} fill={color} opacity={0.75} stroke="rgba(0,0,0,0.4)" strokeWidth={0.08} />
            <PlayerNumber x={c.x} y={c.y} value={p.number} size={1} />
            <title>{`${p.number} ${p.name} s'échauffe`}</title>
          </g>
        );
      })}
    </g>
  );
}

// Arc de la surface (hors surface uniquement) : intersection du cercle de rayon ARC_R autour du point de penalty
// avec la ligne de surface.
const ARC_DY = Math.sqrt(ARC_R ** 2 - (PA_DEPTH - SPOT) ** 2);

function GoalEnd({ flip }) {
  // Dessin côté x=0 ; `flip` le recopie en miroir côté x=L.
  const y0 = W / 2;
  return (
    <g transform={flip ? `translate(${L} 0) scale(-1 1)` : undefined}>
      <rect x={0} y={y0 - PA_WIDTH / 2} width={PA_DEPTH} height={PA_WIDTH} {...LINE} />
      <rect x={0} y={y0 - GA_WIDTH / 2} width={GA_DEPTH} height={GA_WIDTH} {...LINE} />
      <circle cx={SPOT} cy={y0} r={0.25} fill="white" />
      <path d={`M ${PA_DEPTH} ${y0 - ARC_DY} A ${ARC_R} ${ARC_R} 0 0 1 ${PA_DEPTH} ${y0 + ARC_DY}`} {...LINE} />
      <rect x={-NET} y={y0 - GOAL_WIDTH / 2} width={NET} height={GOAL_WIDTH} fill="url(#v2-net)" stroke="white" strokeWidth={0.2} />
    </g>
  );
}

// Joueurs, buts et ballon sur la caméra inclinée (ticket v2-hauteur-ballon/01).
const PLAYER_R = 1.3; // rayon du rond d'un joueur (m)
// Le rond d'un joueur est dessiné à la hauteur de sa taille : sans cela il recouvrirait son ombre. Valeur validée par
// le propriétaire le 06/11/2026 ; si l'ombre est trop discrète sur téléphone, jouer sur son opacité, pas sur cette hauteur.
const PLAYER_LIFT = 1.8;
const SHADOW_K = 0.8; // ombre d'un joueur : ovale de rayon 0,8 × celui du rond (validé le 04/11/2026)
const SHADOW_OPACITY = 0.25;
const CROSSBAR = 2.44; // hauteur de la barre transversale (m)
const BALL_R = 0.4;
const BALL_AIR_R = 0.6;
const BALL_AIR_Z = 1; // hauteur fixe d'un ballon aérien, jusqu'au ticket 02b (vraie hauteur à l'écran)

// Poteaux et barre d'un but (`x` : ligne de but), par la projection : z = 0 puis z = 2,44 m.
function GoalFrame({ x }) {
  const ys = [W / 2 - GOAL_WIDTH / 2, W / 2 + GOAL_WIDTH / 2];
  const [foot0, foot1] = ys.map((y) => project(x, y));
  const [top0, top1] = ys.map((y) => project(x, y, CROSSBAR));
  const stroke = { stroke: "white", strokeWidth: 0.3, strokeLinecap: "round" };
  return (
    <g style={{ pointerEvents: "none" }}>
      <line x1={foot0.x} y1={foot0.y} x2={top0.x} y2={top0.y} {...stroke} />
      <line x1={foot1.x} y1={foot1.y} x2={top1.x} y2={top1.y} {...stroke} />
      <line x1={top0.x} y1={top0.y} x2={top1.x} y2={top1.y} {...stroke} />
    </g>
  );
}

function V2Pitch({ tick, seconds, warmUpFromS, numbers, lineups, selected, onSelect }) {
  const pad = MARGIN + TRACK;
  const stripe = L / STRIPES;
  const height = (W + 2 * pad + BENCH_ZONE) * COS;
  // du fond (y petit) vers l'avant : le joueur le plus proche de la caméra recouvre le plus lointain
  const players = [...tick.players]
    .sort((a, b) => a.y - b.y)
    .map((p) => ({ ...p, ground: project(p.x, p.y), body: project(p.x, p.y, PLAYER_LIFT) }));
  const holder = players.find((p) => p.name === tick.ball.holder);
  const air = tick.ball.mode === "aérien";
  const ballGround = project(tick.ball.x, tick.ball.y);
  const ball = project(tick.ball.x, tick.ball.y, air ? BALL_AIR_Z : 0);
  const ballR = air ? BALL_AIR_R : BALL_R;
  return (
    <svg
      viewBox={`${-pad} ${-pad * COS} ${L + 2 * pad} ${height}`}
      className="w-full max-w-4xl rounded-lg"
      style={{ aspectRatio: `${L + 2 * pad} / ${height}` }}
    >
      <defs>
        <pattern id="v2-net" width={0.5} height={0.5} patternUnits="userSpaceOnUse">
          <rect width={0.5} height={0.5} fill="rgba(255,255,255,0.15)" />
          <path d="M 0 0 L 0.5 0 M 0 0 L 0 0.5" stroke="rgba(255,255,255,0.6)" strokeWidth={0.05} />
        </pattern>
      </defs>
      {/* 1. pelouse et lignes : à plat, écrasées par la même projection (z = 0) */}
      <g transform={GROUND_MATRIX}>
        <rect x={-pad} y={-pad} width={L + 2 * pad} height={W + 2 * pad + BENCH_ZONE} fill="#5a5f66" />
        <rect x={-pad} y={-pad} width={L + 2 * pad} height={W + 2 * pad} fill="#9c4a3c" />
        <rect x={-MARGIN} y={-MARGIN} width={L + 2 * MARGIN} height={W + 2 * MARGIN} fill="#2f7d32" />
        {Array.from({ length: STRIPES }, (_, i) => (
          <rect key={i} x={i * stripe} y={-MARGIN} width={stripe} height={W + 2 * MARGIN} fill={i % 2 ? "#3a8f3c" : "#2f7d32"} />
        ))}

        <rect x={0} y={0} width={L} height={W} {...LINE} />
        <line x1={L / 2} y1={0} x2={L / 2} y2={W} {...LINE} />
        <circle cx={L / 2} cy={W / 2} r={CENTER_CIRCLE_R} {...LINE} />
        <circle cx={L / 2} cy={W / 2} r={0.3} fill="white" />
        {[
          [0, 0, 0],
          [L, 0, 90],
          [L, W, 180],
          [0, W, 270],
        ].map(([x, y, rot]) => (
          <path key={rot} d={`M ${CORNER_R} 0 A ${CORNER_R} ${CORNER_R} 0 0 1 0 ${CORNER_R}`} transform={`translate(${x} ${y}) rotate(${rot})`} {...LINE} />
        ))}
        <GoalEnd />
        <GoalEnd flip />
      </g>
      {lineups && <Bench lineup={lineups.home} side={-1} color="#4f8ef7" seconds={seconds} warmUpFromS={warmUpFromS} />}
      {lineups && <Bench lineup={lineups.away} side={1} color="#e0b84a" seconds={seconds} warmUpFromS={warmUpFromS} />}

      {/* 2. ombres au sol */}
      {players.map((p) => (
        <ellipse
          key={`shadow-${p.name}`}
          cx={p.ground.x}
          cy={p.ground.y}
          rx={PLAYER_R * SHADOW_K}
          ry={PLAYER_R * SHADOW_K * COS}
          fill="black"
          opacity={SHADOW_OPACITY}
          style={{ pointerEvents: "none" }}
        />
      ))}
      {air && (
        <ellipse
          cx={ballGround.x}
          cy={ballGround.y}
          rx={ballR}
          ry={ballR * COS}
          fill="black"
          opacity={0.3}
          style={{ pointerEvents: "none" }}
        />
      )}

      {/* 3. joueurs, triés du fond vers l'avant : vrais cercles */}
      {players.map((p) => (
        <g key={p.name} onClick={() => onSelect(p.name === selected ? null : p.name)} style={{ cursor: "pointer" }}>
          <circle
            cx={p.body.x}
            cy={p.body.y}
            r={PLAYER_R}
            fill={p.team === "home" ? "#4f8ef7" : "#e0b84a"}
            stroke={p.name === selected ? "white" : "rgba(0,0,0,0.4)"}
            strokeWidth={p.name === selected ? 0.4 : 0.1}
          />
          <PlayerNumber x={p.body.x} y={p.body.y} value={numbers[p.name]} />
        </g>
      ))}

      {/* 4. buts en hauteur */}
      <GoalFrame x={0} />
      <GoalFrame x={L} />

      {/* 5. ballon : plus gros et remonté s'il est aérien (hauteur fixe d'un mètre, provisoire) ; atténué s'il est mort */}
      <circle
        cx={ball.x}
        cy={ball.y}
        r={ballR}
        fill="white"
        stroke="black"
        strokeWidth={0.1}
        opacity={tick.ball.dead ? 0.6 : 1}
        style={{ pointerEvents: "none" }}
      />

      {/* 6. nom du porteur, sous son rond ; le contour sombre le garde lisible sur la pelouse comme sur les lignes */}
      {holder && (
        <text
          x={holder.body.x}
          y={holder.body.y + 3.2}
          textAnchor="middle"
          fontSize={1.8}
          fontWeight="bold"
          fill="white"
          stroke="black"
          strokeWidth={0.35}
          paintOrder="stroke"
          style={{ pointerEvents: "none" }}
        >
          {holder.name}
        </text>
      )}
    </svg>
  );
}
