// Barre d'action commune (refonte UI, lot 3) : le geste « simuler » est toujours au même endroit -- en bas de l'écran, au-dessus de la
// navigation -- avec les mêmes dimensions (44 px), dans le championnat, les poules / la phase de ligue et la phase finale.
// `primary` : { label, onClick, disabled, loading } (accent) ; `secondary` : même forme, discret (ex. « Simuler tout »).
export default function ActionBar({ primary, secondary }) {
  return (
    <div className="shrink-0 border-t border-line bg-surface px-3 py-1.5 flex items-center justify-center gap-2">
      {secondary && (
        <button
          onClick={secondary.onClick}
          disabled={secondary.disabled}
          className="h-11 px-4 rounded-lg border border-line bg-surface-2 text-sm font-medium text-gray-200 hover:bg-surface-3 disabled:opacity-40"
        >
          {secondary.label}
        </button>
      )}
      <button
        onClick={primary.onClick}
        disabled={primary.disabled || primary.loading}
        className="h-11 flex-1 max-w-md rounded-lg bg-accent text-white font-semibold hover:brightness-110 disabled:opacity-40"
      >
        {primary.loading ? "…" : primary.label}
      </button>
    </div>
  );
}
