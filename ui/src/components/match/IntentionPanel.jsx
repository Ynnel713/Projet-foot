import { memo } from "react";
import { clock } from "./trace";

// Situation perçue : celle de son équipe, mais l'ancienne tant que son délai de réaction n'est pas écoulé.
function perceivedSituation(trace, team, minute, delayS) {
  const changes = (trace.situations || []).filter((s) => s.team === team && s.minute <= minute);
  const last = changes.at(-1);
  if (last && (minute - last.minute) * 60 < delayS && changes.length > 1) return changes.at(-2).situation;
  return last?.situation || "";
}

// Intention du joueur sélectionné à l'instant lu : dernier segment commencé avant `tick.minute` (la trace n'envoie
// un segment qu'au changement de rôle ou d'action), et dernière décision prise s'il a eu le ballon.
// Sans joueur sélectionné, `tick` peut être nul : le panneau ne se redessine pas à chaque image (ticket
// v2-ecran-match/01).
function IntentionPanel({ trace, tick, selected }) {
  if (!selected) {
    return <p className="text-center text-data text-gray-500">Touchez un joueur pour voir ce qu'il cherche à faire.</p>;
  }
  // intentions et décisions n'arrivent qu'une fois le calcul fini
  const player = tick.players.find((p) => p.name === selected);
  const intentions = (trace.intentions || []).find((i) => i.player === selected);
  const segments = intentions?.segments || [];
  const current = segments.filter((s) => s.minute <= tick.minute).at(-1);
  const decision = (trace.decisions || []).filter((d) => d.player === selected && d.minute <= tick.minute).at(-1);
  const ACTIONS = { pass: "passe", dribble: "conduite", shot: "tir" };
  return (
    <div className="rounded-lg bg-surface px-3 py-2 text-sm text-gray-200">
      <div className="font-semibold text-white">
        {selected} {player && <span className="text-data text-gray-400">({player.poste})</span>}
      </div>
      {player && (
        <div className="text-data text-gray-400">
          Situation perçue : {perceivedSituation(trace, player.team, tick.minute, intentions?.reaction_delay_s || 0)}
        </div>
      )}
      {current ? (
        <div>
          <span className="text-accent">{current.role}</span> : {current.action}
          {current.mate ? ` (${current.mate})` : ""} — {current.reason}
        </div>
      ) : (
        <div className="text-gray-500">
          {trace.done ? "Pas encore d'intention enregistrée." : "Intentions disponibles à la fin du calcul du match."}
        </div>
      )}
      {decision && (
        <div className="text-data text-gray-400">
          Dernière décision ({clock(trace, decision.minute).label}) : {ACTIONS[decision.action] || decision.action}
          {decision.target ? ` vers ${decision.target}` : ""}, {decision.considered} option(s) envisagée(s)
          {decision.best_kind ? "" : decision.best ? ", la meilleure" : ", pas la meilleure"}
          {decision.best_kind && (
            <div>
              Meilleur choix : {ACTIONS[decision.best_kind] || decision.best_kind}. Choisi :{" "}
              {ACTIONS[decision.action] || decision.action}
              {decision.gap > 0 ? ` (${errorLabel(decision.gap)})` : ""}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Écart de valeur avec le meilleur choix factuel, en part de celui-ci (ticket v2-collectif/33).
function errorLabel(gap) {
  // sous 10 % : erreur légère, comptée comme le meilleur choix (BEST_CHOICE_TOLERANCE, texte du ticket)
  if (gap < 0.1) return "erreur légère";
  return gap < 0.4 ? "erreur nette" : "erreur lourde";
}

export default memo(IntentionPanel);
