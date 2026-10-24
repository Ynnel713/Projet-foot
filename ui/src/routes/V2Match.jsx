import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, LoaderCircle, Pause, Play } from "lucide-react";
import { createV2Match, getPersoClubs } from "../api/client";
import dims from "../utils/pitchGeometry.json";

// Vitesses en multiples du TEMPS RÉEL (validées par le propriétaire, 24/10/2026) : x8 par défaut, soit ~11 min
// pour 90 minutes de match. Entre deux positions enregistrées (~1 s de match d'écart, voir api/routers/v2.py),
// joueurs et ballon glissent en ligne droite au lieu de sauter (voir `interpolatedTick`).
const SPEED_OPTIONS = [1, 4, 8, 16]; // x1 = vitesse réelle (ajoutée à la demande du propriétaire, 24/10/2026)
const DEFAULT_SPEED = 8;

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
  return {
    minute: mix(a.minute, b.minute),
    players: a.players.map((p, k) => ({ ...p, x: mix(p.x, b.players[k].x), y: mix(p.y, b.players[k].y) })),
    ball: { x: mix(a.ball.x, b.ball.x), y: mix(a.ball.y, b.ball.y) },
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
    if (!playing || !trace) return undefined;
    const end = (trace.ticks.length - 1) * trace.tick_seconds;
    let frame;
    let previous = performance.now();
    const loop = (now) => {
      const elapsed = (now - previous) / 1000;
      previous = now;
      setSeconds((t) => {
        const next = Math.min(end, t + elapsed * speed);
        if (next >= end) setPlaying(false);
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
    try {
      const result = await createV2Match({ home, away });
      setTrace(result);
      setSeconds(0);
      setPlaying(true);
    } catch {
      setError("Échec de la simulation.");
    } finally {
      setLaunching(false);
    }
  }

  if (!trace) {
    return (
      <div className="p-4 sm:p-6 max-w-xl mx-auto flex flex-col gap-4">
        <button onClick={() => navigate("/")} className="flex items-center gap-1 text-xs text-gray-400 self-start">
          <ArrowLeft size={14} /> Retour
        </button>
        <h1 className="text-2xl font-extrabold text-white">⚽ Version 2 (bêta)</h1>
        <p className="text-sm text-gray-400">
          Moteur physique piloté par les attributs réels des joueurs : l'issue n'est pas décidée à l'avance, elle
          émerge de la simulation. Un match complet prend quelques dizaines de secondes à calculer.
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
              <LoaderCircle size={18} className="animate-spin" /> Simulation du match…
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
  const finished = seconds >= (trace.ticks.length - 1) * trace.tick_seconds;

  return (
    <div className="flex flex-col h-full p-2.5 gap-2">
      <div className="flex items-center justify-between gap-2">
        <button onClick={() => navigate("/")} className="flex items-center gap-1 text-xs text-gray-400 shrink-0">
          <ArrowLeft size={14} /> Retour
        </button>
        <div className="text-center">
          <div className="font-bold text-white tabular-nums">
            {trace.home} {homeGoals} - {awayGoals} {trace.away}
          </div>
          <div className="text-[11px] text-gray-500 tabular-nums">{Math.floor(tick.minute)}'</div>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          {SPEED_OPTIONS.map((s) => (
            <button
              key={s}
              onClick={() => setSpeed(s)}
              className={`text-xs px-2 py-1 rounded ${speed === s ? "bg-accent text-white" : "bg-surface text-gray-400"}`}
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
        <V2Pitch tick={tick} />
      </div>

      {finished && (
        <p className="text-center text-sm text-gold font-semibold">
          Match terminé : {trace.home} {homeGoals} - {awayGoals} {trace.away}
        </p>
      )}
    </div>
  );
}

function ClubSelect({ label, value, onChange, clubs }) {
  return (
    <label className="flex flex-col gap-1 text-sm text-gray-300">
      {label}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-10 rounded-lg bg-surface border border-white/10 px-2 text-white"
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

function V2Pitch({ tick }) {
  const pad = MARGIN + TRACK;
  const stripe = L / STRIPES;
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
          stroke="rgba(0,0,0,0.4)"
          strokeWidth={0.1}
        />
      ))}
      <circle cx={tick.ball.x} cy={tick.ball.y} r={0.4} fill="white" stroke="black" strokeWidth={0.1} />
    </svg>
  );
}
