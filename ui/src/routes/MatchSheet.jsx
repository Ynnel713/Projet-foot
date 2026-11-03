import { useEffect, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { ArrowLeftRight, ChevronLeft } from "lucide-react";
import { getPitchView } from "../api/client";
import ClubLogo from "../components/common/ClubLogo";
import PitchField from "../components/pitch/PitchField";
import { matchOriginTab } from "../utils/matchOrigin";

// Feuille de match V1 (refonte UI, lot 4) : destination du clic sur un match joué, dans l'espace
// de la compétition. Statique, construite avec les seules données de `GET /pitch` ; le live textuel
// et l'animation restent dans PitchView (désactivés en V1). Mobile : une colonne, compositions en
// liste avec bascule Domicile / Extérieur. Bureau (lg) : liste domicile · terrain · liste extérieur.

// Faits du match : les événements réels du fil `live`, sans les événements narratifs ni le texte.
const FACT_KINDS = new Set(["goal", "penalty_missed", "yellow", "second_yellow", "red", "sub"]);
const LINES = [
  { label: "Gardien", postes: ["GK"] },
  { label: "Défense", postes: ["DC", "RB", "LB"] },
  { label: "Milieu", postes: ["MDC", "MC", "MOC"] },
  { label: "Attaque", postes: ["AG", "AD", "BU", "SA", "ATT"] },
];
const UNAVAILABLE_LABELS = { blessure: "Blessé", suspension: "Suspendu" };

function lineOf(poste) {
  const first = (poste ?? "").split("/")[0].trim();
  return LINES.find((l) => l.postes.includes(first))?.label ?? "Milieu";
}

export default function MatchSheet() {
  const { id } = useParams();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null); // { key, sheet }
  const [error, setError] = useState(null); // { key, message }
  const [side, setSide] = useState("home"); // composition affichée sur mobile

  const home = params.get("home");
  const away = params.get("away");
  const journee = params.get("journee");
  const group = params.get("group");
  const matchday = params.get("matchday");
  const roundNumber = params.get("round_number");
  const leg = params.get("leg");
  const key = params.toString();
  const origin = `/competition/${id}/${matchOriginTab(params)}`;

  let contextLabel = "";
  if (journee) contextLabel = `Journée ${journee}`;
  else if (group) contextLabel = `${group} · Journée ${Number(matchday) + 1}`;
  // `leg` 0 vaut aussi pour un match sec (finale, élimination simple) : seul le retour est nommé.
  else if (roundNumber) contextLabel = `Tour ${roundNumber}${leg === "1" ? " · Retour" : ""}`;

  useEffect(() => {
    let alive = true;
    getPitchView(id, { home, away, journee, group, matchday, round_number: roundNumber, leg })
      .then((sheet) => alive && setData({ key, sheet }))
      .catch((err) => {
        if (!alive) return;
        const message =
          err.status === 404
            ? "Match introuvable."
            : err.status === 409
              ? "Feuille de match indisponible : match pas encore joué ou sans effectif réel."
              : "Feuille de match indisponible.";
        setError({ key, message });
      });
    return () => {
      alive = false;
    };
  }, [id, home, away, journee, group, matchday, roundNumber, leg, key]);

  const backLink = (
    <Link to={origin} className="inline-flex items-center gap-1 min-h-11 text-sm font-medium text-link">
      <ChevronLeft size={16} /> {contextLabel || "Retour à la compétition"}
    </Link>
  );

  if (data?.key !== key) {
    if (error?.key !== key) return <div className="p-4 text-sm text-gray-400">Chargement…</div>;
    return (
      <div className="p-4 flex flex-col gap-2 items-start text-sm text-gray-400">
        <p>{error.message}</p>
        {backLink}
      </div>
    );
  }

  const sheet = data.sheet;
  const facts = (sheet.live ?? []).filter((e) => FACT_KINDS.has(e.kind));
  const goPlayer = (club, name) =>
    navigate(`/competition/${id}/clubs/${encodeURIComponent(club)}/players/${encodeURIComponent(name)}`);

  return (
    <div className="mx-auto w-full max-w-[1280px] px-4 py-3 flex flex-col gap-4">
      {backLink}

      <header className="rounded-xl bg-surface border border-line px-4 py-4 grid grid-cols-[1fr_auto_1fr] items-center gap-3">
        <h1 className="sr-only">
          {sheet.home} {sheet.home_goals} - {sheet.away_goals} {sheet.away}
        </h1>
        <TeamHead name={sheet.home} formation={sheet.home_formation} />
        <div className="font-display font-bold text-5xl leading-none text-white px-2">
          {sheet.home_goals} - {sheet.away_goals}
        </div>
        <TeamHead name={sheet.away} formation={sheet.away_formation} reverse />
      </header>

      <div className="grid gap-4 lg:grid-cols-2">
        <Facts facts={facts} sheet={sheet} onPlayer={goPlayer} />
        <Stats home={sheet.home_stats} away={sheet.away_stats} />
      </div>

      <section className="flex flex-col gap-3">
        <div className="lg:hidden grid grid-cols-2 rounded-lg bg-surface border border-line p-1" role="group" aria-label="Composition affichée">
          {[
            ["home", sheet.home],
            ["away", sheet.away],
          ].map(([s, club]) => (
            <button
              key={s}
              onClick={() => setSide(s)}
              aria-pressed={side === s}
              className={`min-h-11 rounded-lg text-sm font-medium truncate px-2 ${side === s ? "bg-surface-3 text-white" : "text-gray-400"}`}
            >
              {club}
            </button>
          ))}
        </div>

        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_20rem_minmax(0,1fr)] xl:grid-cols-[minmax(0,1fr)_24rem_minmax(0,1fr)] lg:items-start">
          <div className={side === "home" ? "" : "hidden lg:block"}>
            <Lineup
              club={sheet.home}
              coach={sheet.home_coach}
              starters={sheet.home_players}
              bench={sheet.home_bench}
              unavailable={sheet.home_unavailable}
              onPlayer={goPlayer}
            />
          </div>
          <div className="hidden lg:block">
            <Pitch sheet={sheet} onPlayer={goPlayer} />
          </div>
          <div className={side === "away" ? "" : "hidden lg:block"}>
            <Lineup
              club={sheet.away}
              coach={sheet.away_coach}
              starters={sheet.away_players}
              bench={sheet.away_bench}
              unavailable={sheet.away_unavailable}
              onPlayer={goPlayer}
            />
          </div>
        </div>
      </section>
    </div>
  );
}

