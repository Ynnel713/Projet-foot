import { useEffect } from "react";
import { motion } from "framer-motion";
import { Goal } from "lucide-react";
import ClubLogo from "../common/ClubLogo";
import { shortScorerName } from "../../utils/playerName";
import { scoreAt } from "../../utils/liveReplay";

const ALERT_MS = 5000;

function AlertToast({ alert, onDismiss }) {
  useEffect(() => {
    const t = setTimeout(() => onDismiss(alert.key), ALERT_MS);
    return () => clearTimeout(t);
  }, [alert.key, onDismiss]);

  return (
    <motion.div
      initial={{ opacity: 0, x: 24 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.22 }}
      className="flex items-center gap-1.5 rounded-lg bg-live-card/95 border border-live-border px-2 py-1.5 text-[12px] text-[#e2e8f0] shadow-lg shadow-black/40"
    >
      <Goal size={14} className="shrink-0 text-ev-goal" aria-hidden="true" />
      <span className="font-bold text-ev-goal shrink-0">BUT !</span>
      <ClubLogo clubName={alert.home} size={14} />
      <span className="tabular-nums font-semibold shrink-0">
        {alert.scoreHome}-{alert.scoreAway}
      </span>
      <ClubLogo clubName={alert.away} size={14} />
      <span className="truncate text-slate-300">
        {shortScorerName(alert.player)} {alert.minute}'
      </span>
    </motion.div>
  );
}

// Alertes « BUT ! » des AUTRES matchs de la journée pendant le live : petites, empilées (3 au plus), disparaissent seules après 5 s.
// Posées dans le flux de la colonne live (sous la barre de lecture), pas en calque : elles ne cachent ni le terrain ni les contrôles.
export function GoalAlerts({ alerts, onDismiss }) {
  return (
    <div className="shrink-0 flex flex-col gap-1.5 px-3 empty:hidden [&:not(:empty)]:pt-2" aria-live="polite">
      {alerts.map((a) => (
        <AlertToast key={a.key} alert={a} onDismiss={onDismiss} />
      ))}
    </div>
  );
}

// Ticker « multiplex » sous le terrain : score courant des autres matchs de la journée à l'horloge du live.
export function MultiplexTicker({ matches, clock }) {
  if (matches.length === 0) return null;
  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 text-[11px] text-slate-400" aria-label="Multiplex">
      <span className="font-bold uppercase tracking-wide text-slate-500">Multiplex</span>
      {matches.map((m) => {
        const s = scoreAt(m, clock);
        return (
          <span key={`${m.home}-${m.away}`} className="whitespace-nowrap tabular-nums">
            {m.home} <span className="font-semibold text-slate-200">{s.home}-{s.away}</span> {m.away}
            {s.lastMinute != null && <span className="text-slate-500"> ({s.lastMinute}')</span>}
          </span>
        );
      })}
    </div>
  );
}
