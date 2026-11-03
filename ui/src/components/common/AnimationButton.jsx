import { Video } from "lucide-react";
import { LIVE_AND_ANIMATION_ENABLED } from "../../config/features";

// Bouton "voir l'animation" d'un match déjà joué, directement depuis la liste des matchs -- n'affiche JAMAIS le score
// avant (US-15/16, docs/PRD_PRODUIT.md) : contrairement au clic sur la ligne (ouvre la fiche, score visible) ou au
// bouton LIVE (replay commenté), ce bouton ouvre l'animation seule, sans passer par un écran qui révèle le résultat.
// Même convention que LiveButton : le clic ne remonte pas (la ligne ouvre le détail classique).
export default function AnimationButton({ onAnimation, compact = false }) {
  if (!LIVE_AND_ANIMATION_ENABLED) return null;
  return (
    <button
      type="button"
      aria-label="Voir l'animation du match"
      title="Voir l'animation, sans révéler le score"
      onClick={(e) => {
        e.stopPropagation();
        onAnimation();
      }}
      className={`relative z-10 pointer-events-auto cursor-pointer justify-self-end shrink-0 rounded-lg flex items-center justify-center gap-1.5
                  bg-surface border border-line text-gray-200 font-semibold tracking-wide transition-transform hover:brightness-125 active:scale-95
                  ${compact ? "h-6 min-w-14 px-2 text-caption" : "h-9 min-w-[4.75rem] px-3 text-xs"}`}
    >
      <Video size={compact ? 9 : 11} aria-hidden="true" />
      Animation
    </button>
  );
}
