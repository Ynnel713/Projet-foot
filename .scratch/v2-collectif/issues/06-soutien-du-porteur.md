# 06: Soutien du porteur et lignes de passe

**What to build:** Les coéquipiers du porteur se placent pour **créer des solutions** : triangles, lignes de passe ouvertes, distances de soutien cohérentes, occupation des couloirs, joueurs entre les lignes. Une équipe ne monte pas toute au-dessus du ballon : il reste un **équilibre derrière le ballon**. Fin des joueurs qui se superposent ou qui rejoignent tous un point prédéfini.

**Attributs :** Off the Ball (qualité du démarquage), Teamwork (équilibre), Vision du porteur (exploitation).

**Blocked by:** 04.

**Status:** ready-for-agent (constantes à proposer avant le code)

**Point de vigilance :** Off the Ball (ticket cerveau 03) choisit déjà un espace libre : l'intégrer au placement collectif. Les appels au trot, sauf vers l'avant, ont été validés le 26/10 mais sont sauvegardés dans `.scratch/v2-collectif/wip-socle-02-intensite.patch`.

- [ ] Nombre moyen de solutions de passe ouvertes pour le porteur dans une fourchette crédible (indicateur du ticket 01, valeur à sourcer)
- [ ] Aucun regroupement : distance minimale entre coéquipiers respectée hors duel
- [ ] Toujours au moins un joueur en sécurité derrière le ballon en possession installée
- [ ] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [ ] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [ ] Suite V2 verte ; V1 inchangée