function TeamHead({ name, formation, reverse = false }) {
  return (
    <div className={`min-w-0 flex items-center gap-3 ${reverse ? "flex-row-reverse text-right" : ""}`}>
      <ClubLogo clubName={name} size={40} />
      <div className="min-w-0">
        <div className="font-display font-semibold text-lg sm:text-2xl leading-tight text-white truncate">{name}</div>
        <div className="text-caption text-gray-500">{formation}</div>
      </div>
    </div>
  );
}

function Panel({ title, children }) {
  return (
    <section className="rounded-xl bg-surface border border-line">
      <h2 className="px-4 pt-3 pb-2 text-caption font-semibold uppercase tracking-wide text-gray-500">{title}</h2>
      {children}
    </section>
  );
}

// Marque d'un fait : ballon pour un but, carton coloré, flèches pour un remplacement.
function FactMark({ kind }) {
  if (kind === "goal") return <span role="img" aria-label="But">⚽</span>;
  if (kind === "penalty_missed") return <span className="text-loss font-semibold">Pen. manqué</span>;
  if (kind === "sub") return <ArrowLeftRight size={14} className="text-ev-sub" aria-label="Remplacement" />;
  const color = kind === "yellow" ? "bg-ev-yellow" : "bg-ev-red";
  const label = { yellow: "Carton jaune", second_yellow: "Deuxième jaune", red: "Carton rouge" }[kind];
  return <span role="img" className={`inline-block w-2.5 h-3.5 shrink-0 ${color}`} aria-label={label} />;
}

