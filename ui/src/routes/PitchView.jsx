import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams, useSearchParams, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { getBracket, getGroups, getMatches, getPitchView } from "../api/client";
import ClubLogo from "../components/common/ClubLogo";
import PitchField from "../components/pitch/PitchField";
import LivePanel from "../components/pitch/LivePanel";
import MatchAnimation from "../components/pitch/MatchAnimation";
import { GoalAlerts, MultiplexTicker } from "../components/pitch/GoalAlerts";
import { MATCH_END, MIN_PER_TICK, TICK_MS, buildOtherGoals } from "../utils/liveReplay";

// Terrain VERTICAL (portrait, demandé le 02/10/2026) : c'est l'orientation NATIVE du placement calculé côté moteur
// (pitch_layout.place_starting_xi) -- domicile en haut (y 10-42), extérieur en bas (y 58-90), x = position latérale 0-100 --, donc
// aucune permutation : left = x, top = y. (L'ancien terrain horizontal pivotait y -> horizontale et 100 - x -> verticale.)
export default function PitchView() {
  const { id } = useParams();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  // Live rejoué (?replay=1, bouton LIVE) : le match est déjà simulé, on le rejoue de la minute 0 à 90 à une horloge accélérée.
  // Sans `replay` (clic sur le résultat), l'horloge est à 90 : tout est affiché d'emblée, aucune alerte.
  const replay = params.get("replay") === "1";
  const [clock, setClock] = useState(replay ? 0 : MATCH_END);
  const [playing, setPlaying] = useState(replay);
  const [speed, setSpeed] = useState(1);
  const [others, setOthers] = useState([]); // autres matchs de la journée (scores, buteurs, minutes) -- alertes buts + multiplex
  const [alerts, setAlerts] = useState([]);
  const [showAnimation, setShowAnimation] = useState(false); // fenêtre « Voir l'animation » (iframe canvas, voir MatchAnimation)
  const fired = useRef(new Set());
  // Hauteur disponible pour le stade (>= lg) : la hauteur de la ligne de la grille moins le titre. La largeur du stade s'en déduit
  // (portrait 68 x 105) ; elle ne peut pas venir du CSS seul : la colonne `auto` est dimensionnée avant que la hauteur en % soit résolue.
  const pitchBox = useRef(null);
  const [pitchH, setPitchH] = useState(null);

  const home = params.get("home");
  const away = params.get("away");
  const journee = params.get("journee");
  const group = params.get("group");
  const matchday = params.get("matchday");
  const roundNumber = params.get("round_number");
  const leg = params.get("leg");

  // Libellé de contexte : championnat (Journée N), poule (Groupe + journée),
  // ou tableau (Tour N, Aller/Retour) -- voir les 3 jeux de paramètres
  // possibles côté API (api.routers.competitions.get_pitch_view).
  let contextLabel = "";
  if (journee) contextLabel = `Journée ${journee}`;
  else if (group) contextLabel = `${group} · Journée ${Number(matchday) + 1}`;
  else if (roundNumber) contextLabel = `Tour ${roundNumber} · ${leg === "0" ? "Aller" : "Retour"}`;

  useEffect(() => {
    getPitchView(id, { home, away, journee, group, matchday, round_number: roundNumber, leg })
      .then(setData)
      .catch(() => setError("Composition indisponible pour ce match."));
  }, [id, home, away, journee, group, matchday, roundNumber, leg]);

  useEffect(() => {
    const el = pitchBox.current;
    if (!el) return undefined;
    const measure = () => setPitchH(window.matchMedia("(min-width: 1024px)").matches ? Math.floor(el.clientHeight) : null);
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(el);
    return () => observer.disconnect();
  }, [data]);

  // Autres matchs du même créneau, pour les alertes buts et le multiplex : journée de championnat ; journée de poule / de phase de ligue
  // (seulement la DERNIÈRE journée jouée, la seule que l'API détaille) ; manche du même tour d'un tableau.
  useEffect(() => {
    const pasLeCourant = (m) => m.played && !(m.home === home && m.away === away);
    let request = null;
    if (journee) request = getMatches(id, journee);
    else if (group && matchday !== null)
      request = getGroups(id).then((d) => (d.groups_matchday - 1 === Number(matchday) ? d.groups.flatMap((g) => g.current_matches) : []));
    else if (roundNumber && leg !== null)
      request = getBracket(id).then((d) =>
        (d.rounds.find((r) => r.number === Number(roundNumber))?.ties ?? []).map((t) => t.legs[Number(leg)]).filter(Boolean),
      );
    if (!request) return;
    request.then((ms) => setOthers(ms.filter(pasLeCourant))).catch(() => setOthers([]));
  }, [id, journee, group, matchday, roundNumber, leg, home, away]);

  const otherGoals = useMemo(() => buildOtherGoals(others), [others]);

  // Horloge du live : un tick toutes les 100 ms, +1/6 de minute de match en x1 ; s'arrête à 90'.
  useEffect(() => {
    if (!playing) return undefined;
    const timer = setInterval(() => setClock((c) => Math.min(MATCH_END, c + speed * MIN_PER_TICK)), TICK_MS);
    return () => clearInterval(timer);
  }, [playing, speed]);
  useEffect(() => {
    if (clock >= MATCH_END) setPlaying(false);
  }, [clock]);

  // Alerte « BUT ! » pour chaque but des autres matchs dont la minute est atteinte par l'horloge (3 au plus à l'écran, 5 s chacune).
  useEffect(() => {
    if (!replay) return;
    const fresh = otherGoals.filter((g) => g.minute <= clock && !fired.current.has(g.key));
    if (fresh.length === 0) return;
    fresh.forEach((g) => fired.current.add(g.key));
    setAlerts((a) => [...a, ...fresh].slice(-3));
  }, [clock, otherGoals, replay]);

  const dismissAlert = useCallback((key) => setAlerts((a) => a.filter((x) => x.key !== key)), []);

  function skipToEnd() {
    otherGoals.forEach((g) => fired.current.add(g.key)); // pas de rafale d'alertes en sautant à la fin
    setAlerts([]);
    setClock(MATCH_END);
    setPlaying(false);
  }

  function restart() {
    fired.current = new Set();
    setAlerts([]);
    setClock(0);
    setPlaying(true);
  }

  function goToPlayer(club, playerName) {
    navigate(`/competition/${id}/clubs/${encodeURIComponent(club)}/players/${encodeURIComponent(playerName)}`);
  }

  if (error) {
    return (
      <div className="p-6 flex flex-col gap-3 items-start">
        <p className="text-sm text-gray-400">{error}</p>
        <button onClick={() => navigate(-1)} className="text-accent text-sm font-medium">
          ← Retour
        </button>
      </div>
    );
  }
  if (!data) return <div className="p-6 text-sm text-gray-400">Chargement…</div>;

  // Événements du fil et score à l'horloge courante (au coup de sifflet final : le score réel du match).
  const visibleEvents = (data.live ?? []).filter((e) => e.minute <= clock);
  const goalsNow = visibleEvents.filter((e) => e.kind === "goal");
  const score =
    clock >= MATCH_END
      ? { home: data.home_goals, away: data.away_goals }
      : { home: goalsNow.filter((e) => e.side === "home").length, away: goalsNow.filter((e) => e.side === "away").length };

  return (
    <div className="flex flex-col h-full p-2.5 gap-2 overflow-y-auto lg:overflow-hidden">
      <div className="shrink-0 flex items-center justify-between gap-2">
        <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-xs text-gray-400">
          <ArrowLeft size={14} /> Retour
        </button>
        <button onClick={() => setShowAnimation(true)} className="text-xs font-semibold text-accent">
          Voir l'animation
        </button>
      </div>

      {showAnimation && (
        <AnimationDialog
          competitionId={id}
          matchParams={{ home, away, journee, group, matchday, round_number: roundNumber, leg }}
          onClose={() => setShowAnimation(false)}
        />
      )}

      <MatchHeader data={data} contextLabel={contextLabel} score={score} minute={clock < MATCH_END ? Math.floor(clock) : null} />

      <MatchStatsPanel homeStats={data.home_stats} awayStats={data.away_stats} />

      {/* Quatre colonnes à partir de lg, de gauche à droite : banc domicile, STADE, banc extérieur, COMMENTAIRE EN DIRECT. Tout tient dans la
          fenêtre sans défiler : la hauteur disponible fixe celle du stade (portrait 68 x 105, largeur déduite), chaque colonne défile en interne
          si besoin. Le live est une colonne, jamais un calque : le terrain n'est JAMAIS masqué. En dessous de lg tout s'empile : stade, live, bancs. */}
      <div className="grid gap-2.5 grid-cols-1 lg:flex-1 lg:min-h-0 lg:grid-cols-[minmax(10rem,13rem)_auto_minmax(10rem,13rem)_minmax(0,1fr)] lg:grid-rows-[minmax(0,1fr)]">
        <div className="order-3 lg:order-1 min-h-0 lg:overflow-y-auto">
          <BenchPanel club={data.home} coach={data.home_coach} bench={data.home_bench} unavailable={data.home_unavailable} onPlayerClick={goToPlayer} />
        </div>

        <div className="order-1 lg:order-2 min-w-0 min-h-0 flex flex-col gap-1.5">
          <div className="shrink-0 flex items-center justify-between gap-2 px-1">
            <span className="text-[11px] font-extrabold uppercase tracking-wide text-live">
              Analyse tactique{replay ? " · temps réel" : ""}
            </span>
            <span className="text-[11px] font-semibold text-slate-300 tabular-nums whitespace-nowrap shrink-0">
              {data.home_formation} vs {data.away_formation}
            </span>
          </div>
          {/* Stade VERTICAL : domicile en haut, extérieur en bas. Hauteur = place restante (lg) ; largeur bornée en mode empilé. */}
          <div ref={pitchBox} className="lg:flex-1 lg:min-h-0 lg:overflow-hidden flex justify-center">
            <div
              className="relative w-full max-w-[24rem] lg:max-w-none"
              style={{ aspectRatio: "68 / 105", ...(pitchH ? { height: pitchH, width: (pitchH * 68) / 105 } : {}) }}
            >
              <PitchField />
              {data.home_players.map((p) => (
                <PlayerDot key={p.name} player={p} color="bg-accent" onClick={() => goToPlayer(data.home, p.name)} />
              ))}
              {data.away_players.map((p) => (
                <PlayerDot key={p.name} player={p} color="bg-gold text-bg" onClick={() => goToPlayer(data.away, p.name)} />
              ))}
            </div>
          </div>
        </div>

        <div className="order-4 lg:order-3 min-h-0 lg:overflow-y-auto">
          <BenchPanel club={data.away} coach={data.away_coach} bench={data.away_bench} unavailable={data.away_unavailable} onPlayerClick={goToPlayer} />
        </div>

        <div className="relative order-2 lg:order-4 h-[30rem] lg:h-auto min-w-0">
          <LivePanel
            events={visibleEvents}
            finished={clock >= MATCH_END}
            alerts={replay ? <GoalAlerts alerts={alerts} onDismiss={dismissAlert} /> : null}
            footer={replay ? <MultiplexTicker matches={others} clock={clock} /> : null}
            playback={
              replay
                ? { clock, playing, speed, onTogglePlay: () => setPlaying((p) => !p), onSpeed: setSpeed, onSkip: skipToEnd, onRestart: restart }
                : null
            }
          />
        </div>
      </div>
    </div>
  );
}

