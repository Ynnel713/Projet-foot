import { fmTierTextColor } from "../../utils/fmTier";
import ClubBadge from "./ClubBadge";

// En-tête de la page club (refonte UI, lot 5) : écusson, identité, trois chiffres clés (note globale, âge moyen, valeur estimée --
// absente si aucun joueur n'a de valeur connue) et, en championnat, la forme sur les 5 derniers matchs (V / N / D : lettre ET couleur).
const FORM = {
  W: { letter: "V", label: "Victoire", tone: "text-win" },
  D: { letter: "N", label: "Match nul", tone: "text-draw" },
  L: { letter: "D", label: "Défaite", tone: "text-loss" },
};

export default function TeamHeader({ roster, form }) {
  return (
    <div className="rounded-xl bg-surface border border-line p-4 flex flex-col gap-3">
      <div className="flex items-center gap-3 flex-wrap">
        <ClubBadge clubName={roster.club} color={roster.color} size={48} />
        <div className="min-w-0 flex-1">
          <h1 className="font-display font-bold text-title text-white truncate">{roster.club}</h1>
          <div className="text-data text-gray-400">
            {roster.championnat} · {roster.players.length} joueurs
          </div>
        </div>
        {form?.length > 0 && (
          <div className="flex items-center gap-1.5" role="img" aria-label={`Forme : ${form.map((r) => FORM[r].label).join(", ")}`}>
            <span className="text-caption text-gray-500 mr-1">Forme</span>
            {form.map((r, i) => (
              <span key={i} className={`h-6 w-6 rounded-md bg-surface-2 flex items-center justify-center text-caption font-bold ${FORM[r].tone}`}>
                {FORM[r].letter}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="flex gap-2 flex-wrap">
        <StatTile label="Note globale" value={roster.note.toFixed(0)} color={fmTierTextColor(roster.note)} />
        <StatTile label="Âge moyen" value={roster.age_moyen.toFixed(1)} />
        {roster.valeur_totale != null && <StatTile label="Valeur estimée" value={`€${roster.valeur_totale.toFixed(0)}M`} />}
      </div>
    </div>
  );
}

function StatTile({ label, value, color }) {
  return (
    <div className="bg-surface-2 rounded-lg px-3 py-1.5 text-center min-w-[84px]">
      <div className="text-caption font-medium text-gray-400">{label}</div>
      <div className="font-display text-2xl font-bold leading-tight text-gray-100" style={color ? { color } : undefined}>
        {value}
      </div>
    </div>
  );
}
