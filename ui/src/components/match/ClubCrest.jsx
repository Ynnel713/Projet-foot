import ClubBadge from "../team/ClubBadge";

// Écusson d'équipe du HUD (ticket v2-ecran-match/08) : `ClubBadge` (logo, sinon initiales sur la couleur d'équipe)
// cerclé de la couleur d'équipe. 44 px, 32 px sous 960 px de large ou 500 px de haut (constantes validées par le
// propriétaire le 19/11/2026).
export default function ClubCrest({ club, side }) {
  const color = `var(--team-${side})`;
  return (
    <div
      className="size-11 max-[959.98px]:size-8 [@media(max-height:499.98px)]:size-8 shrink-0 rounded-full text-sm max-[959.98px]:text-[11px] [@media(max-height:499.98px)]:text-[11px]"
      style={{ boxShadow: `0 0 0 2px var(--team-${side}-ui)` }}
    >
      <ClubBadge clubName={club} color={color} size="100%" />
    </div>
  );
}
