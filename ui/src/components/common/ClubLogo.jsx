import { useState } from "react";
import { clubLogoUrl } from "../../utils/clubSlug";
import { clubInitials } from "../../utils/clubInitials";

// Petit écusson de club (liste de matchs, classement, écran terrain, choix
// d'équipe...) -- vrai logo si déposé dans public/logos/clubs, sinon repli
// discret sur les initiales (pas de couleur de club ici : ces écrans n'ont
// pas forcément la couleur sous la main, contrairement à ClubBadge sur la
// fiche club -- voir clubSlug.js pour la convention de nom de fichier).
export default function ClubLogo({ clubName, size = 20, className = "" }) {
  const [imgFailed, setImgFailed] = useState(false);
  const style = { width: size, height: size };

  if (!imgFailed) {
    return (
      <img
        src={clubLogoUrl(clubName)}
        alt=""
        style={style}
        className={`rounded-full object-contain bg-white/[0.04] shrink-0 ${className}`}
        onError={() => setImgFailed(true)}
      />
    );
  }

  return (
    <div
      style={{ ...style, fontSize: size * 0.4 }}
      className={`rounded-full bg-white/10 text-white/50 flex items-center justify-center font-bold shrink-0 ${className}`}
    >
      {clubInitials(clubName)}
    </div>
  );
}
