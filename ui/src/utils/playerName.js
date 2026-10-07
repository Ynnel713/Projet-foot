// Format court d'un buteur affiché sous un match ("L.Yamal", "E.Haaland") --
// initiale du prénom + "." + nom de famille, comme sur un vrai bandeau de
// match TV. Utilisé uniquement pour les buteurs de match (MatchRow,
// ScorersLine) -- les classements buteurs/passeurs gardent le nom complet,
// plus lisible dans une liste dédiée.
export function shortScorerName(fullName) {
  if (!fullName) return fullName;
  const parts = fullName.trim().split(" ").filter(Boolean);
  if (parts.length < 2) return fullName;
  const [first, ...rest] = parts;
  return `${first[0]}.${rest.join(" ")}`;
}
