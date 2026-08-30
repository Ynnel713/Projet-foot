import { motion } from "framer-motion";

export default function LeagueCard({ name, nbClubs, subtitle, cta, countryCode, isCustom = false, onLaunch }) {
  return (
    <motion.button
      type="button"
      whileHover={{ scale: 1.03 }}
      whileTap={{ scale: 0.98 }}
      transition={{ duration: 0.2 }}
      onClick={onLaunch}
      className={`relative rounded-2xl p-4 flex flex-col items-start gap-1.5 text-left bg-surface ${
        isCustom ? "border-2 border-dashed border-gold/60" : "border border-white/5"
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
      <p className="text-xs text-gray-400">{subtitle ?? (nbClubs != null ? `${nbClubs} clubs` : "Format libre")}</p>
      <span className="mt-auto pt-2 text-xs font-medium text-accent">
        {cta ?? (isCustom ? "Créer →" : "Lancer la saison →")}
      </span>
    </motion.button>
  );
}