// Rôle des noms d'un fait. Le texte du fil (générateur NLG) ne les cite pas dans un ordre fixe, on les
// déduit donc des compositions : l'entrant est le remplaçant entré à cette minute ; le buteur est
// forcément un titulaire crédité d'un but ou un remplaçant entré avant la minute -- s'il est le SEUL
// des deux noms dans ce cas, le rôle est sûr. Sinon (passeur qui a marqué ailleurs ou entré en jeu),
// noms affichés sans rôle plutôt qu'un « passe » faux.
// ponytail: un champ structuré (buteur/passeur, entrant/sortant) dans LiveEventOut supprimerait ce repli.
function factPlayers(event, sheet) {
  const names = [...new Set(event.parts.filter((p) => p.player).map((p) => p.text))];
  if (names.length < 2) return { names, roles: true };
  const bench = [...sheet.home_bench, ...sheet.away_bench];
  let first = null;
  if (event.kind === "sub") {
    first = names.find((n) => bench.some((p) => p.name === n && p.entered_minute === event.minute));
  } else if (event.kind === "goal") {
    const starters = [...sheet.home_players, ...sheet.away_players];
    const canScore = (n) =>
      starters.some((p) => p.name === n && p.goals > 0) ||
      bench.some((p) => p.name === n && p.entered_minute != null && p.entered_minute <= event.minute);
    const scorers = names.filter(canScore);
    if (scorers.length === 1) first = scorers[0];
  }
  if (!first) return { names, roles: false };
  return { names: [first, ...names.filter((n) => n !== first)], roles: true };
}

// Nom cliquable d'un fait → fiche du joueur (tous les joueurs d'un fait sont du club de l'événement).
function FactName({ name, club, onPlayer, muted = false }) {
  return (
    <button
      onClick={() => onPlayer(club, name)}
      className={`hover:underline underline-offset-2 ${muted ? "text-gray-400" : "text-gray-100 font-medium"}`}
    >
      {name}
    </button>
  );
}

function FactText({ event, sheet, onPlayer }) {
  const { names, roles } = factPlayers(event, sheet);
  const link = (name, muted) => <FactName key={name} name={name} club={event.club} onPlayer={onPlayer} muted={muted} />;
  if (!roles) {
    return <span className="min-w-0">{names.flatMap((n, i) => (i ? [", ", link(n)] : [link(n)]))}</span>;
  }
  const [main, second] = names;
  return (
    <span className="min-w-0">
      {link(main)}
      {second && (
        <span className="text-gray-500">
          {event.kind === "sub" ? " pour " : " · passe "}
          {link(second, true)}
        </span>
      )}
    </span>
  );
}

function Facts({ facts, sheet, onPlayer }) {
  return (
    <Panel title="Faits du match">
      {facts.length === 0 ? (
        <p className="px-4 pb-3 text-sm text-gray-500">Aucun fait marquant.</p>
      ) : (
        <ol className="pb-1">
          {facts.map((e, i) => {
            const content = (
              <span className={`flex items-center gap-2 min-w-0 ${e.side === "home" ? "flex-row-reverse text-right" : ""}`}>
                <FactMark kind={e.kind} />
                <FactText event={e} sheet={sheet} onPlayer={onPlayer} />
              </span>
            );
            return (
              <li
                key={`${e.minute}-${e.kind}-${i}`}
                className="grid grid-cols-[minmax(0,1fr)_3rem_minmax(0,1fr)] items-center min-h-11 lg:min-h-9 px-4 border-t border-line text-data"
              >
                <span className="flex justify-end min-w-0">{e.side === "home" && content}</span>
                <span className="text-center text-gray-400 font-semibold">{e.minute}'</span>
                <span className="flex justify-start min-w-0">{e.side === "away" && content}</span>
              </li>
            );
          })}
        </ol>
      )}
    </Panel>
  );
}

