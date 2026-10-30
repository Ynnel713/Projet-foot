# 09: Compensations défensives en cascade

**What to build:** Quand un joueur quitte sa zone (latéral qui monte, milieu attiré), l'équipe identifie **qui peut compenser** : selon une hiérarchie (le milieu défensif coulisse, le défenseur central se décale, le latéral opposé resserre), le **temps qu'il lui faut pour arriver**, le danger réel et les profils. Compensations en cascade si le premier est lui-même attiré ailleurs. Pas de compensation systématique : un porteur bien protégé, ou une équipe qui choisit de prendre des risques, compense moins. Les erreurs de coordination (mauvaise décision, manque de concentration ou d'anticipation) créent des retards, de façon probabiliste. Scénario de référence : le latéral droit monte, le ballon est perdu, l'adversaire lance son ailier gauche.

**Attributs :** Positioning, Anticipation, Teamwork, Decisions, Concentration ; Pace + Acceleration pour le temps d'arrivée.

**Blocked by:** 07, 25 (socle cinématique et contact).

**Status:** ready-for-agent (constantes à proposer avant le code)

- [ ] Test de compensation : pertes de balle après une montée de latéral, avec et sans couverture du milieu ; occasions de contre mesurablement moins nombreuses avec compensation
- [ ] Une compensation n'est choisie que si le joueur peut arriver à temps (temps de déplacement calculé)
- [ ] Les profils meilleurs en Positioning, Anticipation et Teamwork compensent mesurablement mieux
- [ ] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [ ] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [ ] Suite V2 verte ; V1 inchangée

**Reporté du ticket 07 (réserve A2 de l'expert, rattachée ici par le propriétaire le 30/10/2026)**

- Le problème : quand une passe est en l'air (36 % du temps de jeu, mesuré sur 4 matchs), `DefensiveRoles.update` ne donne aucun rôle (`v2engine/defense.py`). Les défenseurs reviennent alors à l'ancienne règle, « ballon libre à moins de 15 m, sinon bloc ».
- La conséquence : le marqueur lâche son attaquant au moment où la passe part vers lui. C'est probablement pour cela qu'un marqueur à Marking 99 reste à 3,66 m de son attaquant, en médiane, pour 1 m visé.
- La piste de l'expert : tant que `ball.receiver` est renseigné, attribuer les rôles comme si le receveur était déjà le porteur. Le presseur vise le point de réception (`meeting_point`) et les marqueurs restent en place. Les lecteurs de passe gardent leur priorité.
- [ ] Un rôle défensif est attribué pendant plus de 90 % du temps de possession adverse, passes en vol comprises
- [ ] La distance médiane entre le marqueur et son attaquant baisse à Marking 99 (`diag_marking.py`, à recréer hors dépôt)
