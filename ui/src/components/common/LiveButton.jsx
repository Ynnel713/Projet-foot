import { Play } from "lucide-react";
import { LIVE_AND_ANIMATION_ENABLED } from "../../config/features";

// Bouton LIVE d'un match (championnat, poules, tableau : toutes les compétitions), TOUJOURS actif : il ouvre directement l'ANIMATION
// du match (sans révéler le score). Match déjà joué : animation immédiate ; match pas encore joué : l'écran simule d'abord
// (journée / tour), puis ouvre l'animation -- pastille bleue. Hitbox : le bouton EST la zone cliquable (relative, z-10,
// pointer-events-auto, flex centré, hauteur fixe), pas d'enveloppe en ligne autour.
export default function LiveButton({ played, onLive, compact = false }) {
  if (!LIVE_AND_ANIMATION_ENABLED) return null;
  return (
    <button
      type="button"
      aria-label="Lancer l'animation du match"
      title={played ? "Revoir l'animation du match" : "Simuler puis lancer l'animation du match"}
      onClick={(e) => {
        e.stopPropagation();
        onLive();
      }}
      className={`relative z-10 pointer-events-auto cursor-pointer justify-self-end shrink-0 rounded-lg flex items-center justify-center gap-1.5
                  bg-live text-bg font-bold tracking-wide transition-transform hover:brightness-110 active:scale-95
                  ${compact ? "h-6 min-w-14 px-2 text-caption" : "h-9 min-w-[4.75rem] px-3 text-xs"} ${played ? "live-btn-pulse" : ""}`}
    >
      <Play size={compact ? 9 : 11} fill="currentColor" aria-hidden="true" />
      LIVE
      {!played && <span className={`${compact ? "h-1.5 w-1.5" : "h-2 w-2"} rounded-full bg-accent ring-2 ring-white/80`} aria-hidden="true" />}
    </button>
  );
}
