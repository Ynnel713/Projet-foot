// Buteurs affichés sous chaque équipe (domicile à gauche, extérieur à
// droite) plutôt que sur une seule ligne mélangée -- on ne sait sinon plus
// qui a marqué pour qui sur un score du genre 2-2.
export default function ScorersLine({ scorers, home, away, className = "" }) {
  if (!scorers || scorers.length === 0) return null;
  const homeScorers = scorers.filter((s) => s.club === home);
  const awayScorers = scorers.filter((s) => s.club === away);

  return (
    <div className={`flex items-start justify-between gap-2 text-[9px] text-gray-600 ${className}`}>
      <span className="flex-1 min-w-0 truncate">{homeScorers.map((s) => `${s.player} ${s.minute}'`).join(", ")}</span>
      <span className="flex-1 min-w-0 truncate text-right">
        {awayScorers.map((s) => `${s.player} ${s.minute}'`).join(", ")}
      </span>
    </div>
  );
}
