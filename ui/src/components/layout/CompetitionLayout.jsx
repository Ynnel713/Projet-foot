import { useCallback, useEffect, useState } from "react";
import { Link, Navigate, Outlet, useLocation, useOutletContext, useParams } from "react-router-dom";
import { BarChart3, CalendarDays, GitFork, LayoutGrid, ListOrdered, Trophy } from "lucide-react";
import { getCompetition, getGroups } from "../../api/client";
import { useGameStore } from "../../store/useGameStore";
import { matchOriginTab } from "../../utils/matchOrigin";

// Espace d'une compétition (refonte UI, lot 2) : onglets toujours visibles --
// barre en bas sur mobile, colonne à gauche à partir de `md` -- autour de
// toutes les pages de la compétition (journée, classement, stats, poules,
// phase finale, club, joueur). Les onglets dépendent du format pour n'exposer
// que des écrans qui existent ; l'onglet Clubs arrive avec l'écran club (lot 5).
// Une compétition perso n'a pas de nom côté API (`championnat` à null).
const DEFAULT_NAME = "Compétition perso";
const FORMAT_LABELS = { LEAGUE: "Championnat", HYBRID: "Poules + élimination", KNOCKOUT: "Élimination directe" };

function tabsFor(status, groups) {
  const stats = { to: "leaderboards", label: "Stats", icon: BarChart3 };
  if (status.format === "LEAGUE") {
    return [
      { to: "simulate", label: "Journée", icon: CalendarDays },
      { to: "standings", label: "Classement", icon: ListOrdered },
      stats,
    ];
  }
  if (status.format === "HYBRID") {
    return [
      { to: "groups", label: groups?.league_phase ? "Phase de ligue" : "Poules", icon: LayoutGrid },
      { to: "bracket", label: "Phase finale", icon: GitFork, disabled: !groups?.knockout_started },
      stats,
    ];
  }
  return [{ to: "bracket", label: "Tableau", icon: Trophy }, stats];
}

export default function CompetitionLayout() {
  const { id } = useParams();
  const { pathname, search } = useLocation();
  const setActiveCompetition = useGameStore((s) => s.setActiveCompetition);
  // Résultats étiquetés par `id` : ceux d'une autre compétition ne s'affichent
  // jamais, et une erreur passagère pendant un rechargement ne masque pas les
  // données déjà chargées (l'erreur ne s'affiche que s'il n'y a rien d'autre).
  const [data, setData] = useState(null); // { id, status, groups }
  const [error, setError] = useState(null); // { id, message }
  // Rechargement demandé par une page après une simulation (lot 3) : « Champion » et « Phase finale » se mettent à jour
  // tout de suite, sans attendre le prochain changement d'onglet.
  const [reloads, setReloads] = useState(0);
  const refresh = useCallback(() => setReloads((n) => n + 1), []);

  // Rechargé à chaque changement de page : « Phase finale » doit s'activer
  // juste après « Lancer les barrages » (Groups navigue alors vers /bracket).
  useEffect(() => {
    let alive = true;
    getCompetition(id)
      .then(async (status) => {
        const groups = status.format === "HYBRID" ? await getGroups(id) : null;
        if (!alive) return;
        setData({ id, status, groups });
        setActiveCompetition(id, status.championnat ?? DEFAULT_NAME);
      })
      .catch((err) => {
        if (!alive) return;
        const gone = err.status === 404;
        // Compétition disparue (API redémarrée) : on l'oublie aussi pour l'en-tête et « Reprendre ».
        if (gone && useGameStore.getState().activeCompetitionId === id) useGameStore.getState().clearActiveCompetition();
        setError({ id, message: gone ? "Cette compétition n'existe plus." : "Compétition indisponible." });
      });
    return () => {
      alive = false;
    };
  }, [id, pathname, reloads, setActiveCompetition]);

  if (data?.id !== id) {
    if (error?.id !== id) return <div className="p-6 text-sm text-gray-400">Chargement…</div>;
    return (
      <div className="p-6 flex flex-col gap-3 items-start text-sm text-gray-400">
        <p>{error.message}</p>
        <Link to="/" className="text-link font-medium">
          Retour à l'accueil
        </Link>
      </div>
    );
  }

  const { status, groups } = data;
  const tabs = tabsFor(status, groups);
  const base = `/competition/${id}`;
  // Feuille de match (lot 4) : l'onglet d'où vient le match reste actif.
  const current = pathname === `${base}/pitch` ? `${base}/${matchOriginTab(new URLSearchParams(search))}` : pathname;
  const isActive = (to) => current.startsWith(`${base}/${to}`);

  return (
    <div className="h-full flex flex-col md:flex-row">
      <nav className="hidden md:flex w-56 shrink-0 flex-col gap-1 border-r border-line bg-surface/60 p-3">
        <div className="px-2 pb-3 mb-1 border-b border-line">
          <div className="font-display text-2xl font-bold text-white leading-tight">{status.championnat ?? DEFAULT_NAME}</div>
          <div className="text-caption text-gray-500 mt-0.5">{FORMAT_LABELS[status.format] ?? status.format}</div>
          {status.champion && <div className="text-caption text-gold mt-1.5">Champion : {status.champion}</div>}
        </div>
        {tabs.map((tab) => (
          <TabLink key={tab.to} tab={tab} href={`${base}/${tab.to}`} active={isActive(tab.to)} layout="side" />
        ))}
      </nav>

      <div className="flex-1 min-w-0 min-h-0 flex flex-col">
        <div className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden">
          <Outlet context={{ ...data, refresh }} />
        </div>
        <nav
          className="md:hidden shrink-0 flex border-t border-line bg-surface"
          style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
        >
          {tabs.map((tab) => (
            <TabLink key={tab.to} tab={tab} href={`${base}/${tab.to}`} active={isActive(tab.to)} layout="bottom" />
          ))}
        </nav>
      </div>
    </div>
  );
}

function TabLink({ tab, href, active, layout }) {
  const { icon: Icon, label, disabled } = tab;
  const side = layout === "side";
  const tone = disabled ? "text-gray-600" : active ? "text-white" : "text-gray-400 hover:text-gray-100";
  const shape = side
    ? `h-10 px-2 rounded-lg flex items-center gap-2.5 text-sm font-medium ${active ? "bg-white/[0.06]" : "hover:bg-white/[0.04]"}`
    : "flex-1 h-14 flex flex-col items-center justify-center gap-0.5 text-caption font-medium";
  const content = (
    <>
      <Icon size={side ? 17 : 20} className={active ? "text-link" : undefined} />
      <span className="truncate">{label}</span>
    </>
  );

  if (disabled) {
    return (
      <span className={`${shape} ${tone} cursor-not-allowed`} aria-disabled="true" title="Disponible une fois la phase finale lancée">
        {content}
      </span>
    );
  }
  return (
    <Link to={href} className={`${shape} ${tone} transition-colors`} aria-current={active ? "page" : undefined}>
      {content}
    </Link>
  );
}

// `/competition/:id` : ouvre l'onglet de départ selon le format et la phase
// (destination de la carte « Reprendre » de l'accueil).
export function CompetitionIndex() {
  const { status, groups } = useOutletContext();
  const to = status.format === "LEAGUE" ? "simulate" : status.format === "HYBRID" && !groups?.knockout_started ? "groups" : "bracket";
  return <Navigate to={to} replace />;
}