// Fenêtre modale de l'animation : un calque plein écran (le layout de la fiche, calé sur la hauteur de la fenêtre, n'est PAS modifié).
// L'iframe n'est montée que si MatchAnimation obtient un payload ; fermer la fenêtre démonte tout.
function AnimationDialog({ competitionId, matchParams, onClose }) {
  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div role="dialog" aria-modal="true" aria-label="Animation du match" className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-3">
      <div className="w-full max-w-5xl max-h-full overflow-y-auto rounded-xl bg-surface border border-white/10 p-3 flex flex-col gap-2">
        <div className="flex justify-end">
          <button onClick={onClose} className="text-xs text-gray-400">
            Fermer ✕
          </button>
        </div>
        <MatchAnimation key={JSON.stringify(matchParams)} competitionId={competitionId} matchParams={matchParams} />
      </div>
    </div>
  );
}

// En-tête agrandi et mis en valeur (retour terrain du 28/09/2026 : "doit
// être plus visuel, plus gros et bien mis en valeur") -- panneau bordé,
// écussons et score à l'échelle d'un vrai résumé de match plutôt qu'une
// simple ligne de texte.
function MatchHeader({ data, contextLabel, score, minute }) {
  return (
    <div className="shrink-0 rounded-xl bg-surface border border-white/10 px-4 py-1.5 flex items-center justify-center gap-4 sm:gap-8">
      <TeamSummary name={data.home} formation={data.home_formation} />

      <div className="flex flex-col items-center shrink-0 px-2">
        {contextLabel && <span className="text-[11px] text-gray-500 mb-0.5">{contextLabel}</span>}
        <span className="font-extrabold tabular-nums text-2xl sm:text-3xl text-white leading-none">
          {score.home} - {score.away}
        </span>
        {minute != null && <span className="live-blink mt-1 text-[11px] font-bold tabular-nums text-red-400">● {minute}'</span>}
      </div>

      <TeamSummary name={data.away} formation={data.away_formation} reverse />
    </div>
  );
}

// Volet stats (possession/tirs/tirs cadrés/xG, retour terrain du
// 29/09/2026) -- dérivées côté moteur du score et du lambda déjà décidés
// (voir ligue1sim.match_stats), jamais l'inverse. Absent (home_stats/
// away_stats == null) pour un club synthétique sans effectif réel -- le
// panneau est alors simplement omis plutôt que d'afficher des stats vides.
function MatchStatsPanel({ homeStats, awayStats }) {
  if (!homeStats || !awayStats) return null;

  return (
    <div className="shrink-0 rounded-xl bg-surface border border-white/10 px-4 py-1.5 flex items-center gap-4 sm:gap-6 flex-wrap">
      <div className="flex-1 min-w-[12rem] flex flex-col gap-0.5">
        <div className="flex items-center gap-2 text-[11px] tabular-nums">
          <span className="w-9 text-right font-semibold text-white">{homeStats.possession.toFixed(0)}%</span>
          <div className="flex-1 h-1.5 rounded-full bg-white/10 overflow-hidden flex">
            <div className="h-full bg-accent" style={{ width: `${homeStats.possession}%` }} />
            <div className="h-full bg-gold" style={{ width: `${awayStats.possession}%` }} />
          </div>
          <span className="w-9 text-left font-semibold text-white">{awayStats.possession.toFixed(0)}%</span>
        </div>
        <div className="text-center text-[9px] uppercase tracking-wide text-gray-500">Possession</div>
      </div>
      <StatCell label="Tirs" home={homeStats.shots} away={awayStats.shots} />
      <StatCell label="Tirs cadrés" home={homeStats.shots_on_target} away={awayStats.shots_on_target} />
      <StatCell label="xG" home={homeStats.xg.toFixed(2)} away={awayStats.xg.toFixed(2)} />
    </div>
  );
}

function StatCell({ label, home, away }) {
  return (
    <div className="flex flex-col items-center leading-tight tabular-nums">
      <span className="text-[13px] font-semibold text-white">
        {home} <span className="text-gray-600">—</span> {away}
      </span>
      <span className="text-[9px] uppercase tracking-wide text-gray-500">{label}</span>
    </div>
  );
}

function TeamSummary({ name, formation, reverse = false }) {
  return (
    <div className={`flex items-center gap-3 min-w-0 max-w-[38%] ${reverse ? "flex-row-reverse text-right" : ""}`}>
      <ClubLogo clubName={name} size={34} />
      <div className="min-w-0">
        <div className="font-bold text-base sm:text-lg text-white truncate">{name}</div>
        <div className="text-[11px] text-gray-500">{formation}</div>
      </div>
    </div>
  );
}

function PlayerDot({ player, color, onClick }) {
  const initials = player.name
    .split(" ")
    .map((p) => p[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <button
      onClick={onClick}
      className="absolute -translate-x-1/2 -translate-y-1/2 flex flex-col items-center gap-0.5 group"
      style={{ left: `${player.x}%`, top: `${player.y}%` }}
    >
      <div
        className={`h-7 w-7 rounded-full ${color} flex items-center justify-center text-[10px] font-bold shadow
                    ring-0 group-hover:ring-2 ring-white/70 transition-all`}
      >
        {initials}
      </div>
      <span className="text-[9px] text-white/80 text-center leading-tight w-max max-w-[140px] group-hover:text-white">
        {player.name}
      </span>
      {(player.goals > 0 || player.yellow_cards > 0 || player.red_card) && (
        <span className="text-[9px] leading-none">
          {"⚽".repeat(Math.min(player.goals, 3))}
          {player.yellow_cards > 0 && "🟨"}
          {player.red_card && "🟥"}
        </span>
      )}
    </button>
  );
}

const UNAVAILABLE_LABELS = { blessure: "Blessé", suspension: "Suspendu" };

// Remplaçants (effectif complet, pas seulement ceux entrés en jeu) +
// indisponibles (blessure/suspension) + entraîneur, de part et d'autre du
// terrain (retour terrain du 28/09/2026 : "mets la totalité des
// remplaçants... si des joueurs sont absents pour blessure ou carton rouge
// précise-le"). `coach` est `None` côté API si l'entraîneur du club n'est
// pas renseigné dans data/entraineurs.xlsx -- la ligne est alors omise
// plutôt que d'afficher un champ vide.
function BenchPanel({ club, coach, bench, unavailable, onPlayerClick, align = "left" }) {
  const players = bench ?? [];
  const absents = unavailable ?? [];
  const alignRight = align === "right";

  return (
    <div className="rounded-xl bg-surface border border-white/10 p-2.5 flex flex-col gap-3">
      <div className="flex items-center gap-2 min-w-0">
        <ClubLogo clubName={club} size={20} />
        <span className="text-[12px] font-extrabold uppercase tracking-wide text-live truncate">{club}</span>
      </div>
      {coach && (
        <div className={alignRight ? "text-right" : ""}>
          <div className="text-[10px] font-bold uppercase tracking-wide text-gray-500">Entraîneur</div>
          <div className="text-[13px] text-white/85 font-medium truncate">{coach}</div>
        </div>
      )}

      <div>
        <div className={`text-[10px] font-bold uppercase tracking-wide text-gray-500 mb-1 ${alignRight ? "text-right" : ""}`}>
          Remplaçants
        </div>
        <div className="flex flex-col gap-0.5">
          {players.map((p) => {
            const enteredGame = p.entered_minute != null;
            return (
              <button
                key={p.name}
                onClick={() => onPlayerClick(club, p.name)}
                className={`flex items-center gap-1.5 text-[11px] text-left rounded px-1.5 py-1 transition-colors ${
                  enteredGame ? "bg-accent/15 hover:bg-accent/25" : "hover:bg-white/5 hover:text-gold"
                } ${alignRight ? "flex-row-reverse text-right" : ""}`}
              >
                <span className="text-gray-500 w-7 shrink-0" style={{ textAlign: alignRight ? "right" : "left" }}>
                  {p.poste}
                </span>
                <span className={`flex-1 min-w-0 truncate ${enteredGame ? "text-white font-medium" : "text-gray-300"}`}>
                  {p.name}
                </span>
                {enteredGame && (
                  <span className="text-[10px] font-bold text-accent tabular-nums shrink-0">{p.entered_minute}'</span>
                )}
              </button>
            );
          })}
          {players.length === 0 && <p className="text-[11px] text-gray-600 italic">Aucun remplaçant.</p>}
        </div>
      </div>

      {absents.length > 0 && (
        <div>
          <div className={`text-[10px] font-bold uppercase tracking-wide text-gray-500 mb-1 ${alignRight ? "text-right" : ""}`}>
            Indisponibles
          </div>
          <div className="flex flex-col gap-0.5">
            {absents.map((p) => (
              <div
                key={p.name}
                className={`flex items-center gap-1.5 text-[11px] px-1.5 py-1 ${alignRight ? "flex-row-reverse text-right" : ""}`}
              >
                <span className="text-gray-600 w-7 shrink-0" style={{ textAlign: alignRight ? "right" : "left" }}>
                  {p.poste}
                </span>
                <span className="flex-1 min-w-0 truncate text-gray-500 line-through decoration-gray-600">{p.name}</span>
                <span
                  className={`text-[9px] font-semibold px-1.5 py-0.5 rounded-full shrink-0 ${
                    p.reason === "blessure" ? "bg-red-500/15 text-red-400" : "bg-amber-500/15 text-amber-400"
                  }`}
                >
                  {UNAVAILABLE_LABELS[p.reason]}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
