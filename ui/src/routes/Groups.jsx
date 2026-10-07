import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, LoaderCircle } from "lucide-react";
import { getGroups, simulateGroupsMatchday, startKnockout } from "../api/client";
import { shortScorerName } from "../utils/playerName";
import TeamLink from "../components/common/TeamLink";
import LiveButton from "../components/common/LiveButton";

export default function Groups() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [launching, setLaunching] = useState(false); // « Lancement du live… » : simulation de la journée avant le premier live
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    getGroups(id)
      .then(setData)
      .catch(() => setError("Compétition introuvable."));
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleSimulate() {
    setLoading(true);
    try {
      setData(await simulateGroupsMatchday(id));
    } finally {
      setLoading(false);
    }
  }

  async function handleStartKnockout() {
    setLoading(true);
    try {
      await startKnockout(id);
      navigate(`/competition/${id}/bracket`);
    } finally {
      setLoading(false);
    }
  }

  // Live d'un match de poule / de phase de ligue, quelle que soit la compétition (Coupe du Monde, Ligue des Champions, perso). Match déjà joué :
  // on rouvre son live. Pas encore joué : on simule la journée (toutes les poules d'un bloc : le moteur n'a qu'un compteur de journée),
  // puis on ouvre le live de CE match. `replay=1` : le live part de la minute 0.
  async function openLive(group, match, played) {
    let matchday = data.groups_matchday - 1;
    if (!played) {
      setLaunching(true);
      try {
        const next = await simulateGroupsMatchday(id);
        setData(next);
        matchday = next.groups_matchday - 1;
      } catch {
        setLaunching(false);
        return;
      }
      setLaunching(false);
    }
    navigate(
      `/competition/${id}/pitch?${new URLSearchParams({
        home: match.home,
        away: match.away,
        group: group.name,
        matchday,
        tab: "live",
        replay: "1",
      })}`,
    );
  }

  if (error) return <div className="p-6 text-sm text-gray-400">{error}</div>;
  if (!data) return <div className="p-6 text-sm text-gray-400">Chargement…</div>;

  // Journée qui vient d'être jouée -- `matchday` (0-indexé) passé à la vue
  // terrain est `groups_matchday - 1` (voir ci-dessous), donc le libellé
  // humain "Journée N" est directement `groups_matchday` (même convention
  // que PitchView : `matchday + 1`).
  const lastPlayedJournee = data.groups_matchday;
  const leaguePhase = data.league_phase;

  function openMatch(g, m) {
    navigate(
      `/competition/${id}/pitch?${new URLSearchParams({
        home: m.home,
        away: m.away,
        group: g.name,
        matchday: data.groups_matchday - 1,
      })}`,
    );
  }

  return (
    <div className="flex flex-col h-full">
      <button onClick={() => navigate(-1)} className="flex items-center gap-1 text-xs text-gray-400 self-start px-3 pt-3 shrink-0">
        <ArrowLeft size={14} /> Retour
      </button>
      {/* items-start : sans ça, une grille CSS étire chaque carte à la
          hauteur de la plus grande de sa ligne -- en J0 (aucun match joué),
          les cartes vides se retrouvaient artificiellement aussi hautes que
          leurs voisines déjà jouées, ~70% de vide (retour audit UX du
          28/09/2026). Chaque carte garde maintenant sa hauteur naturelle.
          Phase de ligue de la Ligue des Champions : UNE seule carte (36 clubs), pleine largeur. */}
      <div className={`flex-1 min-h-0 overflow-y-auto p-3 grid gap-2 items-start ${leaguePhase ? "grid-cols-1" : "grid-cols-3"}`}>
        {data.groups.map((g) => (
          <GroupCard
            key={g.name}
            group={g}
            journee={lastPlayedJournee}
            data={data}
            onMatchClick={(m) => openMatch(g, m)}
            onLive={(m, played) => openLive(g, m, played)}
          />
        ))}
      </div>

      <div className="shrink-0 p-3 border-t border-white/5">
        {data.groups_complete ? (
          <button
            onClick={handleStartKnockout}
            disabled={loading}
            className="w-full h-12 rounded-xl bg-gold text-bg font-semibold disabled:opacity-40"
          >
            {loading ? "…" : leaguePhase ? "🏆 Lancer les barrages →" : "🏆 Lancer les phases finales →"}
          </button>
        ) : (
          <button
            onClick={handleSimulate}
            disabled={loading}
            className="w-full h-12 rounded-xl bg-accent text-white font-semibold disabled:opacity-40"
          >
            {loading ? "…" : leaguePhase ? `Simuler la journée ${data.groups_matchday + 1}` : "Simuler la journée des poules"}
          </button>
        )}
      </div>

      {launching && (
        <div role="status" className="fixed inset-0 z-50 flex flex-col items-center justify-center gap-3 bg-black/70 backdrop-blur-sm">
          <LoaderCircle size={36} className="animate-spin text-live" />
          <span className="text-sm font-semibold text-slate-100">Lancement du live...</span>
        </div>
      )}
    </div>
  );
}

