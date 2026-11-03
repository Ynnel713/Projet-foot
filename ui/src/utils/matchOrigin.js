// Onglet d'où vient un match, déduit des paramètres de son URL `/pitch` (refonte UI, lots 2 et 4) :
// poule ou phase de ligue, tour d'élimination, journée de championnat. "" si aucun ne correspond.
export function matchOriginTab(params) {
  if (params.has("group")) return "groups";
  if (params.has("round_number")) return "bracket";
  if (params.has("journee")) return "simulate";
  return "";
}
