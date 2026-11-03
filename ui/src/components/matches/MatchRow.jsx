import { Fragment } from "react";
import { useNavigate, useParams } from "react-router-dom";
import TeamLink from "../common/TeamLink";
import LiveButton from "../common/LiveButton";
import AnimationButton from "../common/AnimationButton";
import { shortScorerName } from "../../utils/playerName";
import { LIVE_AND_ANIMATION_ENABLED } from "../../config/features";

// Ligne de match unique de l'app (refonte UI, lot 3) : championnat, poules / phase de ligue, phases finales.
// Chaque zone mène à un seul endroit : le SCORE ouvre la feuille de match, un CLUB sa page, un BUTEUR sa fiche joueur.
// La ligne elle-même n'est pas cliquable. Un match non joué affiche « – – », non cliquable.
// Mise en page selon la largeur DISPONIBLE de la ligne (container query, pas celle de l'écran : la colonne de droite de la
// phase de ligue est étroite sur un grand écran) : étroit = deux lignes (clubs et score, buteurs dessous) ; large (>= 36 rem) = une
// seule ligne `buteurs · club · score · club · buteurs`.
// `winner` : nom du vainqueur imposé (confrontation décidée aux tirs au but) ; sinon déduit du score. Le vainqueur est en blanc
// et en gras, l'autre en gris, rien en cas de nul.
export default function MatchRow({ match: m, winner, onOpenSheet, onLive, onAnimation }) {
  const played = m.played !== false && m.home_goals != null && m.away_goals != null;
  const won = winner ?? (played && m.home_goals !== m.away_goals ? (m.home_goals > m.away_goals ? m.home : m.away) : null);
  const tone = (club) => (won ? (won === club ? "text-white font-semibold" : "text-gray-400") : "text-gray-100");
  const buttons = LIVE_AND_ANIMATION_ENABLED && (onLive || (onAnimation && played));
  const grid = buttons
    ? "grid-cols-[minmax(0,1fr)_3.5rem_minmax(0,1fr)_auto] @xl:grid-cols-[minmax(0,1fr)_minmax(0,1.3fr)_3.5rem_minmax(0,1.3fr)_minmax(0,1fr)_auto]"
    : "grid-cols-[minmax(0,1fr)_3.5rem_minmax(0,1fr)] @xl:grid-cols-[minmax(0,1fr)_minmax(0,1.3fr)_3.5rem_minmax(0,1.3fr)_minmax(0,1fr)]";

  return (
    <div className="@container px-3 py-1.5 md:py-1 border-t border-line first:border-t-0">
      <div className={`grid ${grid} items-center gap-x-2 gap-y-0.5`}>
        <TeamLink
          name={m.home}
          align="end"
          className={`col-start-1 row-start-1 @xl:col-start-2 justify-self-end max-w-full min-h-11 md:min-h-0 text-data ${tone(m.home)}`}
        />
        {played ? (
          onOpenSheet ? (
            <button
              onClick={onOpenSheet}
              aria-label={`Feuille de match : ${m.home} ${m.home_goals} - ${m.away_goals} ${m.away}`}
              className="col-start-2 row-start-1 @xl:col-start-3 min-h-11 md:min-h-7 rounded-lg bg-surface-2 hover:bg-surface-3 font-display font-bold text-xl leading-none tabular-nums text-white"
            >
              {m.home_goals} - {m.away_goals}
            </button>
          ) : (
            <span className="col-start-2 row-start-1 @xl:col-start-3 text-center font-display font-bold text-xl tabular-nums text-white">
              {m.home_goals} - {m.away_goals}
            </span>
          )
        ) : (
          <span className="col-start-2 row-start-1 @xl:col-start-3 text-center font-display font-bold text-xl text-gray-500">– –</span>
        )}
        <TeamLink name={m.away} className={`col-start-3 row-start-1 @xl:col-start-4 justify-self-start max-w-full min-h-11 md:min-h-0 text-data ${tone(m.away)}`} />

        <Scorers
          scorers={m.scorers}
          club={m.home}
          className="col-start-1 row-start-2 @xl:col-start-1 @xl:row-start-1 justify-self-end @xl:justify-self-start text-right @xl:text-left"
        />
        <Scorers
          scorers={m.scorers}
          club={m.away}
          className="col-start-3 row-start-2 @xl:col-start-5 @xl:row-start-1 justify-self-start @xl:justify-self-end text-left @xl:text-right"
        />

        {buttons && (
          <div className="col-start-4 row-start-1 row-span-2 @xl:col-start-6 @xl:row-span-1 flex items-center gap-1.5">
            {onAnimation && played && <AnimationButton onAnimation={onAnimation} />}
            {onLive && <LiveButton played={played} onLive={onLive} />}
          </div>
        )}
      </div>
    </div>
  );
}

// Buteurs d'un club : chaque nom ouvre la fiche du joueur (nom complet dans l'URL, nom abrégé à l'affichage). Cible de 32 px
// de haut sur mobile (texte courant, compromis validé : plus haut gonflerait toutes les lignes de match).
function Scorers({ scorers, club, className }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const list = (scorers ?? []).filter((s) => s.club === club);
  if (list.length === 0) return null;
  return (
    <span className={`min-w-0 max-w-full truncate text-caption text-gray-400 ${className}`} title={list.map((s) => `${s.player} ${s.minute}'`).join(", ")}>
      {list.map((s, i) => (
        <Fragment key={`${s.player}-${s.minute}-${i}`}>
          {i > 0 && ", "}
          <button
            onClick={() => navigate(`/competition/${id}/clubs/${encodeURIComponent(club)}/players/${encodeURIComponent(s.player)}`)}
            className="inline-flex items-center min-h-8 md:min-h-0 hover:text-link hover:underline"
          >
            {shortScorerName(s.player)} {s.minute}'
          </button>
        </Fragment>
      ))}
    </span>
  );
}
