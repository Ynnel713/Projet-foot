# 20: Les joueurs connaissent leurs limites

**What to build:** Un défenseur techniquement limité reconnaît qu'une passe risquée est inadaptée à la pression qu'il subit ; un joueur lent anticipe et évite de défendre dans de grands espaces ; un attaquant à faible Teamwork respecte moins les compensations ; une grande Vision avec de faibles Décisions voit la passe brillante et peut choisir l'option dangereuse ; un excellent dribbleur attire deux adversaires mais doit savoir lâcher le ballon. Tendances crédibles, jamais de seuils du type « en dessous de 40, jamais ».

**Attributs :** Croisements : Passing × pression, Pace × Positioning, Vision × Decisions, Dribbling × Decisions.

**Blocked by:** 18, 19.

**Status:** à faire (constantes à proposer avant le code)

- [ ] Pour chaque cas, un test à situation égale montre la tendance, sans interdiction absolue
- [ ] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [ ] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [ ] Suite V2 verte ; V1 inchangée
