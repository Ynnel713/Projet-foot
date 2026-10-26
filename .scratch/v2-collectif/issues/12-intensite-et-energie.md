# 12: Intensité de course et réserve d'énergie

**What to build:** Reprise du ticket v2-socle/02 sur la nouvelle structure : l'intensité de chaque déplacement découle du **rôle** attribué (presseur, couverture, repli, soutien, appel) et de l'attribut mental qui gouverne ce rôle ; Pace reste la seule vitesse maximale. La fatigue dépend de l'effort (réserve d'énergie) : un Work Rate haut avec une Stamina basse décroche plus tôt. La fatigue réduit aussi la **capacité à répéter les efforts**, pas seulement la vitesse.

**Attributs :** Work Rate, Off the Ball, Teamwork, Stamina, Pace, Acceleration.

**Blocked by:** 07, 08, 10.

**Status:** ready-for-agent (constantes à proposer avant le code)

**Point de vigilance :** code sauvegardé dans `.scratch/v2-collectif/wip-socle-02-intensite.patch` du 26/10 : intensités par attribut, fatigue liée à l'effort, approche au trot à 10 m, receveur à 0,7. Mesure sur 20 matchs : 10,5 km et 23 % de baisse en fin de match (bons) ; sprints à 7,2 % et Off the Ball de sens inverse (à corriger).

- [ ] Critères du ticket socle 02 repris tels que validés : 9-14 km par joueur ; 2-3 % de la distance au-dessus de 25 km/h ; ordre des postes de Bradley 2009 ; Work Rate 99 contre 11 : +25 à 45 % de course intense ; Off the Ball 99 contre 11 : 1,5 à 2 fois plus d'appels ; baisse d'environ 20 % de la course intense en fin de match
- [ ] Test de fatigue : des efforts répétés dégradent progressivement la capacité à presser, revenir et tenir la structure
- [ ] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [ ] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [ ] Suite V2 verte ; V1 inchangée
