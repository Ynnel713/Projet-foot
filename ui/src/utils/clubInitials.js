// Même logique que app._club_initials côté Streamlit (badge de club sans
// logo réel) : 2 lettres du seul mot si le nom est monomot, sinon 1re lettre
// des deux premiers mots -- les mots purement numériques (ex. "1899
// Hoffenheim") sont ignorés pour ne pas produire des initiales comme "18".
export function clubInitials(clubName) {
  const words = clubName.split(/\s+/).filter((w) => w && !/^\d+$/.test(w));
  const source = words.length > 0 ? words : clubName.split(/\s+/).filter(Boolean);
  if (source.length === 0) return "?";
  if (source.length === 1) return source[0].slice(0, 2).toUpperCase();
  return (source[0][0] + source[1][0]).toUpperCase();
}
