import { ChevronUp, ChevronDown, Minus, Star } from "lucide-react";
import { useGameStore } from "../../store/useGameStore";
import { parseFlaggedName } from "../../utils/flags";
import TeamLink from "../common/TeamLink";

// Classement unique de l'app (refonte UI, lot 3) : championnat (colonne de la journée et écran Classement), poules, phase de ligue.
// Colonnes `# · Club · J · BP · BC · Diff · Pts` ; sur mobile `# · Club · J · Diff · Pts` (BP et BC masqués avec leurs titres).
// `dense` : phase de ligue de 36 clubs -- texte 11 px et lignes de 20 px sur bureau (la page tient sans défiler à 1440 x 900),
// lignes de 36 px au doigt sur mobile. L'en-tête reste figé si le conteneur défile (fenêtre trop basse).
// `zoneOf(index)` : "direct" (bande verte) / "out" (rouge) / rien ; la légende nomme les zones, la couleur n'est pas le seul signal.
const ZONE_BORDER = { direct: "border-win", out: "border-loss" };

export default function StandingsTable({ rows, dense = false, zoneOf, showRankChange = false, followable = false }) {
  const followedClub = useGameStore((s) => s.followedClub);
  const setFollowedClub = useGameStore((s) => s.setFollowedClub);
  const nations = parseFlaggedName(rows[0]?.club ?? "").code !== null;

  const rowHeight = dense ? "h-9 md:h-5" : "h-9 md:h-8";
  const text = dense ? "text-data md:text-caption" : "text-data";
  const head = "sticky top-0 z-10 bg-surface h-6 text-caption font-medium text-gray-500";

  return (
    <table className={`w-full border-collapse table-fixed ${text}`}>
      <thead>
        <tr>
          {showRankChange && <th className={`${head} w-6`} aria-label="Évolution" />}
          <th className={`${head} w-9 text-left pl-2`}>#</th>
          <th className={`${head} text-left`}>{nations ? "Pays" : "Club"}</th>
          <th className={`${head} w-9 text-center`}>J</th>
          <th className={`${head} w-10 text-center hidden sm:table-cell`}>BP</th>
          <th className={`${head} w-10 text-center hidden sm:table-cell`}>BC</th>
          <th className={`${head} w-11 text-center`}>Diff</th>
          <th className={`${head} w-10 text-center font-semibold text-gray-300`}>Pts</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => {
          const followed = row.club === followedClub; // surligné partout ; l'étoile pour suivre n'existe que sur l'écran Classement
          const zone = zoneOf?.(i);
          const diffTone = row.goal_diff > 0 ? "text-win" : row.goal_diff < 0 ? "text-loss" : "text-draw";
          return (
            <tr
              key={row.club}
              className={`${rowHeight} ${dense ? "" : "border-t border-line"} ${i % 2 ? "bg-white/[0.02]" : ""} ${
                followed ? "!bg-gold/15 text-gold" : "text-gray-300"
              }`}
            >
              {showRankChange && (
                <td className="text-center">
                  <RankChange value={row.rank_change} />
                </td>
              )}
              <td className={`pl-2 tabular-nums text-gray-500 border-l-2 ${zone ? ZONE_BORDER[zone] : "border-transparent"}`}>{row.rank}</td>
              <td className="max-w-0 pr-2">
                <span className="flex items-center gap-1.5 min-w-0">
                  {followable && (
                    <button
                      onClick={() => setFollowedClub(followed ? null : row.club)}
                      className={`shrink-0 ${followed ? "text-gold" : "text-gray-600 hover:text-gray-400"}`}
                      aria-label={followed ? `Ne plus suivre ${row.club}` : `Suivre ${row.club}`}
                    >
                      <Star size={13} fill={followed ? "currentColor" : "none"} />
                    </button>
                  )}
                  <TeamLink name={row.club} logoSize={dense ? 16 : 18} className={`min-h-9 md:min-h-0 font-medium ${followed ? "text-gold" : "text-gray-100"}`} />
                </span>
              </td>
              <td className="text-center tabular-nums text-gray-500">{row.played}</td>
              <td className="text-center tabular-nums hidden sm:table-cell">{row.goals_for}</td>
              <td className="text-center tabular-nums hidden sm:table-cell">{row.goals_against}</td>
              <td className={`text-center tabular-nums ${followed ? "" : diffTone}`}>{row.goal_diff > 0 ? `+${row.goal_diff}` : row.goal_diff}</td>
              <td className="text-center tabular-nums font-bold text-white">{row.points}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

function RankChange({ value }) {
  if (value > 0) return <ChevronUp size={14} className="inline text-win" aria-label="Monte" />;
  if (value < 0) return <ChevronDown size={14} className="inline text-loss" aria-label="Descend" />;
  return <Minus size={12} className="inline text-gray-600" aria-label="Stable" />;
}
