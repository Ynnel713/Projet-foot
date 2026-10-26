# 01: Banc de mesure et tests tactiques

**What to build:** Versionner dans `scripts/` les mesures aujourd'hui éparpillées dans le scratchpad (rythme, passes, tacles, courses) et y ajouter des **indicateurs tactiques** : pertes de balle en transition, temps de réaction au repli, distances entre lignes, nombre de solutions de passe disponibles pour le porteur, qualité des couvertures, fréquence des appels coordonnés. Poser le cadre des **tests tactiques ciblés** (compensation, pressing, circulation, profils, fatigue, diversité, cohérence) : scénarios reproductibles, avec et sans le mécanisme testé. Mesure sur au moins 20 matchs par défaut, 50 pour la calibration.

**Attributs :** Aucun.

**Blocked by:** None (premier ticket du chantier).

**Status:** ready-for-agent (constantes à proposer avant le code)

**Point de vigilance :** les scripts `all20.py`, `course20.py` et `diag_*.py` du scratchpad sont la base : les reprendre, pas les réécrire.

- [ ] Une commande unique donne tous les indicateurs (classiques et tactiques) sur N matchs, graines fixes
- [ ] Les indicateurs tactiques sont définis par écrit (formule, unité) avant le code
- [ ] Un scénario tactique se rejoue à l'identique (même graine, mêmes chiffres)
- [ ] Reprend le critère resté ouvert du ticket v2-cerveau-joueurs/01 : écart mesuré entre profils sur matchs simulés
- [ ] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [ ] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [ ] Suite V2 verte ; V1 inchangée
