// Panneau bordé avec icône + titre -- unité visuelle réutilisée par toutes
// les sections de la fiche joueur (28/09/2026, rapprochement d'une
// maquette fournie par l'utilisateur).
export default function SectionPanel({ icon: Icon, title, className = "", children }) {
  return (
    <div className={`rounded-xl bg-surface border border-line p-4 ${className}`}>
      <div className="flex items-center gap-1.5 mb-2.5">
        {Icon && <Icon size={13} className="text-gray-500 shrink-0" />}
        <span className="text-caption font-medium text-gray-400">{title}</span>
      </div>
      {children}
    </div>
  );
}
