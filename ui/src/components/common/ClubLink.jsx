import { useParams, useNavigate } from "react-router-dom";
import ClubLogo from "./ClubLogo";

// Nom de club (avec écusson, voir ClubLogo) cliquable vers son effectif
// (`/competition/:id/clubs/:name`), partagé par tous les écrans où un club
// apparaît (classement, journée, terrain, poules, tableau, classements
// buteurs/passeurs) -- l'utilisateur doit pouvoir y accéder "à tout
// moment", pas seulement depuis le classement (retour terrain du
// 27/09/2026). Lit `:id` depuis la route courante : tous les écrans
// concernés vivent sous `/competition/:id/...`.
// `stopPropagation` : à passer quand ce lien est imbriqué dans un élément
// cliquable parent (ex. une ligne de match qui ouvre la vue terrain).
// `align="end"` inverse l'ordre écusson/nom (ex. équipe à l'extérieur,
// alignée à droite -- retour terrain du 28/09/2026).
export default function ClubLink({ name, className = "", stopPropagation = false, align = "start", logo = true, logoSize = 18 }) {
  const { id } = useParams();
  const navigate = useNavigate();

  return (
    <button
      onClick={(e) => {
        if (stopPropagation) e.stopPropagation();
        navigate(`/competition/${id}/clubs/${encodeURIComponent(name)}`);
      }}
      className={`flex items-center gap-1.5 min-w-0 hover:text-gold ${
        align === "end" ? "flex-row-reverse justify-end" : ""
      } ${className}`}
    >
      {logo && <ClubLogo clubName={name} size={logoSize} />}
      <span className="truncate">{name}</span>
    </button>
  );
}