function Stats({ home, away }) {
  if (!home || !away) return null;
  const rows = [
    ["Tirs", home.shots, away.shots],
    ["Tirs cadrés", home.shots_on_target, away.shots_on_target],
    ["xG", home.xg.toFixed(2), away.xg.toFixed(2)],
  ];
  return (
    <Panel title="Statistiques">
      <div className="px-4 pb-3 flex flex-col gap-1">
        <div className="flex items-center justify-between text-data font-semibold text-white">
          <span>{home.possession.toFixed(0)} %</span>
          <span className="text-caption font-normal text-gray-500">Possession</span>
          <span>{away.possession.toFixed(0)} %</span>
        </div>
        <div className="h-1.5 rounded-full bg-surface-3 overflow-hidden flex">
          <div className="h-full bg-accent" style={{ width: `${home.possession}%` }} />
          <div className="h-full bg-gray-300" style={{ width: `${away.possession}%` }} />
        </div>
      </div>
      {rows.map(([label, h, a]) => (
        <div key={label} className="flex items-center justify-between min-h-9 px-4 border-t border-line text-data">
          <span className="font-semibold text-white">{h}</span>
          <span className="text-caption text-gray-500">{label}</span>
          <span className="font-semibold text-white">{a}</span>
        </div>
      ))}
    </Panel>
  );
}

function PlayerMarks({ player }) {
  if (!player.goals && !player.yellow_cards && !player.red_card) return null;
  return (
    <span className="flex items-center gap-1 shrink-0">
      {player.goals > 0 && <span role="img" aria-label={`${player.goals} but(s)`}>{"⚽".repeat(Math.min(player.goals, 3))}</span>}
      {player.yellow_cards > 0 && <FactMark kind="yellow" />}
      {player.red_card && <FactMark kind="red" />}
    </span>
  );
}

function PlayerRow({ poste, name, muted, onClick, children }) {
  return (
    <button
      onClick={onClick}
      className="w-full flex items-center gap-2 min-h-11 lg:min-h-8 px-4 border-t border-line text-left text-data hover:bg-surface-2 transition-colors"
    >
      <span className="w-9 shrink-0 text-caption text-gray-500">{poste}</span>
      <span className={`flex-1 min-w-0 truncate ${muted ? "text-gray-400" : "text-gray-100"}`}>{name}</span>
      {children}
    </button>
  );
}

function Rating({ value }) {
  if (value == null) return null;
  return <span className="w-8 shrink-0 text-right font-semibold text-gray-100">{value.toFixed(1)}</span>;
}

function Lineup({ club, coach, starters, bench, unavailable, onPlayer }) {
  const lines = LINES.map((l) => ({ label: l.label, players: starters.filter((p) => lineOf(p.poste) === l.label) })).filter(
    (l) => l.players.length > 0,
  );
  return (
    <Panel title={club}>
      {coach && <p className="px-4 pb-2 -mt-1 text-caption text-gray-400">Entraîneur : {coach}</p>}
      {lines.map((l) => (
        <div key={l.label}>
          <div className="px-4 pt-2 pb-1 text-caption text-gray-500 border-t border-line">{l.label}</div>
          {l.players.map((p) => (
            <PlayerRow key={p.name} poste={p.poste} name={p.name} onClick={() => onPlayer(club, p.name)}>
              <PlayerMarks player={p} />
              <Rating value={p.rating} />
            </PlayerRow>
          ))}
        </div>
      ))}

      <div className="px-4 pt-3 pb-1 text-caption font-semibold uppercase tracking-wide text-gray-500 border-t border-line">Remplaçants</div>
      {bench.length === 0 && <p className="px-4 pb-2 text-sm text-gray-500">Aucun remplaçant.</p>}
      {bench.map((p) => (
        <PlayerRow key={p.name} poste={p.poste} name={p.name} muted={p.entered_minute == null} onClick={() => onPlayer(club, p.name)}>
          {p.entered_minute != null && (
            <span className="flex items-center gap-1 shrink-0 text-caption text-gray-400">
              <ArrowLeftRight size={12} className="text-ev-sub" /> {p.entered_minute}'
            </span>
          )}
          <Rating value={p.rating} />
        </PlayerRow>
      ))}

      {unavailable.length > 0 && (
        <>
          <div className="px-4 pt-3 pb-1 text-caption font-semibold uppercase tracking-wide text-gray-500 border-t border-line">
            Indisponibles
          </div>
          {unavailable.map((p) => (
            <div key={p.name} className="flex items-center gap-2 min-h-9 px-4 border-t border-line text-data">
              <span className="w-9 shrink-0 text-caption text-gray-500">{p.poste}</span>
              <span className="flex-1 min-w-0 truncate text-gray-500 line-through">{p.name}</span>
              <span className={`text-caption shrink-0 ${p.reason === "blessure" ? "text-loss" : "text-draw"}`}>
                {UNAVAILABLE_LABELS[p.reason]}
              </span>
            </div>
          ))}
        </>
      )}
      <div className="h-2" />
    </Panel>
  );
}

