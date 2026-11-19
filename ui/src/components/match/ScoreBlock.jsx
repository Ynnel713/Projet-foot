import { memo } from "react";
import ClubCrest from "./ClubCrest";
import { hudName, scorerText } from "../../utils/matchHud";

// Identité du match (ticket v2-ecran-match/08, constantes validées par le propriétaire le 19/11/2026) : écusson, nom,
// score, nom, écusson. Score en Barlow Condensed 700 à 56 px (36 px sous 960 px de large ou 500 px de haut), noms à
// 20 px (16 px) en majuscules, espacés de 0,04 em, tronqués par « … » (noms longs).
const SMALL = "max-[959.98px]:text-[16px] [@media(max-height:499.98px)]:text-[16px]";

function ClubName({ club, align }) {
  return (
    <span
      title={club}
      className={`min-w-0 flex-1 truncate font-display font-bold uppercase tracking-[0.04em] text-[20px] leading-none text-white ${SMALL} ${align}`}
    >
      {club}
    </span>
  );
}

// Buteurs d'une équipe (ticket v2-ecran-match/08c, décisions du propriétaire du 19/11/2026) : un par ligne, 12 px, sous
// le nom du club et aligné sur lui (côté score), 3 lignes au plus (« +n autres », liste complète au survol) ; le nom se
// présente sans prénom et se tronque en premier (4,5 rem au moins), les minutes ensuite seulement ; rien sans
// but ; masqué sous 500 px de haut (même règle que la frise, EM-04).
const Scorers = memo(function Scorers({ side, list }) {
  if (!list.all.length) return <div data-scorers={side} />; // cellule vide : garde la grille alignée
  // aligné sous le nom (retrait de l'écusson) dès 1280 px ; en dessous, la place manque : aligné sur l'écusson
  const align = side === "home" ? "text-right min-[1280px]:pr-[54px]" : "text-left min-[1280px]:pl-[54px]";
  return (
    <ul
      data-scorers={side}
      title={list.all.map(scorerText).join("\n")}
      className={`min-w-0 self-start text-[12px] leading-[14px] text-gray-300 tabular-nums [@media(max-height:499.98px)]:hidden ${align}`}
    >
      {list.shown.map((row) => (
        <li key={`${row.name}-${row.ownGoal}`} className={`flex min-w-0 gap-1 ${side === "home" ? "justify-end" : "justify-start"}`}>
          <span className="min-w-[4.5rem] shrink-[1000] truncate">{hudName(row.name)}{row.ownGoal ? " (csc)" : ""}</span>
          <span className="min-w-0 truncate text-white">{row.minutes.join(", ")}</span>
        </li>
      ))}
      {list.hidden > 0 && <li className="truncate text-gray-400">+{list.hidden} autres</li>}
    </ul>
  );
});

export default function ScoreBlock({ home, away, score, scorers }) {
  return (
    <div
      className="grid min-w-0 grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-x-2.5 max-[959.98px]:gap-x-1.5"
      aria-label={`${home} ${score.home}, ${away} ${score.away}`}
    >
      <div className="flex min-w-0 flex-1 items-center justify-end gap-2.5 max-[959.98px]:gap-1.5">
        <ClubName club={home} align="text-right" />
        <ClubCrest club={home} side="home" />
      </div>
      <div
        data-zone="score"
        className="shrink-0 px-1 font-display font-bold tabular-nums leading-none text-white text-[56px] max-[959.98px]:text-[36px] [@media(max-height:499.98px)]:text-[36px]"
      >
        {score.home}
        <span className="mx-1.5 text-gray-500">-</span>
        {score.away}
      </div>
      <div className="flex min-w-0 flex-1 items-center gap-2.5 max-[959.98px]:gap-1.5">
        <ClubCrest club={away} side="away" />
        <ClubName club={away} align="text-left" />
      </div>
      {scorers && (scorers.home.all.length > 0 || scorers.away.all.length > 0) && (
        <>
          <Scorers side="home" list={scorers.home} />
          <div />
          <Scorers side="away" list={scorers.away} />
        </>
      )}
    </div>
  );
}
