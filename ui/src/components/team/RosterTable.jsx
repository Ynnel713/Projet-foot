import { useNavigate, useParams } from "react-router-dom";
import { BASE_URL } from "../../api/client";
import { fmTierColor } from "../../utils/fmTier";

// Effectif en tableau (refonte UI, lot 5), groupé par ligne puis trié par note décroissante. Bureau : Joueur · Poste · Âge · Pied · Note ;
// mobile : Joueur · Poste · Note. Lignes de 36 px au doigt, 32 px sur bureau. Le nom ouvre la fiche du joueur.
const LINES = [
  { label: "Gardiens", postes: ["GK"] },
  { label: "Défenseurs", postes: ["DC", "LB", "RB"] },
  { label: "Milieux", postes: ["MDC", "MC", "MOC"] },
  { label: "Attaquants", postes: ["AG", "AD", "SA", "BU", "ATT"] },
];
const PIED_LABELS = { D: "Droit", G: "Gauche" };

function groupByLine(players) {
  const known = LINES.flatMap((l) => l.postes);
  const lines = LINES.map((l) => ({ label: l.label, players: players.filter((p) => l.postes.includes(p.poste)) }));
  const others = players.filter((p) => !known.includes(p.poste));
  if (others.length) lines.push({ label: "Autres", players: others });
  return lines.filter((l) => l.players.length).map((l) => ({ ...l, players: [...l.players].sort((a, b) => b.note - a.note) }));
}

export default function RosterTable({ players, club }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const open = (player) => navigate(`/competition/${id}/clubs/${encodeURIComponent(club)}/players/${encodeURIComponent(player.name)}`);
  const head = "h-6 text-caption font-medium text-gray-500";

  return (
    <div className="rounded-xl bg-surface border border-line overflow-hidden">
      <table className="w-full border-collapse table-fixed text-data">
        <thead>
          <tr>
            <th className={`${head} text-left pl-3`}>Joueur</th>
            <th className={`${head} w-14 text-center`}>Poste</th>
            <th className={`${head} w-12 text-center hidden sm:table-cell`}>Âge</th>
            <th className={`${head} w-16 text-center hidden sm:table-cell`}>Pied</th>
            <th className={`${head} w-14 text-center pr-2`}>Note</th>
          </tr>
        </thead>
        {groupByLine(players).map((line) => (
          <tbody key={line.label}>
            <tr>
              <th colSpan={5} className="h-6 bg-surface-2 text-left pl-3 text-caption font-medium text-gray-400">
                {line.label} · {line.players.length}
              </th>
            </tr>
            {line.players.map((player) => (
              <tr key={player.id ?? player.name} className="h-9 md:h-8 border-t border-line text-gray-300">
                <td className="max-w-0 pl-3">
                  <button onClick={() => open(player)} className="flex items-center gap-2 w-full min-w-0 h-9 md:h-8 text-left text-gray-100 font-medium hover:text-white">
                    {player.photo_url ? (
                      <img src={`${BASE_URL}${player.photo_url}`} alt="" className="h-6 w-6 rounded-md object-cover shrink-0" />
                    ) : (
                      <span className="h-6 w-6 rounded-md bg-surface-3 shrink-0" aria-hidden="true" />
                    )}
                    <span className="truncate">{player.name}</span>
                  </button>
                </td>
                <td className="text-center tabular-nums text-gray-400">{player.poste}</td>
                <td className="text-center tabular-nums hidden sm:table-cell">{player.age}</td>
                <td className="text-center hidden sm:table-cell">{PIED_LABELS[player.pied] ?? "–"}</td>
                <td className="text-center pr-2">
                  <span
                    className="inline-flex min-w-7 h-5 px-1 items-center justify-center rounded-md text-caption font-bold tabular-nums text-white"
                    style={{ backgroundColor: fmTierColor(player.note) }}
                  >
                    {player.note.toFixed(0)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        ))}
      </table>
    </div>
  );
}
