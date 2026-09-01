import { Trophy, Play, ListOrdered, Users, Swords, Target } from "lucide-react";
import { NavLink } from "react-router-dom";
import { useGameStore } from "../../store/useGameStore";

export default function BottomNav() {
  const activeCompetitionId = useGameStore((s) => s.activeCompetitionId);
  const format = useGameStore((s) => s.activeCompetitionFormat);

  // "Matchs" retiré : redondant avec "Simulation", qui montre déjà les
  // matchs de la journée courante (à venir ou joués). "Simulation" reste
  // indispensable : sans lui, quitter cet écran (ex. via "Classement") ne
  // laissait aucun moyen d'y revenir.
  const base = { to: "/", label: "Compétitions", Icon: Trophy, end: true };
  const TABS =
    format === "HYBRID"
      ? [
          base,
          { to: activeCompetitionId ? `/competition/${activeCompetitionId}/groups` : "/", label: "Poules", Icon: Users },
          { to: activeCompetitionId ? `/competition/${activeCompetitionId}/bracket` : "/", label: "Tableau", Icon: Swords },
          {
            to: activeCompetitionId ? `/competition/${activeCompetitionId}/leaderboards` : "/",
            label: "Buteurs",
            Icon: Target,
          },
        ]
      : [
          base,
          {
            to: activeCompetitionId ? `/competition/${activeCompetitionId}/simulate` : "/",
            label: "Simulation",
            Icon: Play,
          },
          { to: activeCompetitionId ? `/competition/${activeCompetitionId}/standings` : "/", label: "Classement", Icon: ListOrdered },
        ];

  return (
    // h-14 (56px) et min-h-[48px] par onglet : au-dessus du minimum tactile
    // de 48px demandé.
    <nav className="h-14 shrink-0 bg-surface border-t border-white/5 flex">
      {TABS.map(({ to, label, Icon, end }) => (
        <NavLink
          key={label}
          to={to}
          end={end}
          className={({ isActive }) =>
            `flex-1 flex flex-col items-center justify-center gap-0.5 min-h-[48px] text-[11px] transition-colors ${
              isActive ? "text-accent" : "text-gray-400"
            }`
          }
        >
          <Icon size={20} strokeWidth={2} />
          {label}
        </NavLink>
      ))}
    </nav>
  );
}
