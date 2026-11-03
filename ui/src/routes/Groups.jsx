import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate, useOutletContext } from "react-router-dom";
import { LoaderCircle } from "lucide-react";
import { getGroups, simulateGroupsMatchday, startKnockout } from "../api/client";
import MatchRow from "../components/matches/MatchRow";
import StandingsTable from "../components/standings/StandingsTable";
import ActionBar from "../components/common/ActionBar";
import AnimationDialog from "../components/pitch/AnimationDialog";

export default function Groups() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { refresh } = useOutletContext();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [launching, setLaunching] = useState(false); // « Lancement du live… » : simulation de la journée avant le premier live
  const [error, setError] = useState(null);
  // Fenêtre « Voir l'animation » (bouton Animation ou LIVE), sans jamais révéler le score avant (US-15/16,
  // docs/PRD_PRODUIT.md) -- { match, group, matchday } ou null.
  const [animationMatch, setAnimationMatch] = useState(null);
  // Phase de ligue : onglet affiché sous lg (« standings » | « matches ») et liste de droite (« results » | « upcoming »,
  // null = au mieux : résultats s'il y en a, sinon matchs à venir).
  const [tab, setTab] = useState("standings");
  const [view, setView] = useState(null);

  const load = useCallback(() => {
    getGroups(id)
      .then(setData)
      .catch(() => setError("Compétition introuvable."));
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleSimulate() {
    setLoading(true);
    try {
      setData(await simulateGroupsMatchday(id));
      setView(null);
      refresh();
    } finally {
      setLoading(false);
    }
  }

  async function handleStartKnockout() {
    setLoading(true);
    try {
      await startKnockout(id);
      refresh();
      navigate(`/competition/${id}/bracket`);
    } finally {
      setLoading(false);
    }
  }

  // Live d'un match de poule / de phase de ligue, quelle que soit la compétition (Coupe du Monde, Ligue des Champions, perso) --
  // ouvre directement l'ANIMATION. Match déjà joué : animation immédiate, sans jamais afficher le score au préalable. Pas encore joué :
  // on simule la journée (toutes les poules d'un bloc : le moteur n'a qu'un compteur de journée), puis l'animation de CE match s'ouvre
  // automatiquement -- aucune étape intermédiaire ne révèle quoi que ce soit sur ce match avant que l'animation ne commence.
  async function openLive(group, match, played) {
    let matchday = data.groups_matchday - 1;
    if (!played) {
      setLaunching(true);
      try {
        const next = await simulateGroupsMatchday(id);
        setData(next);
        setView(null);
        matchday = next.groups_matchday - 1;
        refresh();
      } catch {
        setLaunching(false);
        return;
      }
      setLaunching(false);
    }
    setAnimationMatch({ match, group: group.name, matchday });
  }

  if (error) return <div className="p-6 text-sm text-gray-400">{error}</div>;
  if (!data) return <div className="p-6 text-sm text-gray-400">Chargement…</div>;

  const leaguePhase = data.league_phase;
  const matchday = data.groups_matchday - 1; // journée (0-indexée) des résultats affichés ; seule celle-ci est détaillée par l'API
  const hasResults = data.groups.some((g) => g.current_matches.length > 0);
  const hasUpcoming = data.groups.some((g) => (g.next_matches?.length ?? 0) > 0);
  const showing = view ?? (hasResults ? "results" : "upcoming");

  // Zone de qualification : poules classiques = 2 premiers ; phase de ligue de la Ligue des Champions = 8 premiers directs en 8es
  // (vert), 9e-24e en barrages (sans couleur, nommés par la légende), derniers éliminés (rouge).
  const zoneOf = (i) => {
    if (!leaguePhase) return i < 2 ? "direct" : null;
    if (i < data.direct_spots) return "direct";
    if (i >= data.direct_spots + data.playoff_spots) return "out";
    return null;
  };

  function openSheet(g, m) {
    navigate(`/competition/${id}/pitch?${new URLSearchParams({ home: m.home, away: m.away, group: g.name, matchday })}`);
  }

  const row = (g, m) => (
    <MatchRow
      key={`${m.home}-${m.away}`}
      match={m}
      onOpenSheet={m.played ? () => openSheet(g, m) : undefined}
      onLive={() => openLive(g, m, m.played)}
      onAnimation={() => setAnimationMatch({ match: m, group: g.name, matchday })}
    />
  );

  const primary = data.groups_complete
    ? data.knockout_started
      ? { label: "Voir la phase finale →", onClick: () => navigate(`/competition/${id}/bracket`) }
      : { label: leaguePhase ? "Lancer les barrages →" : "Lancer les phases finales →", onClick: handleStartKnockout, loading }
    : { label: leaguePhase ? `Simuler la journée ${data.groups_matchday + 1}` : "Simuler la journée des poules", onClick: handleSimulate, loading };

  return (
    <div className="flex flex-col h-full">
      {leaguePhase ? (
        <LeaguePhase
          data={data}
          zoneOf={zoneOf}
          tab={tab}
          setTab={setTab}
          showing={showing}
          setView={setView}
          hasResults={hasResults}
          hasUpcoming={hasUpcoming}
          row={row}
        />
      ) : (
        // items-start : chaque carte garde sa hauteur naturelle (en J0, des cartes vides ne s'étirent pas à la hauteur de leurs voisines).
        <div className="flex-1 min-h-0 overflow-y-auto p-3 grid gap-3 items-start grid-cols-1 md:grid-cols-2 xl:grid-cols-3">
          {data.groups.map((g) => (
            <GroupCard key={g.name} group={g} data={data} zoneOf={zoneOf} row={row} />
          ))}
        </div>
      )}

      <ActionBar primary={primary} />

      {launching && (
        <div role="status" className="fixed inset-0 z-50 flex flex-col items-center justify-center gap-3 bg-bg">
          <LoaderCircle size={36} className="animate-spin text-live" />
          <span className="text-sm font-semibold text-gray-100">Lancement du live...</span>
        </div>
      )}

      {animationMatch && (
        <AnimationDialog
          competitionId={id}
          matchParams={{
            home: animationMatch.match.home,
            away: animationMatch.match.away,
            group: animationMatch.group,
            matchday: animationMatch.matchday,
          }}
          onClose={() => setAnimationMatch(null)}
        />
      )}
    </div>
  );
}

// Phase de ligue (36 clubs) : UN seul classement à gauche, les matchs de la journée à droite -- sur bureau (lg) les deux sont visibles
// d'un coup et la page ne défile pas (le classement défile dans son bloc seulement si la fenêtre est trop basse) ; en dessous, une
// bascule Classement · Matchs.
function LeaguePhase({ data, zoneOf, tab, setTab, showing, setView, hasResults, hasUpcoming, row }) {
  const g = data.groups[0];
  const results = showing === "results";
  const matches = (results ? g.current_matches : (g.next_matches ?? [])).map((m) => row(g, m));
  const journee = results ? data.groups_matchday : data.groups_matchday + 1;

  return (
    <>
      <div className="lg:hidden shrink-0 px-3 pt-3">
        <div className="grid grid-cols-2 rounded-lg bg-surface border border-line p-1" role="group" aria-label="Affichage">
          {[
            ["standings", "Classement"],
            ["matches", "Matchs"],
          ].map(([key, label]) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              aria-pressed={tab === key}
              className={`min-h-11 rounded-lg text-sm font-medium ${tab === key ? "bg-surface-3 text-white" : "text-gray-400"}`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 min-h-0 flex flex-col lg:flex-row gap-3 px-3 py-2">
        <section
          className={`${tab === "standings" ? "flex" : "hidden"} lg:flex flex-col min-h-0 lg:w-[28rem] lg:shrink-0 flex-1 lg:flex-none rounded-xl bg-surface border border-line overflow-hidden`}
        >
          <div className="shrink-0 min-h-7 px-3 py-1 flex flex-wrap items-center gap-x-4 gap-y-0.5 text-caption text-gray-400 lg:flex-nowrap lg:overflow-hidden lg:whitespace-nowrap">
            <Legend color="bg-win" label={`1er–${data.direct_spots}e : 8es de finale`} />
            <Legend color="bg-gray-500" label={`${data.direct_spots + 1}e–${data.direct_spots + data.playoff_spots}e : barrages`} />
            <Legend color="bg-loss" label={`${data.direct_spots + data.playoff_spots + 1}e et + : éliminés`} />
          </div>
          <div className="flex-1 min-h-0 overflow-y-auto">
            <StandingsTable rows={g.standings} dense zoneOf={zoneOf} />
          </div>
        </section>

        <section
          className={`${tab === "matches" ? "flex" : "hidden"} lg:flex flex-col min-h-0 min-w-0 flex-1 rounded-xl bg-surface border border-line overflow-hidden`}
        >
          <div className="shrink-0 min-h-7 lg:h-7 px-3 flex items-center justify-between gap-3 text-caption text-gray-400 border-b border-line">
            <span className="font-semibold">
              Journée {journee} · {results ? "Résultats" : "À venir"}
            </span>
            {hasResults && hasUpcoming && (
              <span className="flex items-center gap-3">
                <ViewButton active={results} onClick={() => setView("results")} label="Résultats" />
                <ViewButton active={!results} onClick={() => setView("upcoming")} label="À venir" />
              </span>
            )}
          </div>
          <div className="flex-1 min-h-0 overflow-y-auto">
            {matches.length > 0 ? matches : <p className="p-3 text-sm text-gray-500">Aucun match pour l'instant.</p>}
          </div>
        </section>
      </div>
    </>
  );
}

function ViewButton({ active, onClick, label }) {
  return (
    <button onClick={onClick} aria-pressed={active} className={`min-h-11 lg:min-h-6 ${active ? "text-white font-semibold" : "text-gray-400 hover:text-gray-200"}`}>
      {label}
    </button>
  );
}

function Legend({ color, label }) {
  return (
    <span className="flex items-center gap-1.5">
      <span className={`h-2 w-2 rounded-full ${color}`} aria-hidden="true" />
      {label}
    </span>
  );
}

// Poule classique (Coupe du Monde, perso) : classement puis résultats de la dernière journée jouée et matchs de la suivante.
function GroupCard({ group: g, data, zoneOf, row }) {
  const upcoming = g.next_matches ?? [];
  return (
    <section className="rounded-xl bg-surface border border-line overflow-hidden">
      <h2 className="px-3 pt-3 pb-1 flex items-center justify-between text-sm font-semibold text-gray-300">
        {g.name}
        {g.is_complete && <span className="text-caption font-normal text-win">Terminée</span>}
      </h2>
      <StandingsTable rows={g.standings} zoneOf={zoneOf} />
      {g.current_matches.length > 0 && (
        <>
          <h3 className="px-3 pt-2 pb-1 text-caption text-gray-500 border-t border-line">Journée {data.groups_matchday} · Résultats</h3>
          {g.current_matches.map((m) => row(g, m))}
        </>
      )}
      {upcoming.length > 0 ? (
        <>
          <h3 className="px-3 pt-2 pb-1 text-caption text-gray-500 border-t border-line">Journée {data.groups_matchday + 1} · À venir</h3>
          {upcoming.map((m) => row(g, m))}
        </>
      ) : (
        g.current_matches.length === 0 && <p className="px-3 py-2 text-caption text-gray-500 border-t border-line">Aucun match joué – Journée 1 à venir</p>
      )}
    </section>
  );
}
