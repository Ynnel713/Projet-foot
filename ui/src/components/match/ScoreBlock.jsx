import ClubCrest from "./ClubCrest";

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

export default function ScoreBlock({ home, away, score }) {
  return (
    <div className="flex min-w-0 items-center gap-2.5 max-[959.98px]:gap-1.5" aria-label={`${home} ${score.home}, ${away} ${score.away}`}>
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
    </div>
  );
}
