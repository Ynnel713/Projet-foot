import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getStandings } from "../api/client";
import StandingsTable from "../components/standings/StandingsTable";

export default function Standings() {
  const { id } = useParams();
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getStandings(id)
      .then(setRows)
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="p-6 text-sm text-gray-400">Chargement…</div>;
  if (rows.length === 0) return <div className="p-6 text-sm text-gray-400">Aucun classement disponible.</div>;

  return (
    <div className="p-3">
      <StandingsTable rows={rows} />
    </div>
  );
}
