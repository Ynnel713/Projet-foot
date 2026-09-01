const STAR_COUNT = 8;

// Étoiles (1 à 8 pleines) par percentile de force au sein du vivier fourni --
// auto-calibré sur la distribution réelle plutôt que des seuils de note
// fixes, donc les catégories restent bien réparties quel que soit le vivier
// (clubs seuls, sélections seules, ou les deux mélangés). Même logique que
// `app._star_rating` côté Streamlit (sextiles, ici en octiles).
export function starRating(value, allValues, starCount = STAR_COUNT) {
  if (value == null || allValues.length === 0) return "";
  const sorted = [...allValues].sort((a, b) => a - b);
  let count = 0;
  for (const v of sorted) {
    if (v <= value) count++;
  }
  const percentile = count / sorted.length;
  const filled = Math.min(starCount, Math.max(1, Math.ceil(percentile * starCount)));
  return "★".repeat(filled) + "☆".repeat(starCount - filled);
}
