import TeamLink from "../common/TeamLink";
import { roundTitle } from "../../utils/bracketLabels";

// Arbre des phases finales (refonte UI, lot 6), bureau seulement : une colonne par tour, cartes compactes (club + score cumulé, vainqueur
// en blanc gras), petits traits de liaison d'une colonne à la suivante. Cliquer l'en-tête d'une colonne ou une confrontation sélectionne
// le tour : son détail s'affiche à côté (manches, feuille de match, tirs au but). Le tour courant est repéré en bleu (`link`).
export default function BracketTree({ rounds, selectedNumber, currentNumber, onSelect }) {
  return (
    <div className="flex gap-6 min-w-max h-full" role="group" aria-label="Arbre des phases finales">
      {rounds.map((round, col) => (
        <div key={round.number} className="w-52 shrink-0 flex flex-col gap-2">
          <button
            onClick={() => onSelect(round.number)}
            aria-pressed={round.number === selectedNumber}
            className={`h-8 shrink-0 text-left text-data font-semibold border-b-2 ${
              round.number === currentNumber ? "text-link" : "text-gray-300"
            } ${round.number === selectedNumber ? "border-accent" : "border-line"}`}
          >
            {roundTitle(round)}
          </button>
          <div className="flex-1 flex flex-col justify-around gap-2">
            {round.ties.map((tie) => (
              <CompactTie
                key={`${tie.home}-${tie.away ?? "bye"}`}
                tie={tie}
                first={col === 0}
                last={col === rounds.length - 1}
                onSelect={() => onSelect(round.number)}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function CompactTie({ tie, first, last, onSelect }) {
  const tone = (club) => (tie.winner ? (tie.winner === club ? "text-white font-semibold" : "text-gray-400") : "text-gray-100");
  const rows = tie.is_bye ? [[tie.home, null]] : [[tie.home, tie.home_goals], [tie.away, tie.away_goals]];
  const link = "absolute top-1/2 w-3 h-px bg-gray-700";

  return (
    <div onClick={onSelect} className="relative rounded-lg bg-surface border border-line px-2 py-1 cursor-pointer hover:bg-surface-2">
      {!first && <span className={`${link} right-full`} aria-hidden="true" />}
      {!last && <span className={`${link} left-full`} aria-hidden="true" />}
      {rows.map(([club, goals]) => (
        <div key={club} className="flex items-center gap-2 h-6 text-data">
          <TeamLink name={club} logoSize={16} stopPropagation className={`min-w-0 ${tone(club)}`} />
          <span className={`ml-auto tabular-nums ${tone(club)}`}>{goals ?? ""}</span>
        </div>
      ))}
      {tie.is_bye && <div className="text-caption text-gray-500">Exempt</div>}
      {tie.decided_by_penalties && tie.penalty_score && (
        <div className="text-caption text-gray-500">tab {tie.penalty_score[0]}-{tie.penalty_score[1]}</div>
      )}
    </div>
  );
}
