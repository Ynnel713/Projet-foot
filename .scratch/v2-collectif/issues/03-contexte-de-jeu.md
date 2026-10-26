# 03: Reconnaître la situation de jeu

**What to build:** Chaque équipe identifie à chaque instant le **type de problème tactique** auquel elle fait face : possession installée, défense placée, transition offensive, transition défensive, dernier tiers et surface (les coups de pied arrêtés viennent en phase 8). Pas de séquence scriptée par situation : la situation oriente les rôles et les priorités, puis les joueurs choisissent leur réponse.

**Attributs :** Aucun directement (lecture collective) ; Concentration retarde la reconnaissance d'un changement de phase.

**Blocked by:** 02.

**Status:** ready-for-agent (constantes à proposer avant le code)

- [ ] La situation de chaque équipe est calculée et enregistrée dans la trace
- [ ] Sur scénario, une perte de balle fait basculer en transition défensive en moins d'un temps de réaction réaliste (chiffre à sourcer)
- [ ] Les seuils de bascule entre situations sont proposés et validés avant le code
- [ ] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [ ] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [ ] Suite V2 verte ; V1 inchangée