// Mêmes teintes que MiniStandings (classement condensé des championnats
// nationaux) -- vert/gris/rouge comme code couleur "bon/neutre/mauvais"
// pour les résultats et buts, réutilisées ici pour que le classement de
// poule ait le même vocabulaire visuel (retour terrain du 29/09/2026 :
// "rajoute au classement les mêmes choses que pour les championnats
// nationaux").
const GOOD = "#3ddc70";
const NEUTRAL = "#9ca3af";
const BAD = "#e0645a";

// Zone de qualification d'une ligne du classement : poules classiques = 2 premiers (vert) ; phase de ligue de la Ligue des Champions =
// 8 premiers directs en 8es (vert), 9e-24e en barrages (ambre), derniers éliminés (rouge). Signal de couleur ADDITIONNEL au rang, pas le
// seul (accessible daltonisme : la bordure gauche et la légende nomment la zone).
function zoneOf(index, data) {
  if (data.league_phase) {
    if (index < data.direct_spots) return "direct";
    if (index < data.direct_spots + data.playoff_spots) return "playoff";
    return "out";
  }
  return index < 2 ? "direct" : null;
}

const ZONE_STYLE = {
  direct: { row: "bg-emerald-500/5", border: "border-emerald-500" },
  playoff: { row: "bg-amber-400/5", border: "border-amber-400" },
  out: { row: "bg-red-500/5", border: "border-red-500/70" },
};

function GroupCard({ group: g, journee, data, onMatchClick, onLive }) {
  const wide = data.league_phase;
  const half = Math.ceil(g.standings.length / 2);
  return (
    <div className="bg-surface rounded-lg p-2.5">
      <div className="flex items-center justify-between mb-1.5">
        <h3 className={`font-semibold text-gray-300 ${wide ? "text-sm" : "text-xs"}`}>{g.name}</h3>
        {g.is_complete && <span className="text-[10px] text-emerald-400">Terminée</span>}
      </div>

      {wide ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-6 gap-y-2">
          <StandingsPart rows={g.standings.slice(0, half)} start={0} data={data} wide />
          <StandingsPart rows={g.standings.slice(half)} start={half} data={data} wide />
        </div>
      ) : (
        <StandingsPart rows={g.standings} start={0} data={data} wide={false} />
      )}

      {wide && (
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2 text-[10px] text-gray-400">
          <Legend color="bg-emerald-500" label={`1er-${data.direct_spots}e : 8es de finale`} />
          <Legend color="bg-amber-400" label={`${data.direct_spots + 1}e-${data.direct_spots + data.playoff_spots}e : barrages`} />
          <Legend color="bg-red-500/70" label={`${data.direct_spots + data.playoff_spots + 1}e et au-delà : éliminés`} />
        </div>
      )}

      {/* Résultats de la dernière journée jouée -- pas tout l'historique (trop
          dense sur 8 poules à la fois), juste ce qui vient de se jouer.
          Grille à 5 colonnes (buteurs / pays / score / pays / buteurs), même
          principe que MatchRow (journée d'un championnat) : score au centre,
          pays immédiatement de part et d'autre, buteurs aux extrémités
          (retour terrain du 29/09/2026). Chaque ligne a son bouton LIVE. */}
      {g.current_matches.length > 0 && (
        <div className="mt-2 pt-2 border-t border-white/10">
          <div className="text-[10px] uppercase tracking-wide text-gray-500 mb-1.5">Journée {journee} · Résultats</div>
          <div className={`grid gap-x-6 gap-y-1 ${wide ? "grid-cols-1 xl:grid-cols-2" : "grid-cols-1"}`}>
            {g.current_matches.map((m) => (
              <GroupMatchRow key={`${m.home}-${m.away}`} match={m} played onClick={() => onMatchClick(m)} onLive={() => onLive(m, true)} />
            ))}
          </div>
        </div>
      )}
      {g.next_matches?.length > 0 ? (
        <div className="mt-2 pt-2 border-t border-white/10">
          <div className="text-[10px] uppercase tracking-wide text-gray-500 mb-1.5">
            Journée {journee + 1} · À venir <span className="normal-case tracking-normal text-gray-600">(LIVE simule la journée puis ouvre le match)</span>
          </div>
          <div className={`grid gap-x-6 gap-y-1 ${wide ? "grid-cols-1 xl:grid-cols-2" : "grid-cols-1"}`}>
            {g.next_matches.map((m) => (
              <GroupMatchRow key={`${m.home}-${m.away}`} match={m} played={false} onLive={() => onLive(m, false)} />
            ))}
          </div>
        </div>
      ) : (
        g.current_matches.length === 0 && (
          <p className="mt-2 pt-2 border-t border-white/10 text-[11px] text-gray-500">Aucun match joué &ndash; Journée 1 à venir</p>
        )
      )}
    </div>
  );
}

