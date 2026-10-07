import { Play } from "lucide-react";

// Bouton LIVE d'un match (championnat, poules, tableau : toutes les compétitions), TOUJOURS actif. Match déjà joué : il rouvre le live
// (replay à l'horloge accélérée) ; match pas encore joué : l'écran simule d'abord (journée / tour), puis ouvre le live -- pastille bleue.
// Le clic ne remonte pas (la ligne ouvre le détail classique). Hitbox : le bouton EST la zone cliquable (relative, z-10,
// pointer-events-auto, flex centré, hauteur fixe), pas d'enveloppe en ligne autour.
export default function LiveButton({ played, onLive, compact = false }) {
  return (
    <button
      type="button"
      aria-label="Ouvrir le match en direct"
      title={played ? "Revoir le match en direct" : "Lancer le match en direct"}
      onClick={(e) => {
        e.stopPropagation();
        onLive();
      }}
      className={`relative z-10 pointer-events-auto cursor-pointer justify-self-end shrink-0 rounded-[10px] flex items-center justify-center gap-1.5
                  bg-live text-[#0f1419] font-bold tracking-wide transition-transform hover:brightness-110 active:scale-95
                  ${compact ? "h-6 min-w-[3.5rem] px-2 text-[10px]" : "h-9 min-w-[4.75rem] px-3 text-xs"} ${played ? "live-btn-pulse" : ""}`}
    >
      <Play size={compact ? 9 : 11} fill="currentColor" aria-hidden="true" />
      LIVE
      {!played && <span className={`${compact ? "h-1.5 w-1.5" : "h-2 w-2"} rounded-full bg-accent ring-2 ring-white/80`} aria-hidden="true" />}
    </button>
  );
}
