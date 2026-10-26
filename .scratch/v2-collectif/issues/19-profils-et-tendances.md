# 19: Profils et tendances individuelles

**What to build:** Deux joueurs au même poste avec le même rôle ne jouent pas de la même manière : les attributs modifient aussi les actions envisagées, les espaces repérés et les solutions préférées. Un joueur à grande Vision reconnaît plus d'occasions. Intègre les tendances de la base (Preferred Moves, 55 types) comme des penchants, jamais comme des ordres. Reprend le ticket cerveau 05 (Flair : options risquées) et la partie « avec ballon » du ticket cerveau 06 (Teamwork : donner au partenaire mieux placé).

**Attributs :** Flair, Teamwork, Vision, Decisions, Preferred Moves.

**Blocked by:** 13, 18.

**Status:** ready-for-agent (constantes à proposer avant le code)

**Point de vigilance :** les tickets v2-cerveau-joueurs/05 et /06 sont absorbés ici (et dans le ticket 04 pour Teamwork sans ballon).

- [ ] Critères des tickets cerveau 05 et 06 (partie ballon) repris
- [ ] Test de diversité : plusieurs matchs dans les mêmes conditions donnent des comportements ni identiques ni excessivement aléatoires
- [ ] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [ ] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [ ] Suite V2 verte ; V1 inchangée
