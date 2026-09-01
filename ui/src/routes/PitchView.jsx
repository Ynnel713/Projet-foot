import { useEffect, useState } from "react";
import { useParams, useSearchParams, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { getPitchView } from "../api/client";

// Terrain HORIZONTAL (adapté au format paysage) : le placement calculé côté
// moteur (pitch_layout.place_starting_xi) est vertical -- domicile en haut
// (y 10-42), extérieur en bas (y 58-90), x = position latérale 0-100. On
// pivote à l'affichage : le "y" du moteur (profondeur) devient la position
// HORIZONTALE à l'écran ; le "x" (latéral) devient la position VERTICALE,
// mais en le MIROITANT (100 - x) -- une simple permutation x<->y n'est pas
// une rotation à 90° mais une réflexion, qui inverserait gauche/droite
// (ailiers, latéraux) par rapport à la vraie orientation de chaque équipe.
export default function PitchView() {
  const { id } = useParams();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const home = params.get("home");
  const away = params.get("away");
  const journee = params.get("journee");
  const group = params.get("group");
  const matchday = params.get("matchday");
  const roundNumber = params.get("round_number");
  const leg = params.get("leg");

  // Libellé de contexte : championnat (Journée N), poule (Groupe + journée),
  // ou tableau (Tour N, Aller/Retour) -- voir les 3 jeux de paramètres
  // possibles côté API (api.routers.competitions.get_pitch_view).
  let contextLabel = "";
  if (journee) contextLabel = `Journée ${journee}`;
  else if (group) contextLabel = `${group} · Journée ${Number(matchday) + 1}`;
  else if (roundNumber) contextLabel = `Tour ${roundNumber} · ${leg === "0" ? "Aller" : "Retour"}`;

  useEffect(() => {
    getPitchView(id, { home, away, journee, group, matchday, round_number: roundNumber, leg })
      .then(setData)
      .catch(() => setError("Composition indisponible pour ce match."));
  }, [id, home, away, journee, group, matchday, roundNumber, leg]);

  if (error) {
    return (
      <div className="p-6 flex flex-col gap-3 items-start">
        <p className="text-sm text-gray-400">{error}</p>
        <button onClick={() => navigate(-1)} className="text-accent text-sm font-medium">
          ← Retour
        </button>
      </div>
    );
  }
  if (!data) return <div className="p-6 text-sm text-gray-400">Chargement…</div>;

  return (
    <div className="flex flex-col h-full p-3 gap-2">
      <div className="flex items-center justify-between shrink-0">
        <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-xs text-gray-400">
          <ArrowLeft size={14} /> Retour
        </button>
        <span className="text-xs text-gray-500">{contextLabel}</span>
      </div>

      <div className="flex items-center justify-center gap-3 shrink-0 text-sm">
        <span className="font-semibold truncate max-w-[35%]">{data.home}</span>
        <span className="text-xs text-gray-500">{data.home_formation}</span>
        <span className="font-bold tabular-nums px-2">
          {data.home_goals} - {data.away_goals}
        </span>
        <span className="text-xs text-gray-500">{data.away_formation}</span>
        <span className="font-semibold truncate max-w-[35%]">{data.away}</span>
      </div>

      <div className="flex-1 min-h-0 relative rounded-xl bg-emerald-900/40 border border-emerald-700/40 overflow-hidden">
        {/* ligne médiane (verticale, puisque le terrain est pivoté à l'horizontale) */}
        <div className="absolute inset-y-0 left-1/2 w-px bg-white/20" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-16 w-16 rounded-full border border-white/20" />

        {data.home_players.map((p) => (
          <PlayerDot key={p.name} player={p} color="bg-accent" />
        ))}
        {data.away_players.map((p) => (
          <PlayerDot key={p.name} player={p} color="bg-gold text-bg" />
        ))}
      </div>
    </div>
  );
}

function PlayerDot({ player, color }) {
  const initials = player.name
    .split(" ")
    .map((p) => p[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <div
      className="absolute -translate-x-1/2 -translate-y-1/2 flex flex-col items-center gap-0.5"
      style={{ left: `${player.y}%`, top: `${100 - player.x}%` }}
    >
      <div className={`h-7 w-7 rounded-full ${color} flex items-center justify-center text-[10px] font-bold shadow`}>
        {initials}
      </div>
      <span className="text-[9px] text-white/80 text-center leading-tight w-max max-w-[140px]">{player.name}</span>
      {(player.goals > 0 || player.yellow_cards > 0 || player.red_card) && (
        <span className="text-[9px] leading-none">
          {"⚽".repeat(Math.min(player.goals, 3))}
          {player.yellow_cards > 0 && "🟨"}
          {player.red_card && "🟥"}
        </span>
      )}
    </div>
  );
}
