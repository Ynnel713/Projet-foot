export default function ProgressBar({ current, total }) {
  const pct = total ? Math.round((Math.min(current, total) / total) * 100) : 0;
  return (
    // w-full : sans largeur explicite, un conteneur placé dans un parent
    // flex se réduit à la largeur de son contenu, et le justify-between
    // ci-dessous n'a alors aucun espace à répartir entre les deux <span>.
    <div className="w-full">
      <div className="flex justify-between text-xs text-gray-400 mb-1">
        <span>
          Journée {current ?? "–"} / {total ?? "–"}
        </span>
        <span>{pct}%</span>
      </div>
      <div className="h-2 w-full rounded-full bg-white/10 overflow-hidden">
        <div
          className="h-full rounded-full bg-gradient-to-r from-accent to-gold transition-[width] duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
