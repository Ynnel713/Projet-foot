import { Home } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useGameStore } from "../../store/useGameStore";

// Bouton accueil : seul moyen de revenir à l'écran d'accueil depuis n'importe
// quel écran maintenant que le ruban de navigation du bas a été retiré (voir
// AppShell) -- chaque écran interne (Classement, Poules, Tableau, Buteurs...)
// garde son propre "Retour" local, mais l'accueil doit rester joignable en un
// clic depuis partout.
export default function Header() {
  const activeCompetitionLabel = useGameStore((s) => s.activeCompetitionLabel);
  const navigate = useNavigate();

  return (
    <header className="h-12 shrink-0 flex items-center justify-between px-4 bg-surface border-b border-white/5">
      <div className="flex items-center gap-3 min-w-0">
        <button
          onClick={() => navigate("/")}
          aria-label="Accueil"
          title="Accueil"
          className="h-8 w-8 shrink-0 rounded-lg flex items-center justify-center text-gray-300
                     hover:bg-white/10 hover:text-white active:scale-95 transition-all"
        >
          <Home size={17} strokeWidth={2.25} />
        </button>
        <div className="flex items-center gap-2 min-w-0">
          <img src="/icons/logo-mark.png" alt="" className="h-7 w-7 rounded-md shrink-0" />
          <span className="font-semibold text-sm tracking-tight truncate">Simulafoot</span>
        </div>
      </div>
      <span className="text-xs text-gray-400 truncate px-2">
        {activeCompetitionLabel ?? "Saison 2026-2027"}
      </span>
    </header>
  );
}
