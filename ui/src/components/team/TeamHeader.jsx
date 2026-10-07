import { fmTierColor } from "../../utils/fmTier";
import ClubBadge from "./ClubBadge";

// Équivalent PWA de app._render_team_header (Streamlit) : écusson du club
// (vrai logo si déposé, sinon badge coloré aux initiales -- voir
// ClubBadge), identité du club, et 3 tuiles de stats (note globale, âge
// moyen, valeur estimée -- cette dernière absente si aucun joueur n'a de
// valeur marchande connue, voir RosterOut.valeur_totale).
export default function TeamHeader({ roster }) {
  return (
    <div className="rounded-2xl bg-surface border border-white/10 p-4 flex flex-col gap-3">
      <div className="flex items-center gap-3 flex-wrap">
        <ClubBadge clubName={roster.club} color={roster.color} size={56} />
        <div className="min-w-0">
          <div className="font-extrabold text-lg text-white truncate">{roster.club}</div>
          <div className="text-xs text-gray-400">
            {roster.championnat} · {roster.players.length} joueurs
          </div>
        </div>
      </div>

      <div className="flex gap-2 flex-wrap">
        <StatTile label="Note globale" value={roster.note.toFixed(0)} color={fmTierColor(roster.note)} />
        <StatTile label="Âge moyen" value={roster.age_moyen.toFixed(1)} />
        {roster.valeur_totale != null && (
          <StatTile label="Valeur estimée" value={`€${roster.valeur_totale.toFixed(0)}M`} />
        )}
      </div>
    </div>
  );
}

function StatTile({ label, value, color }) {
  return (
    <div className="bg-white/[0.03] border border-white/10 rounded-lg px-3 py-1.5 text-center min-w-[84px]">
      <div className="text-[9.5px] font-bold uppercase tracking-wide text-gray-400">{label}</div>
      <div className="text-xl font-extrabold leading-tight" style={color ? { color } : undefined}>
        {value}
      </div>
    </div>
  );
}
