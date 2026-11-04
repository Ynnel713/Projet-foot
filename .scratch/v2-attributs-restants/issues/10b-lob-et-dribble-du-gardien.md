# 10b: Lob et dribble du gardien

**Découpé du ticket 10 le 04/11/2026** (audit de granularité). Détail : `10-types-de-finition.md`, point 4.

**What to build:** deux finitions de plus, ouvertes quand le gardien sort (Rushing Out, ticket 03b) : le **lob** (par-dessus le gardien avancé) et le **dribble du gardien**, résolu par Dribbling contre One on Ones dans le duel un contre un du ticket 07a (pas de second duel en double). Gestes « Likes To Lob Keeper » et « Likes To Round Keeper » en penchants.

**Attributs :** Dribbling, One on Ones (gardien) ; Decisions, Flair.

**Blocked by:** 10a, 03b, 07a.

**Bloque :** aucun.

**Status:** à faire (constantes à proposer avant le code)

## Acceptance criteria

- [ ] Constantes produit validées par le propriétaire avant le code
- [ ] Test de cohérence (scènes fixes) : la part de lobs est nettement plus forte gardien avancé que gardien sur sa ligne
- [ ] Repris du ticket 03 (critère Rushing Out, troisième volet) : à situation égale, plus de buts lobés face à un gardien à Rushing Out élevé
- [ ] Le dribble du gardien passe par le duel du 07a (test)
- [ ] Lobs et dribbles du gardien apparaissent au moins une fois sur 50 matchs, sans dominer
- [ ] Tracés et rejoués par le rendu, sans changer l'issue
- [ ] Déterminisme à graine fixée ; suite V2 verte ; V1 inchangée
