# 05: Hauteur et profondeur du bloc

**What to build:** La ligne défensive ajuste sa hauteur selon la position du ballon, la **pression exercée sur le passeur** (passeur pressé : la ligne peut monter ; passeur libre : elle recule), la menace des appels adverses et les capacités des défenseurs (un défenseur lent a intérêt à défendre plus bas). L'espace laissé dans le dos est un choix collectif, pas un effet de la vitesse brute.

**Attributs :** Positioning ; Pace + Acceleration + Positioning (repli préventif) ; Anticipation (lecture de la passe en profondeur).

**Blocked by:** 04.

**Status:** ready-for-agent (constantes à proposer avant le code)

- [ ] Ligne défensive mesurablement plus basse avec des défenseurs lents, à situation égale
- [ ] Passeur pressé contre passeur libre : écart de hauteur de ligne mesurable
- [ ] Passes en profondeur réussies dans une fourchette réelle (à sourcer)
- [ ] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [ ] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [ ] Suite V2 verte ; V1 inchangée
