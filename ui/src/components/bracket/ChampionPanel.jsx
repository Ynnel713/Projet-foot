import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion, useReducedMotion } from "framer-motion";
import { Trophy } from "lucide-react";
import { getLeaderboards } from "../../api/client";
import TeamLink from "../common/TeamLink";
import { pathOf, roundTitle } from "../../utils/bracketLabels";

// Écran de sacre (refonte UI, lot 6) : un seul composant pour le championnat (`standings` : podium) et les tableaux à élimination
// directe (`bracket` : parcours du champion). Le spectacle est réservé à ce moment (DESIGN.md) : une seule entrée en fondu de 250 ms,
// supprimée si l'utilisateur réduit les animations. L'or ne sert que pour la coupe et le nom du champion.
export default function ChampionPanel({ competitionId, champion, subtitle, bracket, standings }) {
  const reduceMotion = useReducedMotion();
  const [boards, setBoards] = useState(null);

  useEffect(() => {
    getLeaderboards(competitionId).then(setBoards).catch(() => setBoards(null));
  }, [competitionId, champion]);

  const path = bracket ? pathOf(bracket.rounds, champion) : [];
  const podium = standings ? standings.slice(0, 3) : [];
  const topScorer = boards?.scorers?.[0];
  const topAssist = boards?.assists?.[0];

  return (
    <motion.section
      aria-label={`Champion : ${champion}`}
      initial={reduceMotion ? false : { opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className="shrink-0 rounded-xl bg-surface border border-line p-4 sm:p-5 flex flex-col gap-4"
    >
      <div className="flex items-center gap-4">
        <Trophy size={40} className="text-gold shrink-0" aria-hidden="true" />
        <div className="min-w-0">
          <div className="text-caption font-medium text-gray-400">Champion{subtitle ? ` · ${subtitle}` : ""}</div>
          <TeamLink name={champion} logoSize={40} className="font-display font-bold text-title text-gold" />
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {path.length > 0 && (
          <div>
            <h3 className="text-caption font-medium text-gray-400 mb-1">Son parcours</h3>
            <ol>
              {path.map((step) => (
                <li key={step.round.number} className="flex items-center gap-2 h-8 text-data border-t border-line first:border-t-0">
                  <span className="w-24 shrink-0 text-caption text-gray-500 truncate">{roundTitle(step.round)}</span>
                  {step.opponent ? (
                    <>
                      <TeamLink name={step.opponent} logoSize={16} className="min-w-0 text-gray-100" />
                      <span className="ml-auto tabular-nums text-white font-semibold">
                        {step.scored} - {step.conceded}
                        {step.penalties && <span className="ml-1.5 text-caption font-normal text-gray-400">tab {step.penalties[0]}-{step.penalties[1]}</span>}
                      </span>
                    </>
                  ) : (
                    <span className="text-gray-400">Exempt</span>
                  )}
                </li>
              ))}
            </ol>
          </div>
        )}

        {podium.length > 0 && (
          <div>
            <h3 className="text-caption font-medium text-gray-400 mb-1">Podium</h3>
            <ol>
              {podium.map((row) => (
                <li key={row.club} className="flex items-center gap-2 h-8 text-data border-t border-line first:border-t-0">
                  <span className="w-5 shrink-0 tabular-nums text-gray-500">{row.rank}</span>
                  <TeamLink name={row.club} logoSize={16} className="min-w-0 text-gray-100" />
                  <span className="ml-auto tabular-nums text-white font-semibold">{row.points} pts</span>
                </li>
              ))}
            </ol>
          </div>
        )}

        {(topScorer || topAssist) && (
          <div>
            <h3 className="text-caption font-medium text-gray-400 mb-1">Moments forts</h3>
            <dl className="flex flex-col gap-1 text-data">
              {topScorer && <Highlight competitionId={competitionId} label="Meilleur buteur" row={topScorer} unit="buts" />}
              {topAssist && <Highlight competitionId={competitionId} label="Meilleur passeur" row={topAssist} unit="passes" />}
            </dl>
            <Link to={`/competition/${competitionId}/leaderboards`} className="inline-flex items-center min-h-11 md:min-h-8 text-data text-link">
              Voir les stats
            </Link>
          </div>
        )}
      </div>
    </motion.section>
  );
}

function Highlight({ competitionId, label, row, unit }) {
  return (
    <div className="flex items-baseline gap-2">
      <dt className="w-32 shrink-0 text-caption text-gray-500">{label}</dt>
      <dd className="min-w-0 truncate text-gray-100">
        <Link
          to={`/competition/${competitionId}/clubs/${encodeURIComponent(row.club)}/players/${encodeURIComponent(row.player)}`}
          className="font-medium hover:text-white"
        >
          {row.player}
        </Link>
        <span className="text-gray-400"> · {row.club} · </span>
        <span className="tabular-nums text-white">{row.count} {unit}</span>
      </dd>
    </div>
  );
}
