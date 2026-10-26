# 09: Compensations défensives en cascade

**What to build:** Quand un joueur quitte sa zone (latéral qui monte, milieu attiré), l'équipe identifie **qui peut compenser** : selon une hiérarchie (le milieu défensif coulisse, le défenseur central se décale, le latéral opposé resserre), le **temps qu'il lui faut pour arriver**, le danger réel et les profils. Compensations en cascade si le premier est lui-même attiré ailleurs. Pas de compensation systématique : un porteur bien protégé, ou une équipe qui choisit de prendre des risques, compense moins. Les erreurs de coordination (mauvaise décision, manque de concentration ou d'anticipation) créent des retards, de façon probabiliste. Scénario de référence : le latéral droit monte, le ballon est perdu, l'adversaire lance son ailier gauche.

**Attributs :** Positioning, Anticipation, Teamwork, Decisions, Concentration ; Pace + Acceleration pour le temps d'arrivée.

**Blocked by:** 07.

**Status:** ready-for-agent (constantes à proposer avant le code)

- [ ] Test de compensation : pertes de balle après une montée de latéral, avec et sans couverture du milieu ; occasions de contre mesurablement moins nombreuses avec compensation
- [ ] Une compensation n'est choisie que si le joueur peut arriver à temps (temps de déplacement calculé)
- [ ] Les profils meilleurs en Positioning, Anticipation et Teamwork compensent mesurablement mieux
- [ ] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [ ] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [ ] Suite V2 verte ; V1 inchangée