const CENTRAL_MIDS = new Set(["MC", "MOC"]);
const HOLDING_DROP = 5; // % de hauteur de terrain : la sentinelle recule d'environ une demi-ligne

// Milieu à 3 et plus (1 MDC + 2 MC/MOC ou plus sur la même ligne, cas d'un dispositif à bandes) : le moteur
// les aligne, la sentinelle sur un côté. À l'affichage seulement, elle passe au centre, un peu plus bas
// (vers son propre but), et les autres se répartissent symétriquement sur la même largeur.
// ponytail: correction d'affichage ; pitch_layout.place_starting_xi n'est pas modifié car il nourrit aussi
// les positions de départ de l'animation (rendu à mesurer avant tout changement).
function withHoldingMid(players, home) {
  const lines = new Map();
  players.forEach((p) => lines.set(p.y, [...(lines.get(p.y) ?? []), p]));
  const moved = new Map();
  for (const line of lines.values()) {
    const holding = line.filter((p) => p.poste === "MDC");
    const others = line.filter((p) => p.poste !== "MDC");
    if (holding.length !== 1 || others.length < 2 || !others.every((p) => CENTRAL_MIDS.has(p.poste))) continue;
    const xs = line.map((p) => p.x);
    const lo = Math.min(...xs);
    const hi = Math.max(...xs);
    moved.set(holding[0].name, { x: 50, y: holding[0].y + (home ? -HOLDING_DROP : HOLDING_DROP) });
    [...others]
      .sort((a, b) => a.x - b.x)
      .forEach((p, i) => moved.set(p.name, { x: lo + (i * (hi - lo)) / (others.length - 1), y: p.y }));
  }
  return players.map((p) => ({ ...p, ...moved.get(p.name) }));
}

// Terrain vertical (bureau seulement) : placement du moteur (pitch_layout.place_starting_xi), domicile en haut,
// extérieur en bas, x latéral et y profondeur en %, donc sans permutation (voir PitchView).
function Pitch({ sheet, onPlayer }) {
  return (
    <div className="relative w-full" style={{ aspectRatio: "68 / 105" }}>
      <PitchField />
      {withHoldingMid(sheet.home_players, true).map((p) => (
        <PitchDot key={`h-${p.name}`} player={p} tone="bg-accent text-white" onClick={() => onPlayer(sheet.home, p.name)} />
      ))}
      {withHoldingMid(sheet.away_players, false).map((p) => (
        <PitchDot key={`a-${p.name}`} player={p} tone="bg-gray-100 text-bg" onClick={() => onPlayer(sheet.away, p.name)} />
      ))}
    </div>
  );
}

function PitchDot({ player, tone, onClick }) {
  const surname = player.name.split(" ").slice(-1)[0];
  return (
    <button
      onClick={onClick}
      title={player.name}
      className="absolute -translate-x-1/2 -translate-y-1/2 flex flex-col items-center gap-0.5 group"
      style={{ left: `${player.x}%`, top: `${player.y}%` }}
    >
      <span className={`h-4 w-4 rounded-full ${tone} ring-0 group-hover:ring-2 ring-white/70`} />
      <span className="text-caption leading-none text-white max-w-[5.5rem] truncate">{surname}</span>
    </button>
  );
}
