import { motion } from "framer-motion";

export default function MatchRow({ match, onClick }) {
  const notPlayed = !match.played;
  const diff = notPlayed ? 0 : match.home_goals - match.away_goals;
  const border = notPlayed
    ? "border-l-gray-700"
    : diff > 0
      ? "border-l-emerald-500"
      : diff < 0
        ? "border-l-red-500"
        : "border-l-gray-500";
  const clickable = Boolean(onClick) && match.played;
  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      onClick={clickable ? onClick : undefined}
      className={`flex flex-col bg-surface rounded-lg px-3 py-2 border-l-4 min-h-[44px] justify-center ${border} ${
        clickable ? "cursor-pointer active:scale-[0.99] transition-transform" : ""
      }`}
    >
      <div className="flex items-center justify-between">
        <span className="flex-1 min-w-0 text-sm truncate">{match.home}</span>
        <span className="font-bold tabular-nums px-3 shrink-0">
          {notPlayed ? "– –" : `${match.home_goals} - ${match.away_goals}`}
        </span>
        <span className="flex-1 min-w-0 text-sm text-right truncate">{match.away}</span>
      </div>
      {match.scorers?.length > 0 && (
        <div className="text-[10px] text-gray-500 truncate mt-0.5">
          ⚽ {match.scorers.map((s) => `${s.player} ${s.minute}'`).join(", ")}
        </div>
      )}
    </motion.div>
  );
}
