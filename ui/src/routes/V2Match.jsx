import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, LoaderCircle, Pause, Play } from "lucide-react";
import { getPersoClubs, getV2Match, startV2Match } from "../api/client";
import dims from "../utils/pitchGeometry.json";
import { goalBall } from "../utils/v2GoalBall";

// Vitesses en multiples du TEMPS RÉEL (validées par le propriétaire, 24/10/2026) : x8 par défaut, soit ~11 min
// pour 90 minutes de match. Entre deux positions enregistrées (~1 s de match d'écart, voir api/routers/v2.py),
// joueurs et ballon glissent en ligne droite au lieu de sauter (voir `interpolatedTick`).
const SPEED_OPTIONS = [1, 4, 8, 16]; // x1 = vitesse réelle (ajoutée à la demande du propriétaire, 24/10/2026)
const DEFAULT_SPEED = 8;
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
  const f = exact - i;
  const mix = (u, v) => u + (v - u) * f;
  const minute = mix(a.minute, b.minute);
  // but entre les deux images : le ballon entre dans le but au lieu de glisser vers le rond central
  const scored = goalBall(a, b, minute, trace.goals, dims.pitch_length_m, dims.pitch_width_m);
  return {
    minute,
    players: a.players.map((p, k) => ({ ...p, x: mix(p.x, b.players[k].x), y: mix(p.y, b.players[k].y) })),
    ball: scored ? { ...scored, holder: null } : { x: mix(a.ball.x, b.ball.x), y: mix(a.ball.y, b.ball.y), holder: a.ball.holder },
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
      setSeconds((t) => {
        const next = Math.min(end, t + elapsed * speed);
        // fin de la lecture seulement si le calcul est fini ; sinon on attend les images suivantes
        if (next >= end && live.done) setPlaying(false);
        return next;
      });
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
      const { id } = await startV2Match({ home, away });
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
  const revealedGoals = trace.goals.filter((g) => g.minute <= tick.minute);
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
            {Math.floor(tick.minute)}'
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

      <div className="flex-1 min-h-0 flex items-center justify-center">
        <V2Pitch tick={tick} selected={selected} onSelect={setSelected} />
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
          Dernière décision ({Math.floor(decision.minute)}') : {ACTIONS[decision.action] || decision.action}
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

function V2Pitch({ tick, selected, onSelect }) {
  const pad = MARGIN + TRACK;
  const stripe = L / STRIPES;
  const holder = tick.players.find((p) => p.name === tick.ball.holder);
  return (
    <svg
      viewBox={`${-pad} ${-pad} ${L + 2 * pad} ${W + 2 * pad}`}
      className="w-full max-w-4xl rounded-lg"
      style={{ aspectRatio: `${L + 2 * pad} / ${W + 2 * pad}` }}
    >
      <defs>
        <pattern id="v2-net" width={0.5} height={0.5} patternUnits="userSpaceOnUse">
          <rect width={0.5} height={0.5} fill="rgba(255,255,255,0.15)" />
          <path d="M 0 0 L 0.5 0 M 0 0 L 0 0.5" stroke="rgba(255,255,255,0.6)" strokeWidth={0.05} />
        </pattern>
      </defs>
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

      {tick.players.map((p) => (
        <circle
          key={p.name}
          cx={p.x}
          cy={p.y}
          r={1.1}
          fill={p.team === "home" ? "#4f8ef7" : "#e0b84a"}
          stroke={p.name === selected ? "white" : "rgba(0,0,0,0.4)"}
          strokeWidth={p.name === selected ? 0.4 : 0.1}
          onClick={() => onSelect(p.name === selected ? null : p.name)}
          style={{ cursor: "pointer" }}
        />
      ))}
      {holder && (
        // nom du porteur, sous son rond ; le contour sombre le garde lisible sur la pelouse comme sur les lignes
        <text
          x={holder.x}
          y={holder.y + 3.2}
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
      <circle cx={tick.ball.x} cy={tick.ball.y} r={0.4} fill="white" stroke="black" strokeWidth={0.1} />
    </svg>
  );
}