function StandingsPart({ rows, start, data, wide }) {
  return (
    <table className="w-full text-[12px] border-collapse table-fixed">
      <thead>
        <tr className="text-gray-500 text-[10px]">
          <th className="text-left font-medium pb-1 w-6">#</th>
          <th className="text-left font-medium pb-1">{wide ? "Club" : "Pays"}</th>
          <th className="text-center font-medium pb-1 w-5">J</th>
          <th className="text-center font-medium pb-1 w-5">V</th>
          <th className="text-center font-medium pb-1 w-5">N</th>
          <th className="text-center font-medium pb-1 w-5">D</th>
          <th className="text-center font-medium pb-1 w-6">BP</th>
          <th className="text-center font-medium pb-1 w-6">BC</th>
          <th className="text-center font-medium pb-1 w-7">Diff</th>
          <th className="text-center font-semibold pb-1 w-6">Pts</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row, k) => {
          const zone = zoneOf(start + k, data);
          const style = zone ? ZONE_STYLE[zone] : null;
          return (
            <tr key={row.club} className={style?.row ?? ""}>
              <td className={`py-1 ${style ? `border-l-2 ${style.border}` : "border-l-2 border-transparent"} pl-1`}>
                <span className="text-gray-500">{row.rank}</span>
              </td>
              <td className="py-1 max-w-0">
                <TeamLink name={row.club} className="text-[12px] font-medium" />
              </td>
              <td className="text-center tabular-nums text-gray-500">{row.played}</td>
              <td className="text-center tabular-nums" style={{ color: GOOD }}>
                {row.won}
              </td>
              <td className="text-center tabular-nums" style={{ color: NEUTRAL }}>
                {row.drawn}
              </td>
              <td className="text-center tabular-nums" style={{ color: BAD }}>
                {row.lost}
              </td>
              <td className="text-center tabular-nums" style={{ color: GOOD }}>
                {row.goals_for}
              </td>
              <td className="text-center tabular-nums" style={{ color: BAD }}>
                {row.goals_against}
              </td>
              <td className="text-center tabular-nums" style={{ color: row.goal_diff > 0 ? GOOD : row.goal_diff < 0 ? BAD : NEUTRAL }}>
                {row.goal_diff > 0 ? `+${row.goal_diff}` : row.goal_diff}
              </td>
              <td className="text-center tabular-nums font-bold text-white">{row.points}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

function Legend({ color, label }) {
  return (
    <span className="flex items-center gap-1.5">
      <span className={`h-2.5 w-1 rounded-sm ${color}`} aria-hidden="true" />
      {label}
    </span>
  );
}

function _scorersText(scorers, club) {
  if (!scorers) return "";
  return scorers
    .filter((s) => s.club === club)
    .map((s) => `${shortScorerName(s.player)} ${s.minute}'`)
    .join(", ");
}

function GroupMatchRow({ match: m, played, onClick, onLive }) {
  const homeScorers = _scorersText(m.scorers, m.home);
  const awayScorers = _scorersText(m.scorers, m.away);

  return (
    // div + role="button" plutôt qu'un <button> : les noms de sélection à
    // l'intérieur (TeamLink) sont eux-mêmes des <button>, imbriquer un
    // bouton dans un bouton est invalide en HTML et casse le clic.
    <div
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
      onClick={onClick}
      className={`text-left rounded px-1 py-0.5 ${onClick ? "cursor-pointer hover:bg-white/5" : ""}`}
    >
      <div className="grid grid-cols-[1fr_1fr_2.25rem_1fr_1fr_auto] items-center gap-1">
        <span className="text-[8px] text-gray-500 truncate justify-self-start">{homeScorers}</span>
        <TeamLink name={m.home} stopPropagation className="justify-self-end text-[11px]" />
        <span className="font-bold text-[13px] tabular-nums text-center text-gray-100">
          {played ? `${m.home_goals} - ${m.away_goals}` : "– –"}
        </span>
        <TeamLink name={m.away} stopPropagation align="end" className="justify-self-start text-[11px]" />
        <span className="text-[8px] text-gray-500 truncate justify-self-end text-right">{awayScorers}</span>
        <LiveButton played={played} onLive={onLive} compact />
      </div>
    </div>
  );
}
