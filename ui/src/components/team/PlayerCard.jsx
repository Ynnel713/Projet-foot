import { BASE_URL } from "../../api/client";
import { fmTierColor } from "../../utils/fmTier";

const PIED_LABELS = { D: "Droit", G: "Gauche" };

// Équivalent PWA de app._team_player_card_html (Streamlit) : photo (ou
// placeholder), note badge coloré, nom, poste/âge/pied. `onSelect` navigue
// vers la fiche du joueur (écran indépendant, voir PlayerPage) -- pas
// d'état "sélectionné" ici, ce composant ne fait qu'ouvrir cette fiche.
export default function PlayerCard({ player, onSelect }) {
  const pied = PIED_LABELS[player.pied] ?? "";
  const meta = [player.poste, `${player.age} ans`, pied].filter(Boolean).join(" · ");

  return (
    <button
      onClick={onSelect}
      className="relative bg-white/[0.04] border border-white/10 rounded-xl p-2 text-center transition-colors hover:bg-white/[0.06]"
    >
      <div
        className="absolute top-1.5 left-1.5 min-w-[22px] h-[22px] px-1 rounded-md flex items-center justify-center text-[11px] font-extrabold text-white"
        style={{ backgroundColor: fmTierColor(player.note) }}
      >
        {player.note.toFixed(0)}
      </div>
      {player.photo_url ? (
        <img
          src={`${BASE_URL}${player.photo_url}`}
          alt=""
          className="w-[60px] h-[60px] rounded-lg mx-auto mb-1.5 object-cover border border-white/10"
        />
      ) : (
        <div className="w-[60px] h-[60px] rounded-lg mx-auto mb-1.5 flex items-center justify-center bg-white/[0.06] text-white/30 text-lg">
          ?
        </div>
      )}
      <div className="font-bold text-xs text-white truncate">{player.name}</div>
      <div className="text-[10.5px] text-gray-400 mt-0.5">{meta}</div>
    </button>
  );
}
