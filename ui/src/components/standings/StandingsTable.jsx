import { ChevronUp, ChevronDown, Minus } from "lucide-react";
import { useGameStore } from "../../store/useGameStore";

export default function StandingsTable({ rows }) {
  const followedClub = useGameStore((s) => s.followedClub);
  const setFollowedClub = useGameStore((s) => s.setFollowedClub);

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs sm:text-sm border-collapse">
        <thead>
          <tr className="text-gray-400 text-left">
            <th className="px-2 py-2 w-8"></th>
            <th className="px-2 py-2 w-8">#</th>
            <th className="px-2 py-2">Club</th>
            <th className="px-2 py-2 text-center">J</th>
            <th className="px-2 py-2 text-center">G</th>
            <th className="px-2 py-2 text-center">N</th>
            <th className="px-2 py-2 text-center">P</th>
            <th className="px-2 py-2 text-center">BP</th>
            <th className="px-2 py-2 text-center">BC</th>
            <th className="px-2 py-2 text-center">Diff</th>
            <th className="px-2 py-2 text-center font-semibold">Pts</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => {
            const isFollowed = row.club === followedClub;
            return (
              <tr
                key={row.club}
                onClick={() => setFollowedClub(isFollowed ? null : row.club)}
                className={`cursor-pointer ${
                  isFollowed ? "bg-gold/15 text-gold" : i % 2 === 0 ? "bg-white/[0.02]" : "bg-transparent"
                }`}
              >
                <td className="px-2 py-1.5">
                  <RankChange value={row.rank_change} />
                </td>
                <td className="px-2 py-1.5 tabular-nums text-gray-400">{row.rank}</td>
                <td className="px-2 py-1.5 font-medium truncate max-w-[9rem] sm:max-w-none">{row.club}</td>
                <td className="px-2 py-1.5 text-center tabular-nums">{row.played}</td>
                <td className="px-2 py-1.5 text-center tabular-nums">{row.won}</td>
                <td className="px-2 py-1.5 text-center tabular-nums">{row.drawn}</td>
                <td className="px-2 py-1.5 text-center tabular-nums">{row.lost}</td>
                <td className="px-2 py-1.5 text-center tabular-nums hidden sm:table-cell">{row.goals_for}</td>
                <td className="px-2 py-1.5 text-center tabular-nums hidden sm:table-cell">{row.goals_against}</td>
                <td className="px-2 py-1.5 text-center tabular-nums">{row.goal_diff}</td>
                <td className="px-2 py-1.5 text-center tabular-nums font-bold">{row.points}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function RankChange({ value }) {
  if (value > 0) return <ChevronUp size={14} className="text-emerald-500" />;
  if (value < 0) return <ChevronDown size={14} className="text-red-500" />;
  return <Minus size={12} className="text-gray-600" />;
}
