// Nom de fichier attendu pour le logo d'un club (public/logos/clubs/<slug>.png)
// -- accents retirés, tout ce qui n'est pas alphanumérique devient un tiret.
// Même algorithme que le script qui a généré NOMS_DE_FICHIERS_ATTENDUS.txt
// (déposé dans le dossier de logos à renommer) : ne pas laisser diverger.
export function clubSlug(clubName) {
  return clubName
    .normalize("NFKD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function clubLogoUrl(clubName) {
  return `/logos/clubs/${clubSlug(clubName)}.png`;
}
