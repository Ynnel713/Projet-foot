# 01: Banc de mesure et tests tactiques

**What to build:** Versionner dans `scripts/` les mesures aujourd'hui éparpillées dans le scratchpad (rythme, passes, tacles, courses) et y ajouter des **indicateurs tactiques** : pertes de balle en transition, temps de réaction au repli, distances entre lignes, nombre de solutions de passe disponibles pour le porteur, qualité des couvertures, fréquence des appels coordonnés. Poser le cadre des **tests tactiques ciblés** (compensation, pressing, circulation, profils, fatigue, diversité, cohérence) : scénarios reproductibles, avec et sans le mécanisme testé. Mesure sur au moins 20 matchs par défaut, 50 pour la calibration.

**Attributs :** Aucun.

**Blocked by:** None (premier ticket du chantier).

**Status:** livré (26/10/2026), validé QC (après un REFUSÉ pour des tests manquants, corrigés)

**Point de vigilance :** les scripts `all20.py`, `course20.py` et `diag_*.py` du scratchpad sont la base : les reprendre, pas les réécrire.

- [x] Une commande unique donne tous les indicateurs (classiques et tactiques) sur N matchs, graines fixes
- [x] Les indicateurs tactiques sont définis par écrit (formule, unité) avant le code
- [x] Un scénario tactique se rejoue à l'identique (même graine, mêmes chiffres)
- [x] Reprend le critère resté ouvert du ticket v2-cerveau-joueurs/01 : écart mesuré entre profils sur matchs simulés
- [x] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [ ] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code — définitions validées le 26/10 ; seuils marqués « proposé » et valeurs réelles à relire dans le texte intégral restent à confirmer
- [x] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [x] Suite V2 verte ; V1 inchangée

## Réalisé (26/10/2026)

- `scripts/measure_v2.py` (commande), `scripts/v2_indicators.py` (indicateurs), `tests/test_v2_indicators.py` (28 tests), spécification et mesure de référence dans `docs/INDICATEURS_V2.md`.
- Moteur : un seul ajout, le paramètre `observer` de `simulate_match`, en lecture seule (trace identique avec et sans, testé).
- Seuils marqués « proposé » dans `docs/INDICATEURS_V2.md` (portée de 40 m, presseur à 3 m, demi-largeur de l'ellipse 4 m, redondance à 5 m, repli) : à confirmer par le propriétaire.
- Critère du ticket cerveau 01 (écart entre profils en match) : mesurable avec `--profil` ; Work Rate sans effet aujourd'hui (pas encore branché), Off the Ball avec effet.
