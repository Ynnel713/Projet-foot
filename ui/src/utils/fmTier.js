// Vert/orange/rouge pour une note ou un attribut FM26 (échelle 0-99) -- mêmes
// seuils que app._fm_tier côté Streamlit (retour terrain du 27/09/2026 : vert
// strictement au-dessus de 70). Couleurs : tokens de ui/src/index.css.
// Aplat sous texte blanc (badge de note) -- mêmes valeurs qu'avant la refonte.
const TIER_FILL_COLORS = {
  good: "var(--color-tier-good-fill)",
  avg: "var(--color-tier-avg-fill)",
  poor: "var(--color-tier-poor-fill)",
};
// Texte sur fond sombre (valeurs d'attributs, libellés du radar) : variante
// claire, lisible ; le vert et le rouge sont ceux des résultats (un seul vert).
const TIER_TEXT_COLORS = { good: "var(--color-win)", avg: "var(--color-tier-avg)", poor: "var(--color-loss)" };

export function fmTier(value) {
  if (value > 70) return "good";
  if (value >= 50) return "avg";
  return "poor";
}

export function fmTierColor(value) {
  return TIER_FILL_COLORS[fmTier(value)];
}

export function fmTierTextColor(value) {
  return TIER_TEXT_COLORS[fmTier(value)];
}
