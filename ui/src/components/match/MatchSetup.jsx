import { ArrowLeft, LoaderCircle } from "lucide-react";

// Écran de réglage de la V2 : choix des deux clubs et lancement (ticket v2-ecran-match/01 : séparé de l'écran de
// lecture). `progress` : part du tampon de démarrage déjà calculée (%), ou null.
export default function MatchSetup({ clubs, home, away, onHome, onAway, error, launching, progress, onLaunch, onBack }) {
  return (
    <div className="p-4 sm:p-6 max-w-xl mx-auto flex flex-col gap-4">
      <button onClick={onBack} className="flex items-center gap-1 min-h-11 text-data text-gray-400 self-start">
        <ArrowLeft size={14} /> Retour
      </button>
      <h1 className="text-2xl font-extrabold text-white">⚽ Version 2 (bêta)</h1>
      <p className="text-sm text-gray-400">
        Moteur physique piloté par les attributs réels des joueurs : l'issue n'est pas décidée à l'avance, elle
        émerge de la simulation. Le match se calcule pendant que tu le regardes : il démarre après quelques secondes.
      </p>

      {clubs.length === 0 && !error ? (
        // Premier appel après démarrage de l'API : lecture du fichier joueurs, ~15 s mesurées (24/10/2026).
        <p className="flex items-center gap-2 text-sm text-gray-400">
          <LoaderCircle size={16} className="animate-spin" /> Chargement des clubs…
        </p>
      ) : (
        <>
          <ClubSelect label="Domicile" value={home} onChange={onHome} clubs={clubs} />
          <ClubSelect label="Extérieur" value={away} onChange={onAway} clubs={clubs} />
        </>
      )}

      {error && <p className="text-sm text-red-400">{error}</p>}

      <button
        onClick={onLaunch}
        disabled={launching || clubs.length === 0}
        className="h-12 rounded-xl bg-accent text-white font-semibold disabled:opacity-40 flex items-center justify-center gap-2"
      >
        {launching ? (
          <>
            <LoaderCircle size={18} className="animate-spin" /> Préparation du match…{" "}
            {progress != null && `${progress} %`}
          </>
        ) : (
          "Lancer le match"
        )}
      </button>
    </div>
  );
}

function ClubSelect({ label, value, onChange, clubs }) {
  return (
    <label className="flex flex-col gap-1 text-sm text-gray-300">
      {label}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-10 rounded-lg bg-surface border border-line px-2 text-white"
      >
        {clubs.map((c) => (
          <option key={c.name} value={c.name}>
            {c.name}
          </option>
        ))}
      </select>
    </label>
  );
}
