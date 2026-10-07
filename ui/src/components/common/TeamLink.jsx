import { useParams, useNavigate } from "react-router-dom";
import { parseFlaggedName, flagUrl } from "../../utils/flags";
import ClubLogo from "./ClubLogo";

// Nom d'équipe cliquable partagé par les écrans de poules/tableau
// (Groups.jsx, Bracket.jsx), utilisés aussi bien par la Coupe du Monde
// (sélections nationales) que par une Compétition Perso à poules/élimination
// (clubs) -- détecte lequel des deux via `parseFlaggedName` (un nom de
// sélection commence par un emoji drapeau, voir nations.py) plutôt que de
// dépendre du contexte appelant :
//   - sélection : drapeau réel (flagcdn.com, l'emoji ne s'affiche pas de
//     façon fiable partout) + nom du pays SEUL, jamais d'écusson de club
//     (retour terrain du 29/09/2026 : "juste drapeau + nom pays").
//   - club : écusson (ClubLogo), comme ClubLink partout ailleurs dans l'app.
export default function TeamLink({ name, className = "", stopPropagation = false, align = "start" }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const { code, label } = parseFlaggedName(name);
  const isNation = code !== null;

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
      {isNation ? (
        <img src={flagUrl(code)} alt="" className="h-3.5 w-5 rounded-sm object-cover shrink-0" />
      ) : (
        <ClubLogo clubName={name} size={18} />
      )}
      <span className="truncate">{isNation ? label : name}</span>
    </button>
  );
}
