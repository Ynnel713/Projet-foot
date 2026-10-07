// Vert/orange/rouge pour une note ou un attribut FM26 (échelle 0-99) -- mêmes
// seuils et couleurs que app._fm_tier côté Streamlit (retour terrain du
// 27/09/2026 : vert strictement au-dessus de 70).
const TIER_COLORS = { good: "#1e8e3e", avg: "#c99a12", poor: "#c0392b" };
// Variante plus claire, réservée aux libellés du radar (mêmes valeurs que
// app._radar_svg côté Streamlit -- plus lisible sur fond sombre qu'un aplat).
const RADAR_TIER_COLORS = { good: "#3ddc70", avg: "#e0b13a", poor: "#e0645a" };

export function fmTier(value) {
  if (value > 70) return "good";
  if (value >= 50) return "avg";
  return "poor";
}

export function fmTierColor(value) {
  return TIER_COLORS[fmTier(value)];
}

export function fmRadarTierColor(value) {
  return RADAR_TIER_COLORS[fmTier(value)];
}
