import { X } from "lucide-react";
import { hudName, scorerText } from "../../utils/matchHud";

// États du match sur le terrain (ticket v2-ecran-match/13, décisions du propriétaire du 19/11/2026 ; spec § Interactions).
// Aucun bandeau ne capte le pointeur : la lecture, la pause et les clics sur le terrain restent possibles. Seule la carte
// de fin est cliquable (Retour, fermer).

// Bandeau en haut du terrain, sous le HUD : but (« BUT · 23' · Kvaratskhelia · club », liseré à la couleur de l'équipe)
// ou coup d'envoi.
export function TopBanner({ kind, children, side }) {
  return (
    <div className="absolute inset-x-0 top-3 flex justify-center pointer-events-none z-10">
      <div
        data-banner={kind}
        role="status"
        className="max-w-[90%] truncate rounded bg-surface/90 border border-line px-3 py-1 font-display text-[18px] font-bold uppercase tracking-wide text-white shadow-lg"
        style={side ? { borderLeft: `4px solid var(--team-${side}-ui)` } : undefined}
      >
        {children}
      </div>
    </div>
  );
}

// Mi-temps : carte centrée, discrète, avec le score ; plus de masque noir sur tout le terrain (spec).
export function HalfTimeBanner({ home, away, score }) {
  return (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
      <div data-banner="mi-temps" role="status" className="rounded-lg bg-surface/85 border border-line px-6 py-3 text-center shadow-lg">
        <div className="font-display text-2xl font-extrabold tracking-widest text-white">MI-TEMPS</div>
        <div className="text-lg text-gray-200 tabular-nums">
          {home} {score.home} - {score.away} {away}
        </div>
      </div>
    </div>
  );
}

// Fin : carte centrée sur le terrain (TERMINÉ, score, buteurs, Retour), refermable pour revoir la position finale.
// Bouton Statistiques : ticket EM-14.
export function FullTimeCard({ home, away, score, scorers, onBack, onClose }) {
  const list = (side) => (
    <ul className={`min-w-0 text-data leading-5 text-gray-300 ${side === "home" ? "text-right" : "text-left"}`}>
      {scorers[side].all.map((row) => (
        <li key={`${row.name}-${row.ownGoal}`} title={scorerText(row)} className="truncate">
          {hudName(row.name)}
          {row.ownGoal ? " (csc)" : ""} <span className="text-white tabular-nums">{row.minutes.join(", ")}</span>
        </li>
      ))}
    </ul>
  );
  return (
    <div className="absolute inset-0 flex items-center justify-center z-20 pointer-events-none">
      <div
        data-banner="fin"
        role="dialog"
        aria-label="Fin du match"
        className="pointer-events-auto relative w-[min(92%,440px)] rounded-lg bg-surface/95 border border-line px-5 py-4 shadow-xl"
      >
        <button
          onClick={onClose}
          aria-label="Fermer"
          className="absolute right-1 top-1 flex size-11 items-center justify-center text-gray-400 hover:text-white"
        >
          <X size={16} />
        </button>
        <div className="text-center text-caption font-semibold tracking-widest text-gold">TERMINÉ</div>
        <div className="mt-1 grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-x-3">
          <div className="truncate text-right font-display text-lg font-bold uppercase text-white">{home}</div>
          <div data-zone="score-final" className="font-display text-4xl font-bold tabular-nums text-white">
            {score.home}
            <span className="mx-1.5 text-gray-500">-</span>
            {score.away}
          </div>
          <div className="truncate text-left font-display text-lg font-bold uppercase text-white">{away}</div>
          {list("home")}
          <div />
          {list("away")}
        </div>
        <div className="mt-3 flex justify-center">
          <button onClick={onBack} className="min-h-11 rounded bg-accent px-5 text-data font-semibold text-white">
            Retour
          </button>
        </div>
      </div>
    </div>
  );
}
