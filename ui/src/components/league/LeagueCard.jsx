
export default function LeagueCard({ name, nbClubs, subtitle, cta, countryCode, isCustom = false, onLaunch }) {
  return (
    <button
      type="button"
      onClick={onLaunch}
      className={`relative rounded-xl p-4 flex flex-col items-start gap-1.5 text-left bg-surface hover:bg-surface-2 transition-colors ${
        isCustom ? "border-2 border-dashed border-accent/40" : "border border-line"
      }`}
    >
      {!isCustom && countryCode && (
        <img
          src={`https://flagcdn.com/w40/${countryCode.split("-")[0]}.png`}
          alt=""
          className="h-6 w-9 rounded object-cover"
        />
      )}
      <h3 className="font-semibold text-sm leading-tight">{name}</h3>
      <p className="text-data text-gray-400">{subtitle ?? (nbClubs != null ? `${nbClubs} clubs` : "Format libre")}</p>
      <span className="mt-auto pt-2 text-data font-medium text-link">
        {cta ?? (isCustom ? "Créer →" : "Lancer la saison →")}
      </span>
    </button>
  );
}
