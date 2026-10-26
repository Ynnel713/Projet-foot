# 11: Transition défense-attaque

**What to build:** Après une récupération : première passe pour sortir de la zone de pression, appels immédiats dans la profondeur, choix entre contre-attaque rapide et conservation du ballon selon l'espace et le nombre d'adversaires derrière le ballon.

**Attributs :** Vision, Decisions, Off the Ball, Anticipation.

**Blocked by:** 03, 06.

**Status:** ready-for-agent (constantes à proposer avant le code)

- [ ] Part des contre-attaques après récupération dans une fourchette réelle (à sourcer)
- [ ] Choix entre contre-attaque et conservation mesurablement lié à l'espace disponible
- [ ] Effet des attributs probabiliste, jamais binaire ; courbes partagées de `attributes` ; rayon de chaque attribut conforme à `docs/CARTE_ATTRIBUTS_V2.md`, sans double comptage (ticket 18)
- [ ] Constantes produit et critères chiffrés (données réelles sourcées, ou « non trouvé ») validés par le propriétaire avant le code
- [ ] Les chiffres réels sont des indicateurs de calibration, pas des objectifs : pas de réglage générique pour les atteindre avant la calibration générale (ticket 22)
- [ ] Suite V2 verte ; V1 inchangée
