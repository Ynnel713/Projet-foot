import { motion } from "framer-motion";
import LiveButton from "../common/LiveButton";
import ClubLink from "../common/ClubLink";
import { shortScorerName } from "../../utils/playerName";

function scorersText(scorers, club) {
  if (!scorers) return "";
  return scorers
    .filter((s) => s.club === club)
    .map((s) => `${shortScorerName(s.player)} ${s.minute}'`)
    .join(", ");
}

export default function MatchRow({ match, onClick, onLive }) {
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
  const homeScorers = scorersText(match.scorers, match.home);
  const awayScorers = scorersText(match.scorers, match.away);

  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      onClick={clickable ? onClick : undefined}
      className={`bg-surface rounded-lg px-3.5 py-3.5 border-l-4 min-h-[58px] flex items-center ${border} ${
        clickable ? "cursor-pointer active:scale-[0.99] transition-transform" : ""
      }`}
    >
      {/* Grille à 5 colonnes (buteur / nom / score / nom / buteur) --
          buteurs et noms sur la même ligne (assez de place une fois les
          noms/logos centrés autour du score, retour terrain du 28/09/2026).
          Les 2 colonnes de noms et la colonne du score ont une largeur
          fixe/proportionnelle identique sur toutes les lignes, donc le
          score reste aligné verticalement d'une ligne à l'autre quelle que
          soit la longueur des noms ou des buteurs de chaque côté. Police et
          hauteur de ligne agrandies (28/09/2026) pour que la liste des
          matchs (moitié moins de lignes que le classement, 9 vs 18 en Ligue
          1) atteigne la même hauteur totale que le classement à côté --
          repère approximatif basé sur un championnat à 18-20 clubs, pas un
          calcul pixel-perfect valable pour tout effectif. */}
      <div className="grid grid-cols-[1fr_1fr_3.5rem_1fr_1fr_auto] items-center gap-3 w-full">
        <span className="text-[11px] text-gray-500 truncate justify-self-start">{homeScorers}</span>
        <ClubLink name={match.home} stopPropagation logoSize={22} className="justify-self-end text-base" />
        <span className="font-bold text-xl tabular-nums text-center">
          {notPlayed ? "– –" : `${match.home_goals} - ${match.away_goals}`}
        </span>
        <ClubLink name={match.away} stopPropagation align="end" logoSize={22} className="justify-self-start text-base" />
        <span className="text-[11px] text-gray-500 truncate justify-self-end text-right">{awayScorers}</span>
        {onLive && <LiveButton played={!notPlayed} onLive={onLive} />}
      </div>
    </motion.div>
  );
}
