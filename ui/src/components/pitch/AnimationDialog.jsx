import { useEffect } from "react";
import MatchAnimation from "./MatchAnimation";
import { LIVE_AND_ANIMATION_ENABLED } from "../../config/features";

// Fenêtre modale de l'animation : un calque plein écran, montable depuis n'importe quel écran (fiche match, liste de
// matchs...) sans jamais devoir d'abord afficher le score/résultat (US-15/16, docs/PRD_PRODUIT.md) -- extrait de
// PitchView.jsx (23/10/2026) pour être réutilisable depuis la liste des matchs (MatchRow), qui affiche le score en
// permanence et ne doit donc jamais être le passage obligé vers l'animation.
export default function AnimationDialog({ competitionId, matchParams, onClose }) {
  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  if (!LIVE_AND_ANIMATION_ENABLED) return null;

  return (
    <div role="dialog" aria-modal="true" aria-label="Animation du match" className="fixed inset-0 z-50 bg-black flex items-center justify-center p-3">
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
