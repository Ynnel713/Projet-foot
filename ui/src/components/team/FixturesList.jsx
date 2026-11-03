import { useNavigate, useParams } from "react-router-dom";
import TeamLink from "../common/TeamLink";

// Calendrier d'un club en championnat (refonte UI, lot 5) : une ligne par match, la journée courante repérée. Le score d'un match joué
// ouvre sa feuille de match (comme dans la boucle centrale, lot 3) ; un match à venir affiche « – – » sans bouton. Le score suit
// l'ordre réel du match (domicile d'abord) ; la lettre V / N / D donne le résultat du club.
const RESULT = {
  W: { letter: "V", label: "Victoire", tone: "text-win" },
  D: { letter: "N", label: "Match nul", tone: "text-draw" },
  L: { letter: "D", label: "Défaite", tone: "text-loss" },
};

export default function FixturesList({ fixtures }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const openSheet = (f) => navigate(`/competition/${id}/pitch?${new URLSearchParams({ home: f.home, away: f.away, journee: f.journee })}`);

  return (
    <ul className="rounded-xl bg-surface border border-line overflow-hidden">
      {fixtures.fixtures.map((f) => {
        const current = f.journee === fixtures.current_journee;
        const result = f.result ? RESULT[f.result] : null;
        return (
          <li
            key={`${f.journee}-${f.home}-${f.away}`}
            aria-current={current ? "true" : undefined}
            className={`grid grid-cols-[2.5rem_minmax(0,1fr)_1.25rem_4.5rem_1.25rem] items-center gap-2 px-3 h-11 md:h-9 border-t border-line first:border-t-0 text-data ${
              current ? "bg-surface-2" : ""
            }`}
          >
            <span className="text-caption text-gray-500 tabular-nums">J{f.journee}</span>
            <TeamLink name={f.opponent} className="min-w-0 min-h-11 md:min-h-0 text-gray-100" />
            <span className="text-caption text-gray-500 text-center" title={f.home_away === "home" ? "Domicile" : "Extérieur"}>
              {f.home_away === "home" ? "D" : "E"}
            </span>
            {f.played ? (
              <button
                onClick={() => openSheet(f)}
                aria-label={`Feuille de match, journée ${f.journee}`}
                className="h-11 md:h-9 font-display font-bold text-lg tabular-nums text-white text-center hover:text-link"
              >
                {f.home_goals} - {f.away_goals}
              </button>
            ) : (
              <span className="text-center font-display text-lg text-gray-500" aria-label="Pas encore joué">
                – –
              </span>
            )}
            <span className={`text-caption font-bold text-center ${result?.tone ?? ""}`} aria-label={result?.label}>
              {result?.letter ?? ""}
            </span>
          </li>
        );
      })}
    </ul>
  );
}
