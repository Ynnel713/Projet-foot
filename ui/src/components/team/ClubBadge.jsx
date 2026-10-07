import { useState } from "react";
import { clubInitials } from "../../utils/clubInitials";
import { clubLogoUrl } from "../../utils/clubSlug";

// Écusson du club : vrai logo (public/logos/clubs/<slug>.png, voir clubSlug.js)
// si présent, sinon repli sur le rond d'initiales colorées existant --
// beaucoup de clubs n'ont pas encore de logo déposé, la couverture se
// complète au fil du temps (retour terrain du 28/09/2026).
export default function ClubBadge({ clubName, color, size = 56, className = "" }) {
  const [imgFailed, setImgFailed] = useState(false);
  const style = { width: size, height: size };

  if (!imgFailed) {
    return (
      <img
        src={clubLogoUrl(clubName)}
        alt={clubName}
        style={style}
        className={`rounded-full object-contain bg-white/[0.04] border border-white/10 shrink-0 ${className}`}
        onError={() => setImgFailed(true)}
      />
    );
  }

  return (
    <div
      style={{ ...style, backgroundColor: color }}
      className={`rounded-full flex items-center justify-center font-extrabold text-white shrink-0 ${className}`}
    >
      {clubInitials(clubName)}
    </div>
  );
}
