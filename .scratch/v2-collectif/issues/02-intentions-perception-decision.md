# 02: Perception, interprétation, décision, exécution

**What to build:** Structurer le cerveau de chaque joueur en quatre temps distincts : **perception** (partenaires, adversaires, espaces et trajectoires qu'il détecte : Vision, Anticipation, Concentration), **interprétation** (menace ou opportunité identifiée), **décision** (action choisie : Decisions, tendances), **exécution** (qualité du geste : attributs techniques et physiques), puis **conséquence** (les autres réagissent). Chaque joueur porte une **intention** explicite (rôle, cible, action), enregistrée dans la trace du match pour la relecture : pourquoi une occasion a été créée, pourquoi une défense s'est désorganisée. Exemple à respecter : un défenseur à 90 en Anticipation détecte la passe en profondeur, mais ne l'intercepte que s'il est assez proche, bien orienté et a le temps d'agir.

**Attributs :** Vision, Anticipation, Concentration (perception) ; Decisions (décision) ; techniques et physiques (exécution).

**Blocked by:** 01.

**Status:** ready-for-agent (constantes à proposer avant le code)

**Point de vigilance :** Vision, Decisions et Passing sont déjà distincts (tickets cerveau 01, 02 et socle 04) : étendre ce principe sans casser l'existant.

- [ ] Chaque joueur a une intention lisible à chaque instant dans la trace (rôle, cible, action)
- [ ] Voir, choisir et réussir sont trois tirages distincts, testés séparément
- [ ] Le rendu V2 peut afficher l'intention d'un joueur (relecture)
- [ ] Décision d'architecture écrite (ADR dans `docs/adr/`) avant le code
- [ ] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [ ] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [ ] Suite V2 verte ; V1 inchangée
